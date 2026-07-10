"""
人脸识别通行模块蓝图
提供人脸信息管理、通行识别、访客授权等接口
"""
from flask import Blueprint

face_bp = Blueprint('face', __name__)


@face_bp.route('/list', methods=['GET'])
def get_face_list():
    """获取人脸信息列表"""
    # TODO: 实现人脸信息列表查询
    pass


@face_bp.route('/add', methods=['POST'])
def add_face():
    """新增人脸信息"""
    # TODO: 实现人脸信息新增
    pass


@face_bp.route('/<int:face_id>', methods=['PUT'])
def update_face(face_id):
    """更新人脸信息"""
    # TODO: 实现人脸信息更新
    pass


@face_bp.route('/<int:face_id>', methods=['DELETE'])
def delete_face(face_id):
    """删除人脸信息"""
    # TODO: 实现人脸信息删除
    pass


@face_bp.route('/pass', methods=['POST'])
def submit_face_pass():
    """提交人脸识别通行请求"""
    # TODO: 实现人脸通行识别逻辑
    pass


@face_bp.route('/records', methods=['GET'])
def get_pass_records():
    """获取通行记录列表"""
    # TODO: 实现通行记录查询
    pass


@face_bp.route('/visitor-auth', methods=['POST'])
def apply_visitor_auth():
    """申请访客临时授权"""
    # TODO: 实现访客临时授权逻辑
    pass