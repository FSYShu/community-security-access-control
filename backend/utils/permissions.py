"""
权限校验装饰器
"""
from functools import wraps
from flask import request
from flask_jwt_extended import get_jwt_identity, get_jwt, verify_jwt_in_request
from utils.response import error_response


def _get_current_user_info():
    verify_jwt_in_request()
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    return {
        'user_id': user_id,
        'username': claims.get('username', ''),
        'role': claims.get('role', '')
    }


def role_required(*roles):
    """角色权限校验装饰器"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            current_user = _get_current_user_info()
            user_role = current_user.get('role', '')
            if user_role not in roles:
                return error_response(message='权限不足', code=403, http_status=403)
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def admin_required(fn):
    """管理员权限校验"""
    return role_required('admin')(fn)


def guard_or_admin_required(fn):
    """安保人员或管理员权限校验"""
    return role_required('admin', 'guard')(fn)



def owner_self_required(fn):
    """业主自身资源权限校验：owner角色且只能操作自己的资源"""
    @wraps(fn)
    def decorator(*args, **kwargs):
        current_user = _get_current_user_info()
        user_role = current_user.get('role', '')
        user_id = current_user.get('user_id')
        if user_role == 'admin':
            return fn(*args, **kwargs)
        if user_role != 'owner':
            return error_response(message='权限不足', code=403, http_status=403)
        owner_id = kwargs.get('owner_id') or request.args.get('owner_id') or request.get_json(silent=True) and request.get_json().get('owner_id')
        if owner_id and int(owner_id) != user_id:
            return error_response(message='只能操作自己的资源', code=403, http_status=403)
        return fn(*args, **kwargs)
    return decorator
