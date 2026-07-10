"""
权限校验装饰器
"""
from functools import wraps
from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from utils.response import error_response


def role_required(*roles):
    """角色权限校验装饰器"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            current_user = get_jwt_identity()
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