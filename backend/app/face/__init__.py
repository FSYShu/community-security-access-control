"""
人脸识别通行模块蓝图
提供人脸信息管理、通行识别、访客授权等接口
"""
import os
import base64
import json
import logging
import cv2
import numpy as np
from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app import db, limiter
from app.models.face import FaceInfo
from app.models.pass_record import PassRecord
from app.models.visitor_auth import VisitorAuth
from utils.response import success_response, error_response
from utils.permissions import admin_required, owner_self_required
from core.db_lock import with_write_lock
from core.audit_logger import log_audit
from core.face_recognition import FaceRecognizer, load_registered_faces

logger = logging.getLogger(__name__)

face_bp = Blueprint('face', __name__)


def _remove_visitor_access(face_info):
    """访客通过所有申请门禁后，删除其人脸记录和授权记录"""
    try:
        from flask import current_app
        faces_file = current_app.config.get('REGISTERED_FACES_FILE')
        if not faces_file:
            faces_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'registered_faces.json')

        registered = []
        if os.path.exists(faces_file):
            with open(faces_file, 'r', encoding='utf-8') as f:
                registered = json.load(f)
        registered = [r for r in registered if r.get('id') != face_info.id]
        with open(faces_file, 'w', encoding='utf-8') as f:
            json.dump(registered, f, ensure_ascii=False)

        db.session.delete(face_info)
        VisitorAuth.query.filter_by(visitor_name=face_info.person_name, approval_status='approved').delete()
        db.session.commit()
        logger.info('Visitor access removed: %s (face_id=%d)', face_info.person_name, face_info.id)
    except Exception as e:
        db.session.rollback()
        logger.error('Failed to remove visitor access for face_id=%d: %s', face_info.id, str(e))


@face_bp.route('/list', methods=['GET'])
@jwt_required()
@limiter.exempt
def get_face_list():
    """获取人脸信息列表"""
    current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    person_type = request.args.get('person_type', '')
    status = request.args.get('status', '')
    keyword = request.args.get('keyword', '')

    query = FaceInfo.query
    if keyword:
        query = query.filter(FaceInfo.person_name.contains(keyword))
    if person_type:
        query = query.filter_by(person_type=person_type)
    if status:
        query = query.filter_by(status=status)

    if get_jwt().get('role') != 'admin':
        query = query.filter_by(owner_id=int(get_jwt_identity()))

    query = query.order_by(FaceInfo.created_at.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return success_response(data={
        'items': [f.to_dict() for f in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page
    })


@face_bp.route('/add', methods=['POST'])
@admin_required
@with_write_lock
def add_face():
    """新增人脸信息"""
    data = request.get_json()
    person_type = data.get('person_type', '')
    person_name = data.get('person_name', '')
    face_image_base64 = data.get('face_image', '')
    owner_id = data.get('owner_id')
    entrance_door_ids = data.get('allowed_gates', [])

    if not person_type or not person_name:
        return error_response(message='人员类型和姓名不能为空', code=400)

    if person_type not in ('owner', 'visitor', 'blacklist'):
        return error_response(message='人员类型无效', code=400)

    if person_type == 'visitor' and not owner_id:
        return error_response(message='访客类型必须关联业主ID', code=400)

    from app.models.gate import Gate
    full_allowed_gates = set()
    community_gates = Gate.query.filter_by(gate_level='community_gate').all()
    for cg in community_gates:
        full_allowed_gates.add(cg.id)
    for eid in entrance_door_ids:
        entrance = Gate.query.get(eid)
        if entrance and entrance.gate_level == 'entrance_door' and entrance.parent_gate_id:
            full_allowed_gates.add(entrance.parent_gate_id)
    computed_allowed_gates = sorted(full_allowed_gates)

    existing_count = FaceInfo.query.filter_by(person_name=person_name, person_type=person_type, status='active').count()
    if existing_count >= 3:
        return error_response(message='每人最多3张人脸图像', code=400)

    face_image_path = ''
    if face_image_base64:
        face_image_path = _save_face_image(face_image_base64, person_type, person_name)

    face = FaceInfo(
        person_type=person_type,
        person_name=person_name,
        face_image_path=face_image_path,
        owner_id=owner_id,
        auth_start_time=data.get('auth_start_time', ''),
        auth_end_time=data.get('auth_end_time', ''),
        allowed_gates=json.dumps(computed_allowed_gates, ensure_ascii=False) if computed_allowed_gates else None,
        entrance_doors=json.dumps(entrance_door_ids, ensure_ascii=False) if entrance_door_ids else None,
        status=data.get('status', 'active')
    )
    db.session.add(face)
    db.session.commit()
    log_audit(operation_type='add_face', operation_content=f'新增人脸: {person_name}({person_type})')
    return success_response(data=face.to_dict(), message='新增成功')


@face_bp.route('/<int:face_id>', methods=['PUT'])
@admin_required
@with_write_lock
def update_face(face_id):
    """更新人脸信息"""
    face = FaceInfo.query.get(face_id)
    if not face:
        return error_response(message='人脸信息不存在', code=404)

    data = request.get_json()
    if 'person_name' in data:
        face.person_name = data['person_name']
    if 'status' in data:
        face.status = data['status']
    if 'auth_start_time' in data:
        face.auth_start_time = data['auth_start_time']
    if 'auth_end_time' in data:
        face.auth_end_time = data['auth_end_time']
    if 'allowed_gates' in data:
        from app.models.gate import Gate
        entrance_door_ids = data['allowed_gates']
        full_allowed_gates = set()
        community_gates = Gate.query.filter_by(gate_level='community_gate').all()
        for cg in community_gates:
            full_allowed_gates.add(cg.id)
        for eid in entrance_door_ids:
            entrance = Gate.query.get(eid)
            if entrance and entrance.gate_level == 'entrance_door' and entrance.parent_gate_id:
                full_allowed_gates.add(entrance.parent_gate_id)
        computed = sorted(full_allowed_gates)
        face.allowed_gates = json.dumps(computed, ensure_ascii=False) if computed else None
        face.entrance_doors = json.dumps(entrance_door_ids, ensure_ascii=False) if entrance_door_ids else None

    db.session.commit()
    log_audit(operation_type='update_face', operation_content=f'更新人脸: {face_id}')
    return success_response(data=face.to_dict(), message='更新成功')


@face_bp.route('/<int:face_id>', methods=['DELETE'])
@admin_required
@with_write_lock
def delete_face(face_id):
    """删除人脸信息"""
    face = FaceInfo.query.get(face_id)
    if not face:
        return error_response(message='人脸信息不存在', code=404)

    if face.face_image_path and os.path.exists(face.face_image_path):
        try:
            os.remove(face.face_image_path)
        except Exception:
            pass

    _remove_from_registered_faces(face.person_name, face.person_type)

    db.session.delete(face)
    db.session.commit()
    log_audit(operation_type='delete_face', operation_content=f'删除人脸: {face_id}')
    return success_response(message='删除成功')


@face_bp.route('/pass', methods=['POST'])
@limiter.exempt
def submit_face_pass():
    """提交人脸识别通行请求：识别人脸、校验权限、返回通行结果"""
    data = request.get_json()
    face_image_base64 = data.get('face_image', '')
    gate_id = data.get('gate_id', '')

    if not face_image_base64:
        return error_response(message='人脸图像不能为空', code=400)

    try:
        jpeg_bytes = base64.b64decode(face_image_base64)
    except Exception:
        return error_response(message='人脸图像解码失败', code=400)

    try:
        nparr = np.frombuffer(jpeg_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return error_response(message='无效的人脸图像', code=400)
    except Exception:
        return error_response(message='人脸图像处理失败', code=400)

    try:
        recognizer = FaceRecognizer()
    except Exception as e:
        logger.error('FaceRecognizer init failed: {}'.format(str(e)))
        return error_response(message='人脸识别服务不可用', code=500)

    try:
        registered_faces = load_registered_faces()
    except Exception as e:
        logger.error('load_registered_faces failed: {}'.format(str(e)))
        registered_faces = []

    rgb_image = np.ascontiguousarray(frame[:, :, ::-1])
    faces = recognizer.detect_faces_rgb(rgb_image)
    if not faces:
        return error_response(message='未检测到人脸', code=400)

    face_rect = faces[0]
    face_descriptor = recognizer.compute_face_descriptor_rgb(rgb_image, face_rect)
    matched_name, matched_id, distance = recognizer.compare_faces(face_descriptor, registered_faces, tolerance=0.4)

    if matched_name == '陌生人':
        return error_response(message='生人：未登记人员，禁止通行', code=403)

    face_info = FaceInfo.query.get(matched_id) if matched_id > 0 else None
    if not face_info:
        return error_response(message='生人：未登记人员，禁止通行', code=403)

    if face_info.status != 'active':
        return error_response(message='该人员已停用', code=403)

    if face_info.person_type == 'blacklist':
        return error_response(message='黑名单：黑名单人员，禁止通行', code=403)

    now = datetime.utcnow()
    if face_info.auth_start_time and face_info.auth_end_time:
        try:
            start = datetime.fromisoformat(face_info.auth_start_time)
            end = datetime.fromisoformat(face_info.auth_end_time)
            if now < start or now > end:
                return error_response(message='授权过期：访客授权已过期', code=403)
        except (ValueError, TypeError):
            pass

    if gate_id and face_info.allowed_gates:
        try:
            allowed = json.loads(face_info.allowed_gates) if isinstance(face_info.allowed_gates, str) else face_info.allowed_gates
            gate_id_str = str(gate_id)
            if isinstance(allowed, list) and gate_id_str not in [str(g) for g in allowed]:
                return error_response(message='权限不足：无此门禁通行权限', code=403)
        except (json.JSONDecodeError, TypeError):
            pass

    try:
        gate_id_int = int(gate_id) if gate_id else 0
        pr = PassRecord(
            gate_id=gate_id_int,
            face_id=face_info.id,
            pass_result='pass',
            pass_time=datetime.utcnow().isoformat()
        )
        db.session.add(pr)
        db.session.commit()
    except Exception as e:
        logger.error('Failed to save pass record: %s', str(e))
        try:
            db.session.rollback()
        except Exception:
            pass

    if face_info.person_type == 'visitor' and gate_id and face_info.allowed_gates:
        try:
            allowed = json.loads(face_info.allowed_gates) if isinstance(face_info.allowed_gates, str) else face_info.allowed_gates
            if isinstance(allowed, list):
                passed_gate_ids = [r.gate_id for r in PassRecord.query.filter_by(face_id=face_info.id, pass_result='pass').all()]
                if all(gid in passed_gate_ids for gid in allowed):
                    _remove_visitor_access(face_info)
        except Exception as e:
            logger.error('Failed to check visitor pass completion: %s', str(e))

    return success_response(data={'result': 'passed', 'person_name': face_info.person_name, 'person_type': face_info.person_type, 'gate_id': gate_id}, message='通行成功')



@face_bp.route('/face-register', methods=['POST'])
@jwt_required()
@with_write_lock
def face_register():
    """人脸注册：接收base64人脸图像，调用dlib计算128维编码"""
    data = request.get_json()
    face_image_base64 = data.get('face_image', '')
    person_name = data.get('person_name', '')
    person_type = data.get('person_type', 'owner')
    entrance_door_ids = data.get('allowed_gates', [])

    if not face_image_base64 or not person_name:
        return error_response(message='人脸图像和姓名不能为空', code=400)

    from app.models.gate import Gate
    full_allowed_gates = set()
    community_gates = Gate.query.filter_by(gate_level='community_gate').all()
    for cg in community_gates:
        full_allowed_gates.add(cg.id)
    for eid in entrance_door_ids:
        entrance = Gate.query.get(eid)
        if entrance and entrance.gate_level == 'entrance_door' and entrance.parent_gate_id:
            full_allowed_gates.add(entrance.parent_gate_id)
    allowed_gates = sorted(full_allowed_gates)

    try:
        import cv2
        import numpy as np
        from core.face_recognition import FaceRecognizer, load_registered_faces
        from flask import current_app

        img_data = base64.b64decode(face_image_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        recognizer = FaceRecognizer()
        faces = recognizer.detect_faces(img)
        if len(faces) == 0:
            return error_response(message='未检测到人脸', code=400)

        face_descriptor = recognizer.compute_face_descriptor(img, faces[0])
        encoding = face_descriptor.tolist()

        faces_file = current_app.config.get('REGISTERED_FACES_FILE')
        if not faces_file:
            faces_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'registered_faces.json')

        registered = []
        if os.path.exists(faces_file):
            with open(faces_file, 'r', encoding='utf-8') as f:
                registered = json.load(f)

        duplicate_name = None
        new_descriptor_np = np.array(encoding)
        for reg in registered:
            reg_descriptor = reg.get('face_descriptor', [])
            if not reg_descriptor or len(reg_descriptor) != 128:
                continue
            distance = np.linalg.norm(new_descriptor_np - np.array(reg_descriptor))
            logger.info('Face duplicate check vs {}({}): distance={:.4f}'.format(
                reg.get('person_name', ''), reg.get('person_type', ''), distance))
            if distance < 0.6:
                duplicate_name = reg.get('person_name', '')
                break

        if not duplicate_name:
            existing_faces = FaceInfo.query.filter_by(status='active').all()
            for ef in existing_faces:
                if not ef.face_feature:
                    continue
                try:
                    ef_descriptor = json.loads(ef.face_feature)
                    if len(ef_descriptor) != 128:
                        continue
                    distance = np.linalg.norm(new_descriptor_np - np.array(ef_descriptor))
                    logger.info('Face duplicate check vs {}(db): distance={:.4f}'.format(ef.person_name, distance))
                    if distance < 0.6:
                        duplicate_name = ef.person_name
                        break
                except (json.JSONDecodeError, ValueError):
                    continue

        if duplicate_name:
            return error_response(message='该人脸已被{}使用'.format(duplicate_name), code=409)

        from datetime import datetime
        new_id = max([r.get('id', 0) for r in registered], default=0) + 1
        new_record = {
            'id': new_id,
            'person_name': person_name,
            'person_type': person_type,
            'face_descriptor': encoding,
            'registered_at': datetime.utcnow().isoformat()
        }
        registered.append(new_record)

        os.makedirs(os.path.dirname(faces_file), exist_ok=True)
        with open(faces_file, 'w', encoding='utf-8') as f:
            json.dump(registered, f, ensure_ascii=False)

        log_audit(operation_type='face_register', operation_content='人脸注册: {}({})'.format(person_name, person_type))

        face_image_path = _save_face_image(face_image_base64, person_type, person_name)
        face_record = FaceInfo(
            person_type=person_type,
            person_name=person_name,
            face_image_path=face_image_path,
            face_feature=json.dumps(encoding),
            allowed_gates=json.dumps(allowed_gates, ensure_ascii=False) if allowed_gates else None,
            entrance_doors=json.dumps(entrance_door_ids, ensure_ascii=False) if entrance_door_ids else None,
            status='active'
        )
        db.session.add(face_record)
        db.session.commit()

        return success_response(data={'person_name': person_name, 'encoding_length': len(encoding)}, message='注册成功')

    except ImportError:
        return error_response(message='dlib未安装，无法进行人脸注册', code=500)
    except Exception as e:
        logger.error('Face register error: {}'.format(str(e)))
        return error_response(message='人脸注册失败: {}'.format(str(e)), code=500)


@face_bp.route('/test', methods=['POST'])
@jwt_required()
def face_test():
    """人脸识别测试：上传图片，检测人脸并与已注册人脸比对"""
    data = request.get_json()
    face_image_base64 = data.get('face_image', '')

    if not face_image_base64:
        return error_response(message='人脸图像不能为空', code=400)

    try:
        import cv2
        import numpy as np
        from core.face_recognition import FaceRecognizer, load_registered_faces

        img_data = base64.b64decode(face_image_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return error_response(message='图像解码失败', code=400)

        recognizer = FaceRecognizer()
        faces = recognizer.detect_faces(img)

        if len(faces) == 0:
            return success_response(data={
                'detected': False,
                'face_count': 0,
                'results': []
            }, message='未检测到人脸')

        registered_faces = load_registered_faces()

        results = []
        for i, face_rect in enumerate(faces):
            x1, y1, x2, y2 = face_rect
            face_descriptor = recognizer.compute_face_descriptor(img, face_rect)
            matched_name, matched_id, distance = recognizer.compare_faces(
                face_descriptor, registered_faces, tolerance=0.4
            )
            is_stranger = matched_name == '陌生人'
            results.append({
                'face_index': i + 1,
                'rect': {'x1': int(x1), 'y1': int(y1), 'x2': int(x2), 'y2': int(y2)},
                'matched': not is_stranger,
                'person_name': matched_name if not is_stranger else '',
                'person_id': matched_id if not is_stranger else None,
                'distance': round(float(distance), 4),
                'confidence': round(max(0, 1 - float(distance) / 0.6) * 100, 1)
            })

        return success_response(data={
            'detected': True,
            'face_count': len(faces),
            'results': results
        })

    except ImportError:
        return error_response(message='dlib未安装，无法进行人脸识别', code=500)
    except Exception as e:
        logger.error('Face test error: {}'.format(str(e)))
        return error_response(message='人脸识别测试失败: {}'.format(str(e)), code=500)


def _save_face_image(face_image_base64, person_type, person_name):
    """保存人脸图像到文件"""
    try:
        img_data = base64.b64decode(face_image_base64)
        save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'face_images')
        os.makedirs(save_dir, exist_ok=True)

        filename = f'{person_type}_{person_name}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.jpg'
        filepath = os.path.join(save_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(img_data)

        return filepath
    except Exception as e:
        logger.error(f'Save face image error: {str(e)}')
        return ''


def _remove_from_registered_faces(person_name, person_type):
    """从registered_faces.json中删除匹配的人脸记录"""
    try:
        from flask import current_app
        faces_file = current_app.config.get('REGISTERED_FACES_FILE')
        if not faces_file:
            faces_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'registered_faces.json')
        if not os.path.exists(faces_file):
            return
        with open(faces_file, 'r', encoding='utf-8') as f:
            registered = json.load(f)
        original_len = len(registered)
        registered = [r for r in registered if not (r.get('person_name') == person_name and r.get('person_type') == person_type)]
        if len(registered) < original_len:
            with open(faces_file, 'w', encoding='utf-8') as f:
                json.dump(registered, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f'Remove registered face error: {str(e)}')
