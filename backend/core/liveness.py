"""
活体检测模块
1. 主动检测（人脸测试）：随机动作挑战（眨眼/转头/张嘴），3-4次机会
2. 被动检测（门禁通行）：分析表情区域（眼/嘴）变化 vs 整体移动，检测照片/视频欺骗
3. 检测到疑似欺骗时自动报警到告警中心
"""
import logging
import math
import threading
import time
import uuid

import cv2
import numpy as np

from core.face_recognition import FaceRecognizer

logger = logging.getLogger(__name__)

CHALLENGE_TYPES = ['blink', 'turn_head', 'open_mouth']

EAR_THRESHOLD = 0.19
EAR_CONSEC_FRAMES = 1
CHALLENGE_EAR_THRESHOLD = 0.19
CHALLENGE_EAR_CONSEC_FRAMES = 1

MOUTH_OPEN_RATIO_THRESHOLD = 0.5

HEAD_TURN_RATIO_THRESHOLD = 0.25

CHALLENGE_TIMEOUT = 10
CHALLENGE_MAX_ATTEMPTS = 4

PASSIVE_FRAME_COUNT = 5
PASSIVE_EXPRESSION_VARIANCE_MIN = 0.00005

_spoof_alarm_cooldown = 60
_last_spoof_alarm_time = {}
_spoof_alarm_lock = threading.Lock()

_active_challenges = {}
_challenge_lock = threading.Lock()

_passive_sessions = {}
_passive_lock = threading.Lock()


def _get_landmarks(rgb_image, face_rect):
    recognizer = FaceRecognizer()
    if isinstance(face_rect, tuple):
        import dlib
        rect = dlib.rectangle(face_rect[0], face_rect[1], face_rect[2], face_rect[3])
    else:
        rect = face_rect
    with recognizer._dlib_lock:
        shape = recognizer.sp(rgb_image, rect)
    points = [(shape.part(i).x, shape.part(i).y) for i in range(68)]
    return points


def _eye_aspect_ratio(eye_points):
    v1 = math.dist(eye_points[1], eye_points[5])
    v2 = math.dist(eye_points[2], eye_points[4])
    h = math.dist(eye_points[0], eye_points[3])
    if h == 0:
        return 0.0
    return (v1 + v2) / (2.0 * h)


def _compute_ear(landmarks):
    left_eye = [landmarks[i] for i in range(36, 42)]
    right_eye = [landmarks[i] for i in range(42, 48)]
    left_ear = _eye_aspect_ratio(left_eye)
    right_ear = _eye_aspect_ratio(right_eye)
    return (left_ear + right_ear) / 2.0


def _compute_mouth_open_ratio(landmarks):
    upper = landmarks[13]
    lower = landmarks[19]
    left = landmarks[48]
    right = landmarks[54]
    mouth_open = math.dist(upper, lower)
    mouth_width = math.dist(left, right)
    if mouth_width == 0:
        return 0.0
    return mouth_open / mouth_width


def _compute_head_turn_ratio(landmarks):
    nose = landmarks[30]
    left_jaw = landmarks[2]
    right_jaw = landmarks[14]
    left_dist = math.dist(nose, left_jaw)
    right_dist = math.dist(nose, right_jaw)
    total = left_dist + right_dist
    if total == 0:
        return 0.0
    return abs(left_dist - right_dist) / total


def _extract_expression_points(landmarks):
    return [landmarks[i] for i in range(36, 48)] + [landmarks[i] for i in range(48, 68)]


def _extract_pose_points(landmarks):
    return [landmarks[i] for i in range(0, 17)] + [landmarks[30]] + [landmarks[33]]


def _compute_expression_features(landmarks):
    """提取表情相关的相对特征（不受刚性移动影响）"""
    ear = _compute_ear(landmarks)
    mouth_ratio = _compute_mouth_open_ratio(landmarks)
    left_eyebrow_eye_dist = math.dist(landmarks[19], landmarks[37]) + math.dist(landmarks[24], landmarks[43])
    face_height = math.dist(landmarks[8], landmarks[27])
    brow_ratio = left_eyebrow_eye_dist / face_height if face_height > 0 else 0
    left_eye_width = math.dist(landmarks[36], landmarks[39])
    right_eye_width = math.dist(landmarks[42], landmarks[45])
    face_width = math.dist(landmarks[0], landmarks[16])
    eye_width_ratio = (left_eye_width + right_eye_width) / face_width if face_width > 0 else 0
    nose_to_mouth = math.dist(landmarks[33], landmarks[51])
    chin_to_nose = math.dist(landmarks[8], landmarks[33])
    nose_mouth_ratio = nose_to_mouth / chin_to_nose if chin_to_nose > 0 else 0
    return [ear, mouth_ratio, brow_ratio, eye_width_ratio, nose_mouth_ratio]


def _compute_point_variance(points_list):
    if len(points_list) < 2:
        return float('inf')
    arr = np.array(points_list, dtype=np.float64)
    return np.var(arr, axis=0).mean()


def _create_spoof_alarm(source_id, description):
    now = time.time()
    alarm_key = str(source_id) if source_id else 'unknown'
    with _spoof_alarm_lock:
        if alarm_key in _last_spoof_alarm_time:
            if now - _last_spoof_alarm_time[alarm_key] < _spoof_alarm_cooldown:
                return
        _last_spoof_alarm_time[alarm_key] = now
    try:
        from app import db
        from app.models.alarm import AlarmEvent
        from datetime import datetime
        alarm = AlarmEvent(
            alarm_type='face_spoof_detected',
            alarm_level='high',
            source_id=source_id or 0,
            source_type='face_liveness',
            alarm_description=description,
            handle_status='pending',
            alarm_time=datetime.utcnow().isoformat()
        )
        db.session.add(alarm)
        db.session.commit()
        logger.info('Spoof alarm created: {}'.format(description))
    except Exception as e:
        logger.error('Failed to create spoof alarm: {}'.format(str(e)))
        try:
            from app import db
            db.session.rollback()
        except Exception:
            pass


def create_challenge():
    challenge_id = str(uuid.uuid4())
    import random
    action = random.choice(CHALLENGE_TYPES)
    challenge = {
        'id': challenge_id,
        'action': action,
        'created_at': time.time(),
        'attempts': 0,
        'blink_count': 0,
        'ear_below_threshold_count': 0,
        'max_mouth_ratio': 0.0,
        'max_head_turn_ratio': 0.0,
        'verified': False,
        'failed': False,
    }
    with _challenge_lock:
        _active_challenges[challenge_id] = challenge
    action_labels = {
        'blink': '请眨眼',
        'turn_head': '请转头',
        'open_mouth': '请张嘴',
    }
    return {
        'challenge_id': challenge_id,
        'action': action,
        'action_label': action_labels.get(action, action),
        'timeout': CHALLENGE_TIMEOUT,
        'max_attempts': CHALLENGE_MAX_ATTEMPTS,
    }


def _cleanup_expired_challenges():
    now = time.time()
    expired = []
    with _challenge_lock:
        for cid, ch in _active_challenges.items():
            if now - ch['created_at'] > CHALLENGE_TIMEOUT + 10:
                expired.append(cid)
        for cid in expired:
            del _active_challenges[cid]


def verify_challenge_frame(challenge_id, image_b64):
    _cleanup_expired_challenges()

    with _challenge_lock:
        challenge = _active_challenges.get(challenge_id)
    if not challenge:
        return {'success': False, 'error': '无效或已过期的挑战'}

    if challenge.get('failed') or challenge.get('verified'):
        return {'success': challenge.get('verified', False), 'action': challenge['action'],
                'error': '' if challenge.get('verified') else '挑战已失败'}

    if time.time() - challenge['created_at'] > CHALLENGE_TIMEOUT:
        challenge['failed'] = True
        _create_spoof_alarm(0, '人脸测试检测到疑似照片或视频欺骗')
        return {'success': False, 'error': '挑战已超时', 'action': challenge['action']}

    import base64
    try:
        img_data = base64.b64decode(image_b64)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return {'success': False, 'error': '图像解码失败'}
    except Exception as e:
        return {'success': False, 'error': '图像解码异常: {}'.format(str(e))}

    recognizer = FaceRecognizer()
    rgb_image = np.ascontiguousarray(frame[:, :, ::-1])
    faces = recognizer.detect_faces_rgb(rgb_image)
    if not faces:
        return {'success': False, 'error': '未检测到人脸', 'action': challenge['action']}

    face_rect = faces[0]
    try:
        landmarks = _get_landmarks(rgb_image, face_rect)
    except Exception as e:
        logger.error('Landmark detection failed: {}'.format(str(e)))
        return {'success': False, 'error': '关键点检测失败', 'action': challenge['action']}

    challenge['attempts'] += 1
    action = challenge['action']

    if action == 'blink':
        ear = _compute_ear(landmarks)
        if ear < CHALLENGE_EAR_THRESHOLD:
            challenge['ear_below_threshold_count'] += 1
        else:
            if challenge['ear_below_threshold_count'] >= CHALLENGE_EAR_CONSEC_FRAMES:
                challenge['blink_count'] += 1
            challenge['ear_below_threshold_count'] = 0

        if challenge['blink_count'] >= 1:
            challenge['verified'] = True
            return {'success': True, 'action': 'blink', 'detail': '检测到眨眼'}

        if challenge['attempts'] >= CHALLENGE_MAX_ATTEMPTS:
            challenge['failed'] = True
            _create_spoof_alarm(0, '人脸测试检测到疑似照片或视频欺骗')
            return {'success': False, 'error': '尝试次数已用完', 'action': 'blink'}

        return {
            'success': False,
            'action': 'blink',
            'progress': challenge['blink_count'],
            'required': 1,
            'ear': round(ear, 3),
            'attempts_left': CHALLENGE_MAX_ATTEMPTS - challenge['attempts'],
        }

    elif action == 'open_mouth':
        ratio = _compute_mouth_open_ratio(landmarks)
        challenge['max_mouth_ratio'] = max(challenge['max_mouth_ratio'], ratio)
        if challenge['max_mouth_ratio'] >= MOUTH_OPEN_RATIO_THRESHOLD:
            challenge['verified'] = True
            return {'success': True, 'action': 'open_mouth', 'detail': '检测到张嘴'}

        if challenge['attempts'] >= CHALLENGE_MAX_ATTEMPTS:
            challenge['failed'] = True
            _create_spoof_alarm(0, '人脸测试检测到疑似照片或视频欺骗')
            return {'success': False, 'error': '尝试次数已用完', 'action': 'open_mouth'}

        return {
            'success': False,
            'action': 'open_mouth',
            'progress': round(challenge['max_mouth_ratio'], 3),
            'required': MOUTH_OPEN_RATIO_THRESHOLD,
            'attempts_left': CHALLENGE_MAX_ATTEMPTS - challenge['attempts'],
        }

    elif action == 'turn_head':
        ratio = _compute_head_turn_ratio(landmarks)
        challenge['max_head_turn_ratio'] = max(challenge['max_head_turn_ratio'], ratio)
        if challenge['max_head_turn_ratio'] >= HEAD_TURN_RATIO_THRESHOLD:
            challenge['verified'] = True
            return {'success': True, 'action': 'turn_head', 'detail': '检测到转头'}

        if challenge['attempts'] >= CHALLENGE_MAX_ATTEMPTS:
            challenge['failed'] = True
            _create_spoof_alarm(0, '人脸测试检测到疑似照片或视频欺骗')
            return {'success': False, 'error': '尝试次数已用完', 'action': 'turn_head'}

        return {
            'success': False,
            'action': 'turn_head',
            'progress': round(challenge['max_head_turn_ratio'], 3),
            'required': HEAD_TURN_RATIO_THRESHOLD,
            'attempts_left': CHALLENGE_MAX_ATTEMPTS - challenge['attempts'],
        }

    return {'success': False, 'error': '未知动作类型'}


def is_challenge_verified(challenge_id):
    with _challenge_lock:
        challenge = _active_challenges.get(challenge_id)
    if not challenge:
        return False
    return challenge.get('verified', False)


def remove_challenge(challenge_id):
    with _challenge_lock:
        _active_challenges.pop(challenge_id, None)


def passive_liveness_check(image_b64, gate_id=None):
    """
    被动活体检测（门禁通行用）
    核心逻辑：区分"整体移动"和"表情变化"
    - 真人：表情区域（眼/嘴）会有自然微动，且与整体移动不同步
    - 手拿照片：整体移动但表情区域完全不变（刚性移动）
    - 视频回放：可能有表情变化，但与整体移动完全同步（缩放/平移一致）
    """
    import base64
    try:
        img_data = base64.b64decode(image_b64)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return True, '图像解码失败，跳过活体检测'
    except Exception as e:
        return True, '图像解码异常，跳过活体检测'

    recognizer = FaceRecognizer()
    rgb_image = np.ascontiguousarray(frame[:, :, ::-1])
    faces = recognizer.detect_faces_rgb(rgb_image)
    if not faces:
        return True, '未检测到人脸，跳过活体检测'

    face_rect = faces[0]
    try:
        landmarks = _get_landmarks(rgb_image, face_rect)
    except Exception as e:
        logger.error('Passive liveness landmark failed: {}'.format(str(e)))
        return True, '关键点检测失败，跳过活体检测'

    expression_pts = _extract_expression_points(landmarks)
    pose_pts = _extract_pose_points(landmarks)

    session_key = str(gate_id) if gate_id else 'default'

    with _passive_lock:
        if session_key not in _passive_sessions:
            _passive_sessions[session_key] = {
                'expression_history': [],
                'pose_history': [],
                'created_at': time.time(),
            }
        session = _passive_sessions[session_key]

        if time.time() - session['created_at'] > 30:
            session['expression_history'] = []
            session['pose_history'] = []
            session['created_at'] = time.time()

        expr_flat = []
        for x, y in expression_pts:
            expr_flat.extend([x, y])
        pose_flat = []
        for x, y in pose_pts:
            pose_flat.extend([x, y])

        session['expression_history'].append(expr_flat)
        session['pose_history'].append(pose_flat)

        if len(session['expression_history']) > PASSIVE_FRAME_COUNT:
            session['expression_history'] = session['expression_history'][-PASSIVE_FRAME_COUNT:]
        if len(session['pose_history']) > PASSIVE_FRAME_COUNT:
            session['pose_history'] = session['pose_history'][-PASSIVE_FRAME_COUNT:]

        expression_history = list(session['expression_history'])
        pose_history = list(session['pose_history'])

    if len(expression_history) < PASSIVE_FRAME_COUNT:
        return True, '采集帧数不足，暂时通过'

    expr_var = _compute_point_variance(expression_history)
    pose_var = _compute_point_variance(pose_history)

    logger.info('Passive liveness gate={} frames={} expr_var={:.6f} pose_var={:.6f}'.format(
        session_key, len(expression_history), expr_var, pose_var))

    if pose_var < 0.0001:
        return True, '画面几乎无移动，暂时通过'

    if expr_var < PASSIVE_EXPRESSION_VARIANCE_MIN:
        desc = '门禁[{}]检测到疑似照片欺骗(表情区域无变化 expr_var={:.6f}<{:.6f}, pose_var={:.6f})'.format(
            session_key, expr_var, PASSIVE_EXPRESSION_VARIANCE_MIN, pose_var)
        logger.warning(desc)
        _create_spoof_alarm(gate_id, desc)
        with _passive_lock:
            if session_key in _passive_sessions:
                _passive_sessions[session_key]['expression_history'] = []
                _passive_sessions[session_key]['pose_history'] = []
        return False, '疑似照片欺骗，已触发告警'

    expr_to_pose_ratio = expr_var / pose_var if pose_var > 0 else 0
    if expr_to_pose_ratio < 0.01:
        desc = '门禁[{}]检测到疑似视频回放欺骗(表情变化与整体移动完全同步 ratio={:.4f})'.format(
            session_key, expr_to_pose_ratio)
        logger.warning(desc)
        _create_spoof_alarm(gate_id, desc)
        with _passive_lock:
            if session_key in _passive_sessions:
                _passive_sessions[session_key]['expression_history'] = []
                _passive_sessions[session_key]['pose_history'] = []
        return False, '疑似视频回放欺骗，已触发告警'

    with _passive_lock:
        if session_key in _passive_sessions:
            _passive_sessions[session_key]['expression_history'] = []
            _passive_sessions[session_key]['pose_history'] = []

    return True, '活体检测通过'


def passive_liveness_check_frames(frames_b64, gate_id=None):
    """
    被动活体检测 - 多帧版本
    前端连续截5帧一起提交，后端分析表情相对特征变化
    照片欺骗：所有相对特征（EAR、嘴巴开合比等）在多帧中完全不变
    真人：相对特征会有自然微动
    """
    import base64

    features_history = []

    recognizer = FaceRecognizer()

    for idx, image_b64 in enumerate(frames_b64):
        try:
            img_data = base64.b64decode(image_b64)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue
        except Exception:
            continue

        rgb_image = np.ascontiguousarray(frame[:, :, ::-1])
        faces = recognizer.detect_faces_rgb(rgb_image)
        if not faces:
            continue

        face_rect = faces[0]
        try:
            landmarks = _get_landmarks(rgb_image, face_rect)
        except Exception:
            continue

        features = _compute_expression_features(landmarks)
        features_history.append(features)

    session_key = str(gate_id) if gate_id else 'default'

    logger.info('Passive liveness(multi-frame) gate={} valid_frames={}/{}'.format(
        session_key, len(features_history), len(frames_b64)))

    if len(features_history) < 3:
        return True, '有效帧数不足，暂时通过'

    arr = np.array(features_history, dtype=np.float64)
    feature_vars = np.var(arr, axis=0)
    total_var = feature_vars.mean()

    feature_names = ['EAR', 'mouth_ratio', 'brow_ratio', 'eye_width_ratio', 'nose_mouth_ratio']
    for i, name in enumerate(feature_names):
        logger.info('  feature {} var={:.8f}'.format(name, feature_vars[i]))
    logger.info('Passive liveness(multi-frame) gate={} total_feature_var={:.8f}'.format(
        session_key, total_var))

    if total_var < 1e-7:
        desc = '门禁[{}]检测到疑似照片欺骗(表情特征完全无变化 var={:.8f})'.format(
            session_key, total_var)
        logger.warning(desc)
        _create_spoof_alarm(gate_id, desc)
        return False, '疑似照片欺骗，已触发告警'

    return True, '活体检测通过'


def detect_blink_in_frames(frames_b64, gate_id=None):
    """
    静默眨眼检测（门禁通行用）
    正常人在1-2秒内肯定会自然眨眼，照片不会
    分析多帧EAR值，检测是否有"下降→回升"的眨眼模式
    """
    import base64

    ear_values = []

    recognizer = FaceRecognizer()

    for idx, image_b64 in enumerate(frames_b64):
        try:
            img_data = base64.b64decode(image_b64)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue
        except Exception:
            continue

        rgb_image = np.ascontiguousarray(frame[:, :, ::-1])
        faces = recognizer.detect_faces_rgb(rgb_image)
        if not faces:
            continue

        face_rect = faces[0]
        try:
            landmarks = _get_landmarks(rgb_image, face_rect)
        except Exception:
            continue

        ear = _compute_ear(landmarks)
        ear_values.append(ear)

    session_key = str(gate_id) if gate_id else 'default'

    logger.info('Blink detection gate={} valid_frames={}/{} ear_values={}'.format(
        session_key, len(ear_values), len(frames_b64),
        [round(e, 3) for e in ear_values]))

    if len(ear_values) < 3:
        return True, '有效帧数不足，暂时通过'

    ear_arr = np.array(ear_values)
    ear_range = float(ear_arr.max() - ear_arr.min())
    ear_std = float(ear_arr.std())

    logger.info('Blink detection gate={} ear_range={:.4f} ear_std={:.4f} ear_values={}'.format(
        session_key, ear_range, ear_std, [round(e, 3) for e in ear_values]))

    if ear_range < 0.03 and ear_std < 0.01:
        desc = '门禁[{}]检测到疑似照片或视频欺骗'.format(session_key)
        logger.warning('Blink detection failed: gate={} ear_range={:.4f} ear_std={:.4f}'.format(
            session_key, ear_range, ear_std))
        _create_spoof_alarm(gate_id, desc)
        return False, '疑似照片或视频欺骗，已触发告警'

    return True, '活体检测通过'
