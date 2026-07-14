"""
物业后台管理模块蓝图
提供历史监控日志查询、业主导入等接口
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.pass_record import PassRecord
from app.models.alarm import AlarmEvent
from app.models.face import FaceInfo
from app.models.gate import Gate
from utils.response import success_response, error_response
from utils.permissions import admin_required
from core.db_lock import with_write_lock
from core.audit_logger import log_audit

property_bp = Blueprint('property', __name__)


@property_bp.route('/pass-logs', methods=['GET'])
@jwt_required()
def get_pass_logs():
    """历史通行日志查询"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')
    gate_id = request.args.get('gate_id', '', type=str)
    gate_level = request.args.get('gate_level', '')
    person_type = request.args.get('person_type', '')

    query = PassRecord.query
    if start_time:
        query = query.filter(PassRecord.pass_time >= start_time)
    if end_time:
        query = query.filter(PassRecord.pass_time <= end_time)
    if gate_id:
        query = query.filter_by(gate_id=int(gate_id))

    if gate_level:
        gate_ids = [g.id for g in Gate.query.filter_by(gate_level=gate_level).all()]
        if gate_ids:
            query = query.filter(PassRecord.gate_id.in_(gate_ids))
        else:
            query = query.filter(PassRecord.gate_id == -1)

    if person_type:
        query = query.filter_by(person_type=person_type)

    query = query.order_by(PassRecord.pass_time.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for r in pagination.items:
        d = r.to_dict()
        gate = Gate.query.get(r.gate_id)
        d['gate_name'] = gate.gate_name if gate else ''
        d['gate_level'] = gate.gate_level if gate else ''
        if not r.person_name and r.face_id:
            face = FaceInfo.query.get(r.face_id)
            d['person_name'] = face.person_name if face else ''
            d['person_type'] = face.person_type if face else ''
        items.append(d)

    return success_response(data={
        'items': items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page
    })



@property_bp.route('/import-owners', methods=['POST'])
@admin_required
@with_write_lock
def import_owners():
    """从物业基础系统批量导入业主数据"""
    data = request.get_json()
    owners = data.get('owners', [])

    if not owners:
        return error_response(message='导入数据不能为空', code=400)

    from app.models.user import User
    imported = 0
    errors = []

    for owner_data in owners:
        username = owner_data.get('username', '')
        real_name = owner_data.get('real_name', '')
        if not username or not real_name:
            errors.append(f'缺少用户名或姓名: {username}')
            continue

        if User.query.filter_by(username=username).first():
            errors.append(f'用户名已存在: {username}')
            continue

        user = User(
            username=username,
            real_name=real_name,
            role='owner',
            phone=owner_data.get('phone', '')
        )
        user.set_password(owner_data.get('password', '123456'))
        db.session.add(user)
        imported += 1

    db.session.commit()
    log_audit(operation_type='import_owners', operation_content=f'批量导入业主: 成功{imported}条, 失败{len(errors)}条')
    return success_response(data={'imported': imported, 'errors': errors}, message=f'导入完成，成功{imported}条')
