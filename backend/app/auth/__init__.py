"""
认证模块蓝图
提供登录、登出、获取用户信息等接口
"""
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app import db
from app.models.user import User
from utils.response import success_response, error_response

auth_bp = Blueprint('auth', __name__)


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

    # 生成 JWT Token
    identity = {'user_id': user.id, 'username': user.username, 'role': user.role}
    access_token = create_access_token(identity=identity)

    return success_response(data={
        'token': access_token,
        'user': user.to_dict()
    }, message='登录成功')


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    return success_response(message='登出成功')


@auth_bp.route('/userinfo', methods=['GET'])
@jwt_required()
def get_user_info():
    """获取当前用户信息"""
    current_user = get_jwt_identity()
    user = User.query.get(current_user.get('user_id'))
    if not user:
        return error_response(message='用户不存在', code=404)
    return success_response(data=user.to_dict())