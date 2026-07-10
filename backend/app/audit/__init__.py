"""
审计日志蓝图
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.models.audit_log import AuditLog
from utils.response import success_response, error_response
from utils.permissions import admin_required

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('/list', methods=['GET'])
@admin_required
def list_audit_logs():
    """获取审计日志列表（仅admin角色）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    operator_id = request.args.get('operator_id', '', type=str)
    operation_type = request.args.get('operation_type', '', type=str)
    start_time = request.args.get('start_time', '', type=str)
    end_time = request.args.get('end_time', '', type=str)

    query = AuditLog.query
    if operator_id:
        query = query.filter_by(operator_id=int(operator_id))
    if operation_type:
        query = query.filter_by(operation_type=operation_type)
    if start_time:
        query = query.filter(AuditLog.operation_time >= start_time)
    if end_time:
        query = query.filter(AuditLog.operation_time <= end_time)

    query = query.order_by(AuditLog.operation_time.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response(data={
        'items': [l.to_dict() for l in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page
    })