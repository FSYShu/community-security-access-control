"""
统一响应工具
"""
from flask import jsonify


def success_response(data=None, message='操作成功', code=0):
    """成功响应"""
    response = {
        'code': code,
        'message': message,
        'data': data
    }
    return jsonify(response)


def error_response(message='操作失败', code=-1, http_status=200, errors=None):
    """错误响应"""
    response = {
        'code': code,
        'message': message,
        'data': errors
    }
    return jsonify(response), http_status


def paginate_response(items, total, page, per_page, message='查询成功'):
    """分页响应"""
    return success_response(data={
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page
    }, message=message)
