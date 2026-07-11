"""
安防总览模块蓝图
提供总览统计数据、最近告警等接口
"""
from datetime import datetime, timedelta
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from app import db
from app.models.pass_record import PassRecord
from app.models.alarm import AlarmEvent
from app.models.gate import Gate
from app.models.danger_zone import DangerZone
from utils import success_response

dashboard_bp = Blueprint('dashboard', __name__)


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

    inactive_zones = DangerZone.query.filter(
        DangerZone.status != 'active'
    ).count()
    zone_status = '异常' if inactive_zones > 0 else '正常'

    return success_response(data={
        'passCount': pass_count,
        'alarmCount': alarm_count,
        'onlineDevices': online_devices,
        'zoneStatus': zone_status
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
            'time': a.alarm_time,
            'level': 'high' if a.alarm_level in ('high', 'critical') else 'low'
        })

    return success_response(data={'list': result})