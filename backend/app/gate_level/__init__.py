"""
门禁终端层级管理蓝图
"""
import json
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.gate_level import GateLevel
from utils.response import success_response, error_response
from utils.permissions import admin_required
from core.db_lock import with_write_lock
from core.audit_logger import log_audit

gate_level_bp = Blueprint('gate_level', __name__)


@gate_level_bp.route('/list', methods=['GET'])
@jwt_required()
def list_gate_levels():
    """获取层级列表"""
    levels = GateLevel.query.all()
    return success_response(data=[l.to_dict() for l in levels])


@gate_level_bp.route('/add', methods=['POST'])
@admin_required
@with_write_lock
def add_gate_level():
    """新增层级"""
    data = request.get_json()
    level_code = data.get('level_code', '')
    level_name = data.get('level_name', '')

    if not level_code or not level_name:
        return error_response(message='层级编码和名称不能为空', code=400)

    if GateLevel.query.get(level_code):
        return error_response(message='层级编码已存在', code=400)

    level = GateLevel(
        level_code=level_code,
        level_name=level_name,
        security_level=data.get('security_level', '一般'),
        default_pass_policy=json.dumps(data.get('default_pass_policy', {}), ensure_ascii=False),
        allow_custom_override=1 if data.get('allow_custom_override', True) else 0,
        status=data.get('status', 'active')
    )
    db.session.add(level)
    db.session.commit()
    log_audit(operation_type='add_gate_level', operation_content=f'新增层级: {level_code}')
    return success_response(data=level.to_dict(), message='新增成功')


@gate_level_bp.route('/<code>', methods=['PUT'])
@admin_required
@with_write_lock
def update_gate_level(code):
    """更新层级"""
    level = GateLevel.query.get(code)
    if not level:
        return error_response(message='层级不存在', code=404)

    data = request.get_json()
    if 'level_name' in data:
        level.level_name = data['level_name']
    if 'security_level' in data:
        level.security_level = data['security_level']
    if 'default_pass_policy' in data:
        level.default_pass_policy = json.dumps(data['default_pass_policy'], ensure_ascii=False)
    if 'allow_custom_override' in data:
        level.allow_custom_override = 1 if data['allow_custom_override'] else 0
    if 'status' in data:
        level.status = data['status']

    db.session.commit()
    log_audit(operation_type='update_gate_level', operation_content=f'更新层级: {code}')
    return success_response(data=level.to_dict(), message='更新成功')


@gate_level_bp.route('/<code>', methods=['DELETE'])
@admin_required
@with_write_lock
def delete_gate_level(code):
    """删除层级"""
    level = GateLevel.query.get(code)
    if not level:
        return error_response(message='层级不存在', code=404)

    db.session.delete(level)
    db.session.commit()
    log_audit(operation_type='delete_gate_level', operation_content=f'删除层级: {code}')
    return success_response(message='删除成功')