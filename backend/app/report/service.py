"""Database service for the security daily report workflow."""

import json
import threading
from datetime import datetime, timedelta, timezone

from flask import current_app

from app import db
from app.models.alarm import AlarmEvent
from app.models.gate import Gate
from app.models.pass_record import PassRecord
from app.models.report import DailyReport
from core.security_report_workflow import SecurityReportWorkflow


_CST = timezone(timedelta(hours=8))
_report_lock = threading.Lock()


class ReportAlreadyExists(Exception):
    pass


class ReportGenerationInProgress(Exception):
    """Another report generation or deletion is currently using the report lock."""

    pass


def validate_report_date(report_date):
    try:
        parsed = datetime.strptime(report_date, '%Y-%m-%d')
    except (TypeError, ValueError):
        raise ValueError('日报日期格式必须为 YYYY-MM-DD')
    if parsed.strftime('%Y-%m-%d') != report_date:
        raise ValueError('日报日期格式必须为 YYYY-MM-DD')
    return parsed


def utc_bounds_for_local_date(report_date):
    parsed = validate_report_date(report_date)
    local_start = parsed.replace(tzinfo=_CST)
    local_end = local_start + timedelta(days=1)
    return (
        local_start.astimezone(timezone.utc).replace(tzinfo=None).isoformat(),
        local_end.astimezone(timezone.utc).replace(tzinfo=None).isoformat(),
    )


def generate_daily_report(report_date, replace=False):
    """Generate and persist one report, preserving its id when regenerated."""
    start_time, end_time = utc_bounds_for_local_date(report_date)
    if not _report_lock.acquire(blocking=False):
        raise ReportGenerationInProgress()
    try:
        existing = DailyReport.query.filter_by(report_date=report_date).first()
        if existing is not None and not replace:
            raise ReportAlreadyExists(report_date)

        pass_records = PassRecord.query.filter(
            PassRecord.pass_time >= start_time,
            PassRecord.pass_time < end_time,
        ).all()
        alarms = AlarmEvent.query.filter(
            AlarmEvent.alarm_time >= start_time,
            AlarmEvent.alarm_time < end_time,
        ).all()
        gates = Gate.query.all()
        ai_provider = current_app.config.get('AI_REPORT_PROVIDER', 'siliconflow')
        ai_service_url = (
            current_app.config.get(
                'SILICONFLOW_BASE_URL', 'https://api.siliconflow.cn/v1'
            )
            if ai_provider == 'siliconflow'
            else current_app.config.get('AI_SERVICE_URL', '')
        )
        ai_model = (
            current_app.config.get(
                'SILICONFLOW_MODEL', 'Qwen/Qwen2.5-7B-Instruct'
            )
            if ai_provider == 'siliconflow'
            else current_app.config.get('AI_REPORT_MODEL', '')
        )
        ai_api_key = (
            current_app.config.get('SILICONFLOW_API_KEY', '')
            if ai_provider == 'siliconflow'
            else current_app.config.get('AI_SERVICE_API_KEY', '')
        )
        workflow = SecurityReportWorkflow(
            ai_service_url=ai_service_url,
            ai_enabled=current_app.config.get('AI_REPORT_ENABLED', True),
            ai_timeout=current_app.config.get('AI_REPORT_TIMEOUT', 60.0),
            ai_endpoint=current_app.config.get(
                'AI_REPORT_ENDPOINT', '/chat/completions'
            ),
            ai_provider=ai_provider,
            ai_model=ai_model,
            ai_api_key=ai_api_key,
        )
        result = workflow.run(report_date, pass_records, alarms, gates)

        report = existing or DailyReport(report_date=report_date)
        report.pass_stats = json.dumps(result['pass_stats'], ensure_ascii=False)
        report.alarm_stats = json.dumps(result['alarm_stats'], ensure_ascii=False)
        report.abnormal_events = json.dumps(
            result['abnormal_events'], ensure_ascii=False
        )
        report.ai_summary = result['ai_summary']
        report.risk_level = result['risk_level']
        report.risk_score = result['risk_score']
        report.recommendations = json.dumps(
            result['recommendations'], ensure_ascii=False
        )
        report.workflow_source = result['workflow_source']
        report.generate_status = 'generated'
        report.generated_at = datetime.utcnow().isoformat()
        db.session.add(report)
        db.session.commit()
        return report
    finally:
        _report_lock.release()


def delete_daily_report(report_id):
    """Delete one report and return its date, or None when it does not exist."""
    if not _report_lock.acquire(blocking=False):
        raise ReportGenerationInProgress()
    try:
        report = db.session.get(DailyReport, report_id)
        if report is None:
            return None
        report_date = report.report_date
        db.session.delete(report)
        db.session.commit()
        return report_date
    finally:
        _report_lock.release()
