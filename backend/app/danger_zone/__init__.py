"""
禁区入侵检测模块蓝图
提供禁区管理、入侵检测配置等接口
"""
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


@danger_zone_bp.route('/cleanup', methods=['POST'])
@admin_required
@with_write_lock
def cleanup_orphan_zones():
    """清理没有关联门禁的禁区"""
    zones = DangerZone.query.all()
    deleted = []
    for z in zones:
        gate_id_str = z.camera_ids
        if not gate_id_str:
            deleted.append(z.zone_name)
            db.session.delete(z)
            continue
        gate_ids = [int(x.strip()) for x in gate_id_str.split(',') if x.strip().isdigit()]
        existing_gates = Gate.query.filter(Gate.id.in_(gate_ids)).all()
        if not existing_gates:
            deleted.append(z.zone_name)
            db.session.delete(z)
    if deleted:
        db.session.commit()
        log_audit(operation_type='cleanup_orphan_zones', operation_content='清理孤立禁区: {}'.format(', '.join(deleted)))
    return success_response(message='已清理{}个孤立禁区'.format(len(deleted)), data={'deleted': deleted})
