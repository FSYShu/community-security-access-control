import json
import os
import sys
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask
from dotenv import dotenv_values

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import db
from app.daily_report_scheduler import DailyReportScheduler
from app.models import AlarmEvent, DailyReport, Gate, PassRecord
from app.report.ai_config import (
    save_siliconflow_api_key,
    validate_siliconflow_api_key,
)
from app.report.service import (
    ReportAlreadyExists,
    ReportGenerationInProgress,
    _report_lock,
    delete_daily_report,
    generate_daily_report,
)
from core.security_report_workflow import SecurityReportWorkflow


_CST = timezone(timedelta(hours=8))


@pytest.fixture
def report_app():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        AI_REPORT_ENABLED=False,
        DAILY_REPORT_GENERATE_TIME='00:10',
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def seed_security_data(app):
    with app.app_context():
        gate = Gate(gate_name='测试门禁1', gate_level='community_gate')
        db.session.add(gate)
        db.session.flush()
        db.session.add_all([
            PassRecord(
                gate_id=gate.id,
                pass_result='pass',
                pass_time='2026-07-13T01:00:00',
            ),
            PassRecord(
                gate_id=gate.id,
                pass_result='reject',
                reject_reason='陌生人',
                pass_time='2026-07-13T02:00:00',
            ),
            AlarmEvent(
                alarm_type='open_flame',
                alarm_level='critical',
                source_id=gate.id,
                source_type='gate',
                alarm_description='疑似出现明火',
                handle_status='pending',
                alarm_time='2026-07-13T03:00:00',
            ),
        ])
        db.session.commit()


def test_report_workflow_generates_summary_risk_and_recommendations(report_app):
    seed_security_data(report_app)

    with report_app.app_context():
        report = generate_daily_report('2026-07-13')
        pass_stats = json.loads(report.pass_stats)
        alarm_stats = json.loads(report.alarm_stats)
        recommendations = json.loads(report.recommendations)

        assert pass_stats['total'] == 2
        assert pass_stats['reject_count'] == 1
        assert alarm_stats['total'] == 1
        assert alarm_stats['pending_count'] == 1
        assert report.risk_level == 'high'
        assert report.workflow_source == 'local_rules'
        assert '通行2次' in report.ai_summary
        assert any('明火烟雾' in item for item in recommendations)


def test_existing_report_requires_explicit_regeneration(report_app):
    seed_security_data(report_app)

    with report_app.app_context():
        first = generate_daily_report('2026-07-13')
        first_id = first.id
        with pytest.raises(ReportAlreadyExists):
            generate_daily_report('2026-07-13')

        regenerated = generate_daily_report('2026-07-13', replace=True)
        assert regenerated.id == first_id
        assert DailyReport.query.count() == 1


def test_report_generation_does_not_queue_behind_another_generation(report_app):
    with report_app.app_context():
        assert _report_lock.acquire(blocking=False)
        try:
            with pytest.raises(ReportGenerationInProgress):
                generate_daily_report('2026-07-13')
        finally:
            _report_lock.release()


def test_report_can_be_deleted(report_app):
    seed_security_data(report_app)

    with report_app.app_context():
        report = generate_daily_report('2026-07-13')
        report_id = report.id

        assert delete_daily_report(report_id) == '2026-07-13'
        assert db.session.get(DailyReport, report_id) is None
        assert delete_daily_report(report_id) is None


def test_scheduler_generates_previous_day_only_after_configured_time(report_app):
    seed_security_data(report_app)
    scheduler = DailyReportScheduler(report_app)

    assert scheduler.run_if_due(
        datetime(2026, 7, 14, 0, 9, tzinfo=_CST)
    ) is None

    report = scheduler.run_if_due(
        datetime(2026, 7, 14, 0, 10, tzinfo=_CST)
    )
    assert report['report_date'] == '2026-07-13'

    same_report = scheduler.run_if_due(
        datetime(2026, 7, 14, 12, 0, tzinfo=_CST)
    )
    assert same_report['id'] == report['id']


def test_siliconflow_response_is_used_for_recommendations(monkeypatch):
    response_body = json.dumps({
        'choices': [{
            'message': {
                'content': json.dumps({
                    'recommendations': ['检查待处理告警'],
                }, ensure_ascii=False)
            }
        }]
    }, ensure_ascii=False).encode('utf-8')
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return response_body

    def fake_urlopen(req, timeout):
        captured['url'] = req.full_url
        captured['authorization'] = req.get_header('Authorization')
        captured['payload'] = json.loads(req.data.decode('utf-8'))
        captured['timeout'] = timeout
        return FakeResponse()

    monkeypatch.setattr(
        'core.security_report_workflow.urlrequest.urlopen', fake_urlopen
    )
    workflow = SecurityReportWorkflow(
        ai_service_url='https://api.siliconflow.cn/v1',
        ai_provider='siliconflow',
        ai_model='Qwen/Qwen2.5-7B-Instruct',
        ai_api_key='test-api-key',
    )

    result = workflow.run('2026-07-13', [], [], [])

    assert result['workflow_source'] == 'siliconflow'
    assert result['ai_summary'].startswith('2026-07-13共记录通行0次')
    assert result['recommendations'] == ['检查待处理告警']
    assert captured['url'] == 'https://api.siliconflow.cn/v1/chat/completions'
    assert captured['authorization'] == 'Bearer test-api-key'
    assert captured['payload']['model'] == 'Qwen/Qwen2.5-7B-Instruct'
    assert captured['payload']['response_format'] == {'type': 'json_object'}


def test_siliconflow_without_api_key_uses_local_rules(monkeypatch):
    called = []
    monkeypatch.setattr(
        'core.security_report_workflow.urlrequest.urlopen',
        lambda req, timeout: called.append(req),
    )
    workflow = SecurityReportWorkflow(
        ai_service_url='https://api.siliconflow.cn/v1',
        ai_provider='siliconflow',
        ai_api_key='',
    )

    result = workflow.run('2026-07-13', [], [], [])

    assert result['workflow_source'] == 'local_rules'
    assert called == []


def test_siliconflow_api_key_is_persisted_and_applied(tmp_path):
    app = Flask(__name__)
    app.config.update(
        AI_REPORT_PROVIDER='local',
        AI_REPORT_ENABLED=False,
        SILICONFLOW_API_KEY='',
    )
    env_path = tmp_path / '.env'
    api_key = 'sk-' + ('a' * 40)

    save_siliconflow_api_key(app, api_key, str(env_path))

    values = dotenv_values(str(env_path))
    assert values['AI_REPORT_PROVIDER'] == 'siliconflow'
    assert values['SILICONFLOW_API_KEY'] == api_key
    assert values['AI_REPORT_ENABLED'] == 'true'
    assert app.config['AI_REPORT_PROVIDER'] == 'siliconflow'
    assert app.config['SILICONFLOW_API_KEY'] == api_key
    assert app.config['AI_REPORT_ENABLED'] is True


@pytest.mark.parametrize('api_key', ['', 'not-a-key', 'sk-short', 'sk-good\nBAD'])
def test_invalid_siliconflow_api_key_is_rejected(api_key):
    with pytest.raises(ValueError):
        validate_siliconflow_api_key(api_key)
