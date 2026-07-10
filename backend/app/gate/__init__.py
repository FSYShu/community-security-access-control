"""
门禁终端模块蓝图
提供门禁终端管理、权限配置等接口
"""
from flask import Blueprint

gate_bp = Blueprint('gate', __name__)


@gate_bp.route('/list', methods=['GET'])
def get_gate_list():
    """获取门禁终端列表"""
    # TODO: 实现门禁终端列表查询
    pass


@gate_bp.route('/<int:gate_id>/permission', methods=['PUT'])
def config_gate_permission(gate_id):
    """配置门禁权限"""
    # TODO: 实现门禁权限配置
    pass