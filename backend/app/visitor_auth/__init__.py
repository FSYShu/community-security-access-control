"""
访客临时授权管理蓝图
"""
import json
import os
import base64
import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.visitor_auth import VisitorAuth
from app.models.gate import Gate
from app.models.gate_level import GateLevel
from app.models.face import FaceInfo
from utils.response import success_response, error_response
from utils.permissions import admin_required
from core.db_lock import with_write_lock
from core.audit_logger import log_audit

visitor_auth_bp = Blueprint('visitor_auth', __name__)
logger = logging.getLogger(__name__)


def _verify_gate_terminal(gate_id, push_key):
    """验证门禁终端身份（通过gate_id和push_key）"""
    if not gate_id:
        return None
    try:
        gate_id = int(gate_id)
    except (ValueError, TypeError):
        return None
    gate = Gate.query.get(gate_id)
    if not gate or not gate.bound:
        return None
    if gate.push_key and push_key and gate.push_key != push_key:
        return None
    return gate


def _register_visitor_face(auth, gate):
    """审批通过后注册访客人脸到人脸识别系统"""
    if not auth.visitor_face_image_path:
        logger.warning('Visitor auth %d has no face image, skip registration', auth.id)
        return
    try:
        import cv2
        import numpy as np
        from core.face_recognition import FaceRecognizer
        from flask import current_app

        face_b64 = auth.visitor_face_image_path
        if face_b64.startswith('data:'):
            face_b64 = face_b64.split(',', 1)[1]

        img_data = base64.b64decode(face_b64)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            logger.error('Failed to decode visitor face image for auth %d', auth.id)
            return

        recognizer = FaceRecognizer()
        faces = recognizer.detect_faces(img)
        if not faces:
            logger.error('No face detected in visitor image for auth %d', auth.id)
            return

        face_descriptor = recognizer.compute_face_descriptor(img, faces[0])
        encoding = face_descriptor.tolist()

        allowed_gate_ids = []
        current = gate
        while current:
            allowed_gate_ids.append(current.id)
            if current.parent_gate_id:
                current = Gate.query.get(current.parent_gate_id)
            else:
                current = None
        apply_source = getattr(auth, 'apply_source', '') or ''
        if '|' in apply_source:
            source_name = apply_source.split('|', 1)[1]
            source_gate = Gate.query.filter_by(gate_name=source_name).first()
            if source_gate and source_gate.id not in allowed_gate_ids:
                allowed_gate_ids.append(source_gate.id)

        face_record = FaceInfo(
            person_type='visitor',
            person_name=auth.visitor_name,
            face_image_path=auth.visitor_face_image_path,
            face_feature=json.dumps(encoding),
            allowed_gates=json.dumps(allowed_gate_ids, ensure_ascii=False),
            status='active'
        )
        db.session.add(face_record)
        db.session.commit()

        faces_file = current_app.config.get('REGISTERED_FACES_FILE')
        if not faces_file:
            faces_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'registered_faces.json')

        registered = []
        if os.path.exists(faces_file):
            with open(faces_file, 'r', encoding='utf-8') as f:
                registered = json.load(f)

        from datetime import datetime
        new_record = {
            'id': face_record.id,
            'person_name': auth.visitor_name,
            'person_type': 'visitor',
            'face_descriptor': encoding,
            'registered_at': datetime.utcnow().isoformat()
        }
        registered.append(new_record)

        os.makedirs(os.path.dirname(faces_file), exist_ok=True)
        with open(faces_file, 'w', encoding='utf-8') as f:
            json.dump(registered, f, ensure_ascii=False)

        logger.info('Visitor face registered: %s (auth_id=%d, face_id=%d)', auth.visitor_name, auth.id, face_record.id)

    except Exception as e:
        db.session.rollback()
        logger.error('Failed to register visitor face for auth %d: %s', auth.id, str(e))


@visitor_auth_bp.route('/apply', methods=['POST'])
@jwt_required()
@with_write_lock
def apply_visitor_auth():
    """申请访客授权"""
    data = request.get_json()
    visitor_name = data.get('visitor_name', '')
    owner_id = data.get('owner_id')

    if not visitor_name:
        return error_response(message='访客姓名不能为空', code=400)

    current_user = get_jwt_identity()
    if not owner_id:
        owner_id = int(current_user)

    raw_levels = data.get('apply_gate_levels', [])
    if isinstance(raw_levels, str):
        try:
            raw_levels = json.loads(raw_levels)
        except (json.JSONDecodeError, TypeError):
            raw_levels = []
    level_name_map = {lv.level_code: lv.level_name for lv in GateLevel.query.all()}
    level_names = [level_name_map.get(l, l) if l in level_name_map else l for l in raw_levels]

    auth = VisitorAuth(
        visitor_name=visitor_name,
        owner_id=owner_id,
        apply_gate_levels=json.dumps(level_names, ensure_ascii=False),
        apply_time_range=json.dumps(data.get('apply_time_range', {}), ensure_ascii=False),
        apply_source=data.get('apply_source', 'gate_web'),
        visitor_face_image_path=data.get('visitor_face_image_path', '')
    )
    db.session.add(auth)
    db.session.commit()
    log_audit(operation_type='apply_visitor_auth', operation_content=f'访客申请: {visitor_name}')
    return success_response(data=auth.to_dict(), message='申请已提交')


@visitor_auth_bp.route('/list', methods=['GET'])
@jwt_required()
def list_visitor_auths():
    """获取授权列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')

    query = VisitorAuth.query
    if status_filter:
        query = query.filter_by(approval_status=status_filter)
    query = query.order_by(VisitorAuth.apply_time.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response(data={
        'items': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page
    })


@visitor_auth_bp.route('/<int:auth_id>/approve', methods=['PUT'])
@admin_required
@with_write_lock
def approve_visitor_auth(auth_id):
    """审批访客授权"""
    auth = VisitorAuth.query.get(auth_id)
    if not auth:
        return error_response(message='授权记录不存在', code=404)

    data = request.get_json()
    approval_status = data.get('approval_status', '')
    if approval_status not in ('approved', 'rejected'):
        return error_response(message='审批状态无效', code=400)

    current_user = get_jwt_identity()
    auth.approval_status = approval_status
    auth.approver_id = int(get_jwt_identity())
    from datetime import datetime
    auth.approval_time = datetime.utcnow().isoformat()

    db.session.commit()

    if approval_status == 'approved':

        gate = Gate.query.filter_by(gate_level='community_gate').first()
        _register_visitor_face(auth, gate)

    log_audit(operation_type='approve_visitor_auth', operation_content=f'审批访客授权: {auth_id} -> {approval_status}')
    return success_response(data=auth.to_dict(), message='审批完成')


@visitor_auth_bp.route('/gate-apply', methods=['POST'])
@with_write_lock
def gate_apply_visitor_auth():
    """门禁终端申请访客授权（无需JWT，通过终端身份验证）"""
    data = request.get_json()
    gate_id = data.get('gate_id')
    push_key = data.get('push_key', '')
    gate = _verify_gate_terminal(gate_id, push_key)
    if not gate:
        return error_response(message='终端身份验证失败', code=403)

    visitor_name = data.get('visitor_name', '')
    if not visitor_name:
        return error_response(message='访客姓名不能为空', code=400)

    raw_levels = data.get('apply_gate_levels', [])
    if isinstance(raw_levels, list) and raw_levels:
        gate_names = raw_levels
    else:
        gate_names = []
        current = gate
        while current:
            if current.gate_level != 'entrance_door':
                gate_names.insert(0, current.gate_name)
            if current.parent_gate_id:
                current = Gate.query.get(current.parent_gate_id)
            else:
                current = None

    from datetime import datetime, timedelta, timezone
    cst = timezone(timedelta(hours=8))
    now_cst = datetime.now(cst)

    auth = VisitorAuth(
        visitor_name=visitor_name,
        owner_id=0,
        apply_gate_levels=json.dumps(gate_names, ensure_ascii=False),
        apply_time_range=json.dumps(data.get('apply_time_range', {}), ensure_ascii=False),
        apply_source='gate_terminal|' + gate.gate_name,
        visitor_face_image_path=data.get('visitor_face_image_path', ''),
        apply_time=now_cst.strftime('%Y-%m-%dT%H:%M:%S'),
        visit_address=data.get('visit_address', '')
    )
    db.session.add(auth)
    db.session.commit()
    log_audit(operation_type='gate_apply_visitor_auth', operation_content=f'门禁终端访客申请: {visitor_name}')
    return success_response(data=auth.to_dict(), message='申请已提交')


@visitor_auth_bp.route('/gate-list', methods=['GET'])
def gate_list_visitor_auths():
    """门禁终端获取授权列表（无需JWT，通过终端身份验证，只返回与本终端相关的申请）"""
    gate_id = request.args.get('gate_id', '')
    push_key = request.args.get('push_key', '')
    gate = _verify_gate_terminal(gate_id, push_key)
    if not gate:
        return error_response(message='终端身份验证失败', code=403)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')

    related_names = set()
    related_names.add(gate.gate_name)
    children = Gate.query.filter_by(parent_gate_id=gate.id).all()
    for child in children:
        related_names.add(child.gate_name)
        grandchildren = Gate.query.filter_by(parent_gate_id=child.id).all()
        for gc in grandchildren:
            related_names.add(gc.gate_name)

    query = VisitorAuth.query
    if status_filter:
        query = query.filter_by(approval_status=status_filter)
    all_records = query.order_by(VisitorAuth.apply_time.desc()).all()

    filtered = []
    for auth in all_records:
        matched = False
        try:
            levels = json.loads(auth.apply_gate_levels) if auth.apply_gate_levels else []
            if isinstance(levels, str):
                levels = json.loads(levels)
            for name in related_names:
                if name in levels:
                    matched = True
                    break
        except (json.JSONDecodeError, TypeError):
            pass
        if not matched:
            visit_addr = getattr(auth, 'visit_address', '') or ''
            for name in related_names:
                if name and name in visit_addr:
                    matched = True
                    break
        if matched:
            filtered.append(auth)

    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = filtered[start:end]

    return success_response(data={
        'items': [a.to_dict() for a in page_items],
        'total': total,
        'page': page,
        'per_page': per_page
    })


@visitor_auth_bp.route('/gate-approve/<int:auth_id>', methods=['PUT'])
@with_write_lock
def gate_approve_visitor_auth(auth_id):
    """门禁终端审批访客授权（无需JWT，通过终端身份验证）"""
    data = request.get_json()
    gate_id = data.get('gate_id')
    push_key = data.get('push_key', '')
    gate = _verify_gate_terminal(gate_id, push_key)
    if not gate:
        return error_response(message='终端身份验证失败', code=403)

    auth = VisitorAuth.query.get(auth_id)
    if not auth:
        return error_response(message='授权记录不存在', code=404)

    approval_status = data.get('approval_status', '')
    if approval_status not in ('approved', 'rejected'):
        return error_response(message='审批状态无效', code=400)

    auth.approval_status = approval_status
    from datetime import datetime
    auth.approval_time = datetime.utcnow().isoformat()

    db.session.commit()

    if approval_status == 'approved':

        _register_visitor_face(auth, gate)

    log_audit(operation_type='gate_approve_visitor_auth', operation_content=f'门禁终端审批访客授权: {auth_id} -> {approval_status}')
    return success_response(data=auth.to_dict(), message='审批完成')


@visitor_auth_bp.route('/gate-delete/<int:auth_id>', methods=['DELETE'])
@with_write_lock
def gate_delete_visitor_auth(auth_id):
    """门禁终端删除访客授权记录（通过终端身份验证）"""
    data = request.get_json() or {}
    gate_id = data.get('gate_id')
    push_key = data.get('push_key', '')
    gate = _verify_gate_terminal(gate_id, push_key)
    if not gate:
        return error_response(message='终端身份验证失败', code=403)

    auth = VisitorAuth.query.get(auth_id)
    if not auth:
        return error_response(message='授权记录不存在', code=404)

    db.session.delete(auth)
    db.session.commit()
    log_audit(operation_type='gate_delete_visitor_auth', operation_content=f'门禁终端删除访客授权: {auth_id}')
    return success_response(message='删除成功')