"""
物业后台管理模块蓝图
提供历史监控日志查询等接口
"""
from flask import Blueprint

property_bp = Blueprint('property', __name__)


@property_bp.route('/log/history', methods=['GET'])
def get_history_logs():
    """获取历史监控日志"""
    # TODO: 实现历史监控日志查询
    pass