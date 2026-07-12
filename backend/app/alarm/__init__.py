"""
告警中心模块蓝图
提供告警列表、告警详情、告警处置、告警导出等接口
"""
import io
from datetime import datetime

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt

from app import db
from app.models.alarm import AlarmEvent
from utils.response import success_response, error_response, paginate_response
from utils.permissions import admin_required, guard_or_admin_required
from core.db_lock import with_write_lock
from core.audit_logger import log_audit

alarm_bp = Blueprint('alarm', __name__)


@alarm_bp.route('/list', methods=['GET'])
@jwt_required()
def get_alarm_list():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    alarm_type = request.args.get('alarm_type', '')
    alarm_level = request.args.get('alarm_level', '')
    handle_status = request.args.get('handle_status', '')
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')

    query = AlarmEvent.query
    if alarm_type:
        query = query.filter_by(alarm_type=alarm_type)
    if alarm_level:
        query = query.filter_by(alarm_level=alarm_level)
    if handle_status:
        query = query.filter_by(handle_status=handle_status)
    if start_time:
        query = query.filter(AlarmEvent.alarm_time >= start_time)
    if end_time:
        query = query.filter(AlarmEvent.alarm_time <= end_time)

    pagination = query.order_by(AlarmEvent.alarm_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    items = [a.to_dict() for a in pagination.items]
    return paginate_response(items, pagination.total, page, per_page)


@alarm_bp.route('/<int:alarm_id>', methods=['GET'])
@jwt_required()
def get_alarm_detail(alarm_id):
    alarm = AlarmEvent.query.get(alarm_id)
    if not alarm:
        return error_response(message='告警事件不存在', code=404)
    return success_response(data=alarm.to_dict())


@alarm_bp.route('/<int:alarm_id>/handle', methods=['PUT'])
@guard_or_admin_required
@with_write_lock
def handle_alarm(alarm_id):
    alarm = AlarmEvent.query.get(alarm_id)
    if not alarm:
        return error_response(message='告警事件不存在', code=404)

    if alarm.handle_status == 'handled':
        return error_response(message='该告警已处置', code=409)

    data = request.get_json()
    handle_remark = data.get('handle_remark', '').strip()
    if not handle_remark:
        return error_response(message='处置备注不能为空', code=400)

    current_user = get_jwt()
    user_id = int(current_user.get('sub', 0))

    alarm.handle_status = 'handled'
    alarm.handler_id = user_id
    alarm.handle_time = datetime.utcnow().isoformat()
    alarm.handle_remark = handle_remark
    db.session.commit()
    log_audit(operation_type='handle_alarm', operation_content='处置告警ID: {}'.format(alarm_id))
    return success_response(data=alarm.to_dict(), message='处置成功')


@alarm_bp.route('/export', methods=['GET'])
@guard_or_admin_required
def export_alarm_log():
    alarm_type = request.args.get('alarm_type', '')
    handle_status = request.args.get('handle_status', '')
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')

    query = AlarmEvent.query
    if alarm_type:
        query = query.filter_by(alarm_type=alarm_type)
    if handle_status:
        query = query.filter_by(handle_status=handle_status)
    if start_time:
        query = query.filter(AlarmEvent.alarm_time >= start_time)
    if end_time:
        query = query.filter(AlarmEvent.alarm_time <= end_time)

    alarms = query.order_by(AlarmEvent.alarm_time.desc()).limit(5000).all()

    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = '告警日志'
        headers = ['告警ID', '告警类型', '告警级别', '来源类型', '来源ID', '告警描述', '告警时间', '处置状态', '处置人ID', '处置时间', '处置备注']
        ws.append(headers)
        for a in alarms:
            ws.append([
                a.id, a.alarm_type, a.alarm_level, a.source_type, a.source_id,
                a.alarm_description, a.alarm_time, a.handle_status,
                a.handler_id, a.handle_time, a.handle_remark
            ])
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        filename = 'alarm_log_{}.xlsx'.format(datetime.utcnow().strftime('%Y%m%d_%H%M%S'))
        return send_file(output, as_attachment=True, attachment_filename=filename,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        return error_response(message='导出失败: {}'.format(str(e)), code=500)


@alarm_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_alarm_stats():
    total = AlarmEvent.query.count()
    pending = AlarmEvent.query.filter_by(handle_status='pending').count()
    handled = AlarmEvent.query.filter_by(handle_status='handled').count()
    today = datetime.utcnow().strftime('%Y-%m-%d')
    today_count = AlarmEvent.query.filter(AlarmEvent.alarm_time >= today).count()
    return success_response(data={
        'total': total,
        'pending': pending,
        'handled': handled,
        'today_count': today_count
    })
