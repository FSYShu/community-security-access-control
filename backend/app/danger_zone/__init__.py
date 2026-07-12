"""
禁区入侵检测模块蓝图
提供禁区管理、入侵检测配置等接口
"""
import json
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.danger_zone import DangerZone
from app.models.gate import Gate
from utils.response import success_response, error_response
from utils.permissions import admin_required
from core.db_lock import with_write_lock
from core.audit_logger import log_audit

danger_zone_bp = Blueprint('danger_zone', __name__)


@danger_zone_bp.route('/list', methods=['GET'])
@jwt_required()
def get_danger_zone_list():
    status = request.args.get('status', '')
    query = DangerZone.query
    if status:
        query = query.filter_by(status=status)
    zones = query.order_by(DangerZone.created_at.desc()).all()
    result = []
    for z in zones:
        d = z.to_dict()
        gate_id_str = z.camera_ids
        if gate_id_str:
            gate_ids = [int(x.strip()) for x in gate_id_str.split(',') if x.strip().isdigit()]
            gates = Gate.query.filter(Gate.id.in_(gate_ids)).all()
            d['camera_names'] = ', '.join(g.gate_name for g in gates)
        else:
            d['camera_names'] = ''
        result.append(d)
    return success_response(data=result)


@danger_zone_bp.route('/add', methods=['POST'])
@admin_required
@with_write_lock
def add_danger_zone():
    data = request.get_json()
    zone_name = data.get('zone_name', '').strip()
    camera_ids = data.get('camera_ids', '')
    safety_distance = data.get('safety_distance', 2.0)
    stay_duration = data.get('stay_duration', 30)
    alarm_level = data.get('alarm_level', 'high')

    if not zone_name:
        return error_response(message='禁区名称不能为空', code=400)

    if not camera_ids:
        return error_response(message='请关联至少一个摄像头', code=400)

    try:
        safety_distance = float(safety_distance)
        if safety_distance <= 0:
            return error_response(message='安全距离必须大于0', code=400)
    except (ValueError, TypeError):
        return error_response(message='安全距离格式错误', code=400)

    try:
        stay_duration = int(stay_duration)
        if stay_duration <= 0:
            return error_response(message='滞留时长必须大于0', code=400)
    except (ValueError, TypeError):
        return error_response(message='滞留时长格式错误', code=400)

    if alarm_level not in ('low', 'medium', 'high'):
        return error_response(message='告警级别无效', code=400)

    zone = DangerZone(
        zone_name=zone_name,
        camera_ids=camera_ids,
        safety_distance=safety_distance,
        stay_duration=stay_duration,
        alarm_level=alarm_level,
        status='active'
    )
    db.session.add(zone)
    db.session.commit()
    log_audit(operation_type='add_danger_zone', operation_content='新增禁区: {}'.format(zone_name))
    return success_response(data=zone.to_dict(), message='新增成功')


@danger_zone_bp.route('/<int:zone_id>', methods=['GET'])
@jwt_required()
def get_danger_zone(zone_id):
    zone = DangerZone.query.get(zone_id)
    if not zone:
        return error_response(message='禁区不存在', code=404)
    return success_response(data=zone.to_dict())


@danger_zone_bp.route('/<int:zone_id>', methods=['PUT'])
@admin_required
@with_write_lock
def update_danger_zone(zone_id):
    zone = DangerZone.query.get(zone_id)
    if not zone:
        return error_response(message='禁区不存在', code=404)

    data = request.get_json()
    if 'zone_name' in data:
        zone_name = data['zone_name'].strip()
        if not zone_name:
            return error_response(message='禁区名称不能为空', code=400)
        zone.zone_name = zone_name

    if 'camera_ids' in data:
        camera_ids = data['camera_ids']
        if not camera_ids:
            return error_response(message='请关联至少一个摄像头', code=400)
        zone.camera_ids = camera_ids

    if 'safety_distance' in data:
        try:
            val = float(data['safety_distance'])
            if val <= 0:
                return error_response(message='安全距离必须大于0', code=400)
            zone.safety_distance = val
        except (ValueError, TypeError):
            return error_response(message='安全距离格式错误', code=400)

    if 'stay_duration' in data:
        try:
            val = int(data['stay_duration'])
            if val <= 0:
                return error_response(message='滞留时长必须大于0', code=400)
            zone.stay_duration = val
        except (ValueError, TypeError):
            return error_response(message='滞留时长格式错误', code=400)

    if 'alarm_level' in data:
        if data['alarm_level'] not in ('low', 'medium', 'high'):
            return error_response(message='告警级别无效', code=400)
        zone.alarm_level = data['alarm_level']

    if 'status' in data:
        if data['status'] not in ('active', 'inactive'):
            return error_response(message='状态值无效', code=400)
        zone.status = data['status']

    db.session.commit()
    log_audit(operation_type='update_danger_zone', operation_content='更新禁区: {}'.format(zone.zone_name))
    return success_response(data=zone.to_dict(), message='更新成功')


@danger_zone_bp.route('/<int:zone_id>', methods=['DELETE'])
@admin_required
@with_write_lock
def delete_danger_zone(zone_id):
    zone = DangerZone.query.get(zone_id)
    if not zone:
        return error_response(message='禁区不存在', code=404)

    zone_name = zone.zone_name
    db.session.delete(zone)
    db.session.commit()
    log_audit(operation_type='delete_danger_zone', operation_content='删除禁区: {}'.format(zone_name))
    return success_response(message='删除成功')


@danger_zone_bp.route('/cameras', methods=['GET'])
@jwt_required()
def get_available_cameras():
    gates = Gate.query.filter(
        Gate.push_key != '', Gate.push_key.isnot(None)
    ).order_by(Gate.created_at.desc()).all()
    result = []
    for g in gates:
        result.append({
            'gate_id': g.id,
            'gate_name': g.gate_name,
            'push_key': g.push_key
        })
    return success_response(data=result)
