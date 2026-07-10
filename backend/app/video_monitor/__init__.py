"""
视频监控模块蓝图
提供监控区域列表、视频回放等接口
"""
from flask import Blueprint

video_monitor_bp = Blueprint('video_monitor', __name__)


@video_monitor_bp.route('/list', methods=['GET'])
def get_monitor_list():
    """获取监控区域列表"""
    # TODO: 实现监控区域列表查询
    pass


@video_monitor_bp.route('/<int:monitor_id>/playback', methods=['GET'])
def get_video_playback(monitor_id):
    """获取视频回放地址"""
    # TODO: 实现视频回放地址获取
    pass