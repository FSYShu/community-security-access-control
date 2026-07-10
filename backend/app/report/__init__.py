"""
安防监控日报模块蓝图
提供日报列表、日报详情、手动生成日报等接口
"""
from flask import Blueprint

report_bp = Blueprint('report', __name__)


@report_bp.route('/daily/list', methods=['GET'])
def get_daily_report_list():
    """获取安防监控日报列表"""
    # TODO: 实现日报列表查询
    pass


@report_bp.route('/daily/<int:report_id>', methods=['GET'])
def get_daily_report_detail(report_id):
    """获取安防监控日报详情"""
    # TODO: 实现日报详情查询
    pass


@report_bp.route('/daily/generate', methods=['POST'])
def generate_daily_report():
    """手动生成安防监控日报"""
    # TODO: 实现日报手动生成逻辑
    pass