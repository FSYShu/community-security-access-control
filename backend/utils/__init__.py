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


def error_response(message='操作失败', code=-1, http_status=200):
    """错误响应"""
    response = {
        'code': code,
        'message': message,
        'data': None
    }
    return jsonify(response), http_status


def paginate_response(query, page, per_page, schema):
    """分页响应"""
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return success_response({
        'items': schema.dump(pagination.items),
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    })