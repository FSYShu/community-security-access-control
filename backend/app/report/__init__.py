"""
安防监控日报模块蓝图
"""
import json
from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.report import DailyReport
from app.models.pass_record import PassRecord
from app.models.alarm import AlarmEvent
from app.models.gate import Gate
from utils.response import success_response, error_response
from utils.permissions import admin_required
from core.db_lock import with_write_lock
from core.audit_logger import log_audit

report_bp = Blueprint('report', __name__)


@report_bp.route('/list', methods=['GET'])
@jwt_required()
def get_report_list():
    """获取日报列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = DailyReport.query
    if start_date:
        query = query.filter(DailyReport.report_date >= start_date)
    if end_date:
        query = query.filter(DailyReport.report_date <= end_date)

    query = query.order_by(DailyReport.report_date.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response(data={
        'items': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page
    })


@report_bp.route('/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report_detail(report_id):
    """获取日报详情"""
    report = DailyReport.query.get(report_id)
    if not report:
        return error_response(message='日报不存在', code=404)
    return success_response(data=report.to_dict())


@report_bp.route('/generate', methods=['POST'])
@admin_required
@with_write_lock
def generate_report():
    """手动生成指定日期的日报"""
    data = request.get_json()
    report_date = data.get('report_date', '')
    if not report_date:
        return error_response(message='请指定日报日期', code=400)

    existing = DailyReport.query.filter_by(report_date=report_date).first()
    if existing:
        return error_response(message='该日期日报已存在，请使用重新生成', code=400)

    report = _build_report(report_date)
    db.session.add(report)
    db.session.commit()
    log_audit(operation_type='generate_report', operation_content=f'生成日报: {report_date}')
    return success_response(data=report.to_dict(), message='日报生成成功')


@report_bp.route('/<int:report_id>/regenerate', methods=['POST'])
@admin_required
@with_write_lock
def regenerate_report(report_id):
    """重新生成指定日期的日报"""
    report = DailyReport.query.get(report_id)
    if not report:
        return error_response(message='日报不存在', code=404)

    report_date = report.report_date
    db.session.delete(report)
    db.session.commit()

    new_report = _build_report(report_date)
    db.session.add(new_report)
    db.session.commit()
    log_audit(operation_type='regenerate_report', operation_content=f'重新生成日报: {report_date}')
    return success_response(data=new_report.to_dict(), message='日报重新生成成功')


def _build_report(report_date):
    """构建日报统计数据"""
    next_date = datetime.strptime(report_date, '%Y-%m-%d')
    from datetime import timedelta
    next_day = (next_date + timedelta(days=1)).isoformat()

    total_pass = PassRecord.query.filter(
        PassRecord.pass_time >= report_date,
        PassRecord.pass_time < next_day
    ).all()

    pass_count = len([r for r in total_pass if r.pass_result == 'pass'])
    reject_count = len([r for r in total_pass if r.pass_result == 'reject'])

    gates = Gate.query.all()
    gate_distribution = {}
    level_distribution = {}
    for g in gates:
        g_pass = len([r for r in total_pass if r.gate_id == g.id and r.pass_result == 'pass'])
        g_reject = len([r for r in total_pass if r.gate_id == g.id and r.pass_result == 'reject'])
        if g_pass + g_reject > 0:
            gate_distribution[g.gate_name] = {'pass': g_pass, 'reject': g_reject}
            level = g.gate_level
            if level not in level_distribution:
                level_distribution[level] = {'pass': 0, 'reject': 0}
            level_distribution[level]['pass'] += g_pass
            level_distribution[level]['reject'] += g_reject

    pass_stats = json.dumps({
        'total': len(total_pass),
        'pass_count': pass_count,
        'reject_count': reject_count,
        'level_distribution': level_distribution,
        'gate_distribution': gate_distribution
    }, ensure_ascii=False)

    total_alarms = AlarmEvent.query.filter(
        AlarmEvent.alarm_time >= report_date,
        AlarmEvent.alarm_time < next_day
    ).all()

    type_dist = {}
    level_dist = {}
    for a in total_alarms:
        type_dist[a.alarm_type] = type_dist.get(a.alarm_type, 0) + 1
        level_dist[a.alarm_level] = level_dist.get(a.alarm_level, 0) + 1

    alarm_stats = json.dumps({
        'total': len(total_alarms),
        'type_distribution': type_dist,
        'level_distribution': level_dist
    }, ensure_ascii=False)

    abnormal_events = json.dumps([a.to_dict() for a in total_alarms if a.alarm_level == 'critical'], ensure_ascii=False)

    return DailyReport(
        report_date=report_date,
        pass_stats=pass_stats,
        alarm_stats=alarm_stats,
        abnormal_events=abnormal_events,
        generate_status='generated',
        generated_at=datetime.utcnow().isoformat()
    )
