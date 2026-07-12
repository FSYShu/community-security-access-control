"""
安防总览模块蓝图
提供总览统计数据、最近告警等接口
"""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from app import db
from app.models.pass_record import PassRecord
from app.models.alarm import AlarmEvent
from app.models.gate import Gate
from app.models.danger_zone import DangerZone
from utils import success_response

dashboard_bp = Blueprint('dashboard', __name__)


def _format_alarm_time(time_str):
    if not time_str:
        return ''
    try:
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone(timedelta(hours=8)))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, AttributeError):
        return time_str[:19].replace('T', ' ') if len(time_str) >= 19 else time_str


@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """获取总览统计数据"""
    today = datetime.utcnow().strftime('%Y-%m-%d')

    pass_count = PassRecord.query.filter(
        PassRecord.pass_time.like(today + '%')
    ).count()

    alarm_count = AlarmEvent.query.filter_by(handle_status='pending').count()

    online_devices = Gate.query.filter_by(status='online').count()

    zones = DangerZone.query.all()
    alarming_zone_ids = set()
    if zones:
        pending_alarms = AlarmEvent.query.filter_by(
            handle_status='pending', source_type='danger_zone'
        ).with_entities(AlarmEvent.source_id).distinct().all()
        alarming_zone_ids = {a[0] for a in pending_alarms}

    zone_list = []
    has_alarm = False
    has_inactive = False
    for z in zones:
        if z.status != 'active':
            status_text = '已停用'
            has_inactive = True
        elif z.id in alarming_zone_ids:
            status_text = '告警中'
            has_alarm = True
        else:
            status_text = '正常运行'
        zone_list.append({
            'id': z.id,
            'zone_name': z.zone_name,
            'status': z.status,
            'status_text': status_text
        })

    if has_alarm:
        zone_status = '告警中'
    elif has_inactive and not any(z['status_text'] == '正常运行' for z in zone_list):
        zone_status = '已停用'
    else:
        zone_status = '正常运行'

    return success_response(data={
        'passCount': pass_count,
        'alarmCount': alarm_count,
        'onlineDevices': online_devices,
        'zoneStatus': zone_status,
        'zoneList': zone_list
    })


@dashboard_bp.route('/recent-alarms', methods=['GET'])
@jwt_required()
def get_recent_alarms():
    """获取最近告警列表"""
    limit = request.args.get('limit', 5, type=int)

    query = AlarmEvent.query.order_by(AlarmEvent.alarm_time.desc())
    if get_jwt().get('role') != 'admin':
        query = query.filter_by(handler_id=int(get_jwt_identity()))

    alarms = query.limit(limit).all()

    result = []
    for a in alarms:
        result.append({
            'id': a.id,
            'title': a.alarm_description,
            'location': a.source_type,
            'time': _format_alarm_time(a.alarm_time),
            'level': 'high' if a.alarm_level in ('high', 'critical') else 'low'
        })

    return success_response(data={'list': result})