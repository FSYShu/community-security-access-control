"""
认证模块蓝图
提供登录、登出、获取用户信息、用户注册/管理等接口
"""
import logging
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt_identity, get_jwt, jwt_required

from app import db
from app.models.user import User
from utils.response import success_response, error_response
from utils.permissions import admin_required
from core.audit_logger import log_audit

auth_bp = Blueprint('auth', __name__)

logger = logging.getLogger(__name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')

    if not username or not password:
        return error_response(message='用户名和密码不能为空', code=400)

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return error_response(message='用户名或密码错误', code=401)

    if user.status != 'active':
        return error_response(message='账号已被禁用', code=403)

    identity = str(user.id)
    additional_claims = {'username': user.username, 'role': user.role}
    access_token = create_access_token(identity=identity, additional_claims=additional_claims)

    log_audit(operator_id=user.id, operation_type='USER_LOGIN', operation_content=f'用户登录: {username}', ip_address=request.remote_addr)

    return success_response(data={
        'token': access_token,
        'user': user.to_dict()
    }, message='登录成功')


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    current_user = get_jwt_identity()
    claims = get_jwt()
    log_audit(operator_id=int(current_user), operation_type='USER_LOGOUT', operation_content=f'用户登出: {claims.get("username", "")}', ip_address=request.remote_addr)
    return success_response(message='登出成功')


@auth_bp.route('/userinfo', methods=['GET'])
@jwt_required()
def get_user_info():
    """获取当前用户信息"""
    current_user = get_jwt_identity()
    claims = get_jwt()
    user = User.query.get(int(current_user))
    if not user:
        return error_response(message='用户不存在', code=404)
    return success_response(data=user.to_dict())


@auth_bp.route('/register', methods=['POST'])
@admin_required
def register():
    """管理员注册新用户（仅admin角色可调用）"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    role = data.get('role', 'owner')

    if not username or not password:
        return error_response(message='用户名和密码不能为空', code=400)

    if role not in ('owner', 'admin', 'guard'):
        return error_response(message='角色类型无效，仅支持 owner/admin/guard', code=400)

    if User.query.filter_by(username=username).first():
        return error_response(message='用户名已存在', code=400)

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return success_response(data=user.to_dict(), message='注册成功')


@auth_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """获取用户列表（仅admin角色可调用）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    keyword = request.args.get('keyword', '')

    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if keyword:
        query = query.filter(User.username.contains(keyword))

    query = query.order_by(User.id.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response(data={
        'items': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    })


@auth_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """获取指定用户信息（仅admin角色可调用）"""
    user = User.query.get(user_id)
    if not user:
        return error_response(message='用户不存在', code=404)
    return success_response(data=user.to_dict())


@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """更新用户信息（仅admin角色可调用）"""
    user = User.query.get(user_id)
    if not user:
        return error_response(message='用户不存在', code=404)

    data = request.get_json()

    if 'status' in data and data['status'] in ('active', 'disabled'):
        user.status = data['status']

    if 'password' in data and data['password']:
        old_password = data.get('old_password', '')
        if not old_password:
            return error_response(message='请输入原密码', code=400)
        if not user.check_password(old_password):
            return error_response(message='原密码错误', code=400)
        user.set_password(data['password'])

    db.session.commit()
    return success_response(data=user.to_dict(), message='更新成功')


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户（仅admin角色可调用）"""
    current_identity = get_jwt_identity()
    if int(current_identity) == user_id:
        return error_response(message='不能删除自己的账号', code=400)

    user = User.query.get(user_id)
    if not user:
        return error_response(message='用户不存在', code=404)

    db.session.delete(user)
    db.session.commit()
    return success_response(message='删除成功')


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改密码"""
    current_user = get_jwt_identity()
    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return error_response(message='旧密码和新密码不能为空', code=400)

    user = User.query.get(int(current_user))
    if not user:
        return error_response(message='用户不存在', code=404)

    if not user.check_password(old_password):
        return error_response(message='旧密码错误', code=400)

    user.set_password(new_password)
    db.session.commit()

    log_audit(operator_id=user.id, operation_type='USER_CHANGE_PASSWORD', operation_content='修改密码', ip_address=request.remote_addr)

    return success_response(message='密码修改成功')


ROLE_PERMISSIONS = {
    'admin': {
        'label': '管理员',
        'permissions': [
            '用户权限管理（新增/编辑/删除用户）',
            '门禁终端管理（新增/编辑/删除/权限配置）',
            '人脸信息管理',
            '物业后台管理',
            '安防监控日报（生成/删除）',
            '告警处置与导出',
            '视频监控与回放',
            '审计日志查看',
            '通行日志查看'
        ]
    },
    'guard': {
        'label': '安保人员',
        'permissions': [
            '告警处置与导出',
            '视频监控与回放',
            '通行日志查看',
            '安防监控日报（查看）'
        ]
    }
}


@auth_bp.route('/role-permissions', methods=['GET'])
@jwt_required()
def get_role_permissions():
    """获取角色权限说明"""
    return success_response(data=ROLE_PERMISSIONS)
