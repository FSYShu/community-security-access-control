"""
访客临时授权管理蓝图
"""
import json
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.visitor_auth import VisitorAuth
from utils.response import success_response, error_response
from utils.permissions import admin_required
from core.db_lock import with_write_lock
from core.audit_logger import log_audit

visitor_auth_bp = Blueprint('visitor_auth', __name__)


@visitor_auth_bp.route('/apply', methods=['POST'])
@jwt_required()
@with_write_lock
def apply_visitor_auth():
    """申请访客授权"""
    data = request.get_json()
    visitor_name = data.get('visitor_name', '')
    owner_id = data.get('owner_id')

    if not visitor_name:
        return error_response(message='访客姓名不能为空', code=400)

    current_user = get_jwt_identity()
    if not owner_id:
        owner_id = int(current_user)

    auth = VisitorAuth(
        visitor_name=visitor_name,
        owner_id=owner_id,
        apply_gate_levels=json.dumps(data.get('apply_gate_levels', []), ensure_ascii=False),
        apply_time_range=json.dumps(data.get('apply_time_range', {}), ensure_ascii=False),
        apply_source=data.get('apply_source', 'gate_web'),
        visitor_face_image_path=data.get('visitor_face_image_path', '')
    )
    db.session.add(auth)
    db.session.commit()
    log_audit(operation_type='apply_visitor_auth', operation_content=f'访客申请: {visitor_name}')
    return success_response(data=auth.to_dict(), message='申请已提交')


@visitor_auth_bp.route('/list', methods=['GET'])
@jwt_required()
def list_visitor_auths():
    """获取授权列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')

    query = VisitorAuth.query
    if status_filter:
        query = query.filter_by(approval_status=status_filter)
    query = query.order_by(VisitorAuth.apply_time.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response(data={
        'items': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page
    })


@visitor_auth_bp.route('/<int:auth_id>/approve', methods=['PUT'])
@admin_required
@with_write_lock
def approve_visitor_auth(auth_id):
    """审批访客授权"""
    auth = VisitorAuth.query.get(auth_id)
    if not auth:
        return error_response(message='授权记录不存在', code=404)

    data = request.get_json()
    approval_status = data.get('approval_status', '')
    if approval_status not in ('approved', 'rejected'):
        return error_response(message='审批状态无效', code=400)

    current_user = get_jwt_identity()
    auth.approval_status = approval_status
    auth.approver_id = int(get_jwt_identity())
    from datetime import datetime
    auth.approval_time = datetime.utcnow().isoformat()

    db.session.commit()
    log_audit(operation_type='approve_visitor_auth', operation_content=f'审批访客授权: {auth_id} -> {approval_status}')
    return success_response(data=auth.to_dict(), message='审批完成')