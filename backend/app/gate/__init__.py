"""
门禁终端模块蓝图
提供门禁终端管理、权限配置等接口
"""
import json
import re
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db, limiter
from app.models.gate import Gate
from app.models.gate_level import GateLevel
from app.models.pass_record import PassRecord
from utils.response import success_response, error_response
from utils.permissions import admin_required
from core.db_lock import with_write_lock
from core.audit_logger import log_audit

gate_bp = Blueprint('gate', __name__)

HEARTBEAT_TIMEOUT_SECONDS = 30
_CST = timezone(timedelta(hours=8))


def _update_offline_status():
    """将心跳超时的已绑定终端标记为离线"""
    now = datetime.now(_CST)
    timeout = (now - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)).isoformat()
    gates = Gate.query.filter(
        Gate.bound == 1,
        Gate.status == 'online',
        Gate.last_heartbeat != '',
        Gate.last_heartbeat.isnot(None),
        Gate.last_heartbeat < timeout
    ).all()
    for g in gates:
        g.status = 'offline'
    if gates:
        db.session.commit()


@gate_bp.route('/list', methods=['GET'])
@jwt_required()
@limiter.exempt
def get_gate_list():
    """获取门禁终端列表"""
    _update_offline_status()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    gate_level = request.args.get('gate_level', '')
    status = request.args.get('status', '')
    keyword = request.args.get('keyword', '')

    query = Gate.query
    if keyword:
        query = query.filter(Gate.gate_name.contains(keyword))
    if gate_level:
        query = query.filter_by(gate_level=gate_level)
    if status == 'unbound':
        query = query.filter_by(bound=0)
    elif status:
        query = query.filter_by(bound=1, status=status)

    query = query.order_by(Gate.created_at.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for g in pagination.items:
        d = g.to_dict()
        level = GateLevel.query.get(g.gate_level)
        d['level_name'] = level.level_name if level else g.gate_level
        d['security_level'] = level.security_level if level else ''
        if g.parent_gate_id:
            pg = Gate.query.get(g.parent_gate_id)
            d['parent_gate_name'] = pg.gate_name if pg else ''
        if g.stream_channel_id:
            from app.models.stream_channel import StreamChannel
            ch = StreamChannel.query.get(g.stream_channel_id)
            d['stream_channel_name'] = ch.channel_name if ch else ''
        if g.push_key:
            d['push_key'] = g.push_key
        items.append(d)

    return success_response(data={
        'items': items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page
    })


@gate_bp.route('/unit-doors', methods=['GET'])
@jwt_required()
@limiter.exempt
def get_unit_doors():
    """获取单元门列表（供入户门绑定选择）"""
    gates = Gate.query.filter_by(gate_level='unit_door').order_by(Gate.created_at.desc()).all()
    items = [{'id': g.id, 'gate_name': g.gate_name} for g in gates]
    return success_response(data=items)


@gate_bp.route('/public-addresses', methods=['GET'])
@limiter.exempt
def get_public_addresses():
    """获取门禁地址数据（公开接口，无需认证）"""
    unit_doors = Gate.query.filter_by(gate_level='unit_door').order_by(Gate.created_at.asc()).all()
    entrance_doors = Gate.query.filter_by(gate_level='entrance_door').order_by(Gate.created_at.asc()).all()
    items = []
    for g in unit_doors:
        items.append({'gate_name': g.gate_name, 'gate_level': g.gate_level})
    for g in entrance_doors:
        items.append({'gate_name': g.gate_name, 'gate_level': g.gate_level})
    return success_response(data={'items': items})


@gate_bp.route('/with-stream', methods=['GET'])
@limiter.exempt
@jwt_required()
def get_gates_with_stream():
    """获取绑定了视频流的门禁终端列表"""
    gates = Gate.query.filter(Gate.push_key != '', Gate.push_key.isnot(None), Gate.gate_level != 'entrance_door').order_by(Gate.created_at.desc()).all()
    items = []
    for g in gates:
        d = g.to_dict()
        level = GateLevel.query.get(g.gate_level)
        d['level_name'] = level.level_name if level else g.gate_level
        items.append(d)
    return success_response(data=items)


@gate_bp.route('/<int:gate_id>', methods=['GET'])
@jwt_required()
def get_gate_detail(gate_id):
    """获取门禁终端详情"""
    gate = Gate.query.get(gate_id)
    if not gate:
        return error_response(message='门禁终端不存在', code=404)
    d = gate.to_dict()
    level = GateLevel.query.get(gate.gate_level)
    d['level_name'] = level.level_name if level else gate.gate_level
    if gate.parent_gate_id:
        pg = Gate.query.get(gate.parent_gate_id)
        d['parent_gate_name'] = pg.gate_name if pg else ''
    return success_response(data=d)


@gate_bp.route('/add', methods=['POST'])
@admin_required
@with_write_lock
def add_gate():
    """新增门禁终端"""
    data = request.get_json()
    gate_name = data.get('gate_name', '')
    gate_level = data.get('gate_level', '')

    if not gate_name or not gate_level:
        return error_response(message='终端名称和层级不能为空', code=400)

    GATE_NAME_PATTERNS = {
        'community_gate': r'^(东|南|西|北|东南|东北|西南|西北)\d+门$',
        'unit_door': r'^\d+栋\d+单元$',
        'entrance_door': r'^\d+栋\d+单元\d+室$',
    }
    pattern = GATE_NAME_PATTERNS.get(gate_level)
    if pattern and not re.match(pattern, gate_name):
        name_tips = {
            'community_gate': '社区大门名称格式：方位+数字+门，如东1门、西南2门',
            'unit_door': '单元门名称格式：数字+栋+数字+单元，如3栋2单元',
            'entrance_door': '入户门名称格式：数字+栋+数字+单元+数字+室，如3栋2单元501室',
        }
        return error_response(message=name_tips.get(gate_level, '名称格式不正确'), code=400)

    level = GateLevel.query.get(gate_level)
    if not level:
        return error_response(message='终端层级不存在', code=400)

    parent_gate_id = data.get('parent_gate_id')
    if gate_level == 'entrance_door':
        if not parent_gate_id:
            return error_response(message='入户门必须绑定对应的单元门', code=400)
        parent_gate = Gate.query.get(parent_gate_id)
        if not parent_gate or parent_gate.gate_level != 'unit_door':
            return error_response(message='绑定的上级终端必须是单元门', code=400)

    require_secondary_auth = 1 if gate_level == 'dangerous_area' else 0

    default_policy = {}
    try:
        default_policy = json.loads(level.default_pass_policy)
    except Exception:
        pass

    gate = Gate(
        gate_name=gate_name,

        gate_level=gate_level,
        building_unit=data.get('building_unit', ''),
        parent_gate_id=parent_gate_id if gate_level == 'entrance_door' else None,
        camera_id=data.get('camera_id'),
        stream_channel_id=data.get('stream_channel_id'),
        push_key=data.get('push_key', ''),
        pass_time_config=json.dumps(data.get('pass_time_config', default_policy), ensure_ascii=False),
        allowed_persons=json.dumps(data.get('allowed_persons', default_policy), ensure_ascii=False),
        custom_pass_policy=json.dumps(data.get('custom_pass_policy', {}), ensure_ascii=False),
        require_secondary_auth=require_secondary_auth,
        status=data.get('status', 'online')
    )
    db.session.add(gate)
    db.session.commit()

    if gate_level == 'dangerous_area':
        from app.models.danger_zone import DangerZone
        existing = DangerZone.query.filter_by(camera_ids=str(gate.id)).first()
        if not existing:
            zone = DangerZone(
                zone_name=gate_name,
                camera_ids=str(gate.id),
                safety_distance=2.0,
                stay_duration=30,
                alarm_level='high',
                status='active'
            )
            db.session.add(zone)
            db.session.commit()

    log_audit(operation_type='add_gate', operation_content=f'新增门禁终端: {gate_name}')
    return success_response(data=gate.to_dict(), message='新增成功')


@gate_bp.route('/<int:gate_id>', methods=['PUT'])
@admin_required
@with_write_lock
def update_gate(gate_id):
    """更新门禁终端"""
    gate = Gate.query.get(gate_id)
    if not gate:
        return error_response(message='门禁终端不存在', code=404)

    data = request.get_json()
    if 'gate_name' in data:
        gate.gate_name = data['gate_name']

    effective_level = data.get('gate_level', gate.gate_level)
    effective_name = data.get('gate_name', gate.gate_name)
    GATE_NAME_PATTERNS = {
        'community_gate': r'^(东|南|西|北|东南|东北|西南|西北)\d+门$',
        'unit_door': r'^\d+栋\d+单元$',
        'entrance_door': r'^\d+栋\d+单元\d+室$',
    }
    pattern = GATE_NAME_PATTERNS.get(effective_level)
    if pattern and not re.match(pattern, effective_name):
        name_tips = {
            'community_gate': '社区大门名称格式：方位+数字+门，如东1门、西南2门',
            'unit_door': '单元门名称格式：数字+栋+数字+单元，如3栋2单元',
            'entrance_door': '入户门名称格式：数字+栋+数字+单元+数字+室，如3栋2单元501室',
        }
        return error_response(message=name_tips.get(effective_level, '名称格式不正确'), code=400)

    if 'gate_level' in data:
        old_level = gate.gate_level
        gate.gate_level = data['gate_level']
        if data['gate_level'] == 'entrance_door':
            parent_id = data.get('parent_gate_id')
            if not parent_id:
                return error_response(message='入户门必须绑定对应的单元门', code=400)
            parent_gate = Gate.query.get(parent_id)
            if not parent_gate or parent_gate.gate_level != 'unit_door':
                return error_response(message='绑定的上级终端必须是单元门', code=400)
            gate.parent_gate_id = parent_id
        else:
            gate.parent_gate_id = None
        if old_level == 'dangerous_area' and data['gate_level'] != 'dangerous_area':
            from app.models.danger_zone import DangerZone
            zones = DangerZone.query.all()
            for z in zones:
                ids = [x.strip() for x in (z.camera_ids or '').split(',')]
                if str(gate_id) in ids:
                    db.session.delete(z)
    if 'building_unit' in data:
        gate.building_unit = data['building_unit']
    if 'camera_id' in data:
        gate.camera_id = data['camera_id']
    if 'stream_channel_id' in data:
        gate.stream_channel_id = data['stream_channel_id']
    if 'push_key' in data:
        gate.push_key = data['push_key']
    if 'status' in data:
        gate.status = data['status']

    db.session.commit()

    if gate.gate_level == 'dangerous_area':
        from app.models.danger_zone import DangerZone
        existing = DangerZone.query.filter_by(camera_ids=str(gate.id)).first()
        if not existing:
            zone = DangerZone(
                zone_name=gate.gate_name,
                camera_ids=str(gate.id),
                safety_distance=2.0,
                stay_duration=30,
                alarm_level='high',
                status='active'
            )
            db.session.add(zone)
            db.session.commit()

    log_audit(operation_type='update_gate', operation_content=f'更新门禁终端: {gate_id}')
    return success_response(data=gate.to_dict(), message='更新成功')


@gate_bp.route('/<int:gate_id>', methods=['DELETE'])
@admin_required
@with_write_lock
def delete_gate(gate_id):
    """删除门禁终端"""
    gate = Gate.query.get(gate_id)
    if not gate:
        return error_response(message='门禁终端不存在', code=404)

    related_count = PassRecord.query.filter_by(gate_id=gate_id).count()
    if related_count > 0:
        return error_response(message=f'该终端存在{related_count}条关联通行记录，无法删除', code=400)

    if gate.gate_level == 'dangerous_area':
        from app.models.danger_zone import DangerZone
        zone = DangerZone.query.filter_by(camera_ids=str(gate_id)).first()
        if zone:
            db.session.delete(zone)

    db.session.delete(gate)
    db.session.commit()
    log_audit(operation_type='delete_gate', operation_content=f'删除门禁终端: {gate_id}')
    return success_response(message='删除成功')


@gate_bp.route('/<int:gate_id>/permission', methods=['PUT'])
@admin_required
@with_write_lock
def config_gate_permission(gate_id):
    """配置门禁权限"""
    gate = Gate.query.get(gate_id)
    if not gate:
        return error_response(message='门禁终端不存在', code=404)

    data = request.get_json()
    level = GateLevel.query.get(gate.gate_level)
    if not level:
        return error_response(message='终端层级信息缺失', code=400)

    if 'custom_pass_policy' in data:
        if not level.allow_custom_override:
            return error_response(message='该层级不允许自定义策略覆盖', code=400)
        custom = data['custom_pass_policy']
        if gate.gate_level == 'dangerous_area':
            if custom.get('allow_all_owners'):
                return error_response(message='危险防护区域不允许设置为所有业主通行', code=400)
        gate.custom_pass_policy = json.dumps(custom, ensure_ascii=False)

    if 'pass_time_config' in data:
        gate.pass_time_config = json.dumps(data['pass_time_config'], ensure_ascii=False)

    if 'allowed_persons' in data:
        gate.allowed_persons = json.dumps(data['allowed_persons'], ensure_ascii=False)

    if 'require_secondary_auth' in data:
        if gate.gate_level == 'dangerous_area' and not data['require_secondary_auth']:
            return error_response(message='危险防护区域必须启用二次验证', code=400)
        gate.require_secondary_auth = 1 if data['require_secondary_auth'] else 0

    db.session.commit()
    log_audit(operation_type='config_gate_permission', operation_content=f'配置门禁权限: {gate_id}')
    return success_response(data=gate.to_dict(), message='权限配置成功')


@gate_bp.route('/<int:gate_id>/bind', methods=['POST'])
@jwt_required()
@with_write_lock
def bind_gate(gate_id):
    """门禁终端绑定"""
    gate = Gate.query.get(gate_id)
    if not gate:
        return error_response(message='门禁终端不存在', code=404)
    gate.bound = 1
    db.session.commit()
    return success_response(data=gate.to_dict(), message='绑定成功')


@gate_bp.route('/<int:gate_id>/unbind', methods=['POST'])
@jwt_required()
@with_write_lock
def unbind_gate(gate_id):
    """门禁终端解绑"""
    gate = Gate.query.get(gate_id)
    if not gate:
        return error_response(message='门禁终端不存在', code=404)
    push_key = gate.push_key
    gate.bound = 0
    db.session.commit()
    if push_key:
        try:
            from core.rtmp_relay import stop_ffmpeg
            stop_ffmpeg(push_key)
        except Exception:
            pass
    try:
        gate_data = gate.to_dict()
    except Exception:
        gate_data = {'id': gate.id, 'gate_name': gate.gate_name, 'bound': False}
    return success_response(data=gate_data, message='解绑成功')
