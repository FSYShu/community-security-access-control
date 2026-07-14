"""
禁区入侵检测核心模块
使用运动检测+人脸检测双重策略
距离判断基于近大远小原理：人脸在画面中越大，离摄像头越近
"""
import logging
import time
import threading
import os
from datetime import datetime

import cv2
import numpy as np

from app import db
from app.models.danger_zone import DangerZone
from app.models.alarm import AlarmEvent

logger = logging.getLogger(__name__)

DETECT_WIDTH = 320
ALARM_COOLDOWN = 30
MOTION_THRESHOLD = 25
MOTION_MIN_AREA = 500
MOTION_AREA_RATIO = 0.005

REFERENCE_FACE_HEIGHT_RATIO = 0.35
REFERENCE_DISTANCE = 1.0

_gate_calib = {}
_gate_calib_lock = threading.Lock()

_face_recognizer = None
_face_rec_lock = threading.Lock()

_zone_first_seen = {}
_zone_first_seen_lock = threading.Lock()

_prev_gray = {}


def _get_face_recognizer():
    global _face_recognizer
    with _face_rec_lock:
        if _face_recognizer is None:
            try:
                from core.face_recognition import FaceRecognizer
                _face_recognizer = FaceRecognizer()
            except Exception as e:
                logger.error('FaceRecognizer init failed: {}'.format(str(e)))
                return None
        return _face_recognizer


def _update_gate_calib(gate_id, calib_distance, calib_face_ratio):
    with _gate_calib_lock:
        _gate_calib[gate_id] = {
            'calib_distance': calib_distance,
            'calib_face_ratio': calib_face_ratio,
        }


def _get_gate_calib(gate_id):
    with _gate_calib_lock:
        return _gate_calib.get(gate_id)


def estimate_distance(face_rect, frame_height, gate_id=None):
    x1, y1, x2, y2 = face_rect
    face_pixel_height = y2 - y1
    if face_pixel_height <= 0 or frame_height <= 0:
        return float('inf')
    height_ratio = face_pixel_height / frame_height
    if height_ratio <= 0:
        return float('inf')
    calib = _get_gate_calib(gate_id) if gate_id else None
    if calib and calib.get('calib_distance') and calib.get('calib_face_ratio') and calib['calib_face_ratio'] > 0:
        distance = calib['calib_distance'] * calib['calib_face_ratio'] / height_ratio
    else:
        distance = REFERENCE_DISTANCE * REFERENCE_FACE_HEIGHT_RATIO / height_ratio
    return round(distance, 2)


def _detect_faces(frame, gate_id=None):
    recognizer = _get_face_recognizer()
    if recognizer is None:
        return []
    h, w = frame.shape[:2]
    if w > DETECT_WIDTH:
        scale = DETECT_WIDTH / w
        detect_frame = cv2.resize(frame, (DETECT_WIDTH, int(h * scale)),
                                  interpolation=cv2.INTER_LINEAR)
    else:
        detect_frame = frame
        scale = 1.0

    try:
        rgb_image = np.ascontiguousarray(detect_frame[:, :, ::-1])
        faces = recognizer.detect_faces_rgb(rgb_image)
    except Exception as e:
        logger.error('Face detection error: {}'.format(str(e)))
        return []

    persons = []
    for face_rect in faces:
        if scale != 1.0:
            x1, y1, x2, y2 = face_rect
            face_rect = (int(x1 / scale), int(y1 / scale),
                         int(x2 / scale), int(y2 / scale))
        distance = estimate_distance(face_rect, frame.shape[0], gate_id)
        persons.append({
            'rect': face_rect,
            'confidence': 1.0,
            'method': 'face',
            'distance': distance
        })
    return persons


def _detect_motion(frame, zone_id):
    global _prev_gray
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if zone_id not in _prev_gray or _prev_gray[zone_id] is None:
        _prev_gray[zone_id] = gray
        return False

    prev = _prev_gray[zone_id]
    frame_delta = cv2.absdiff(prev, gray)
    thresh = cv2.threshold(frame_delta, MOTION_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = gray.shape
    frame_area = h * w
    motion_area = 0
    for contour in contours:
        if cv2.contourArea(contour) < MOTION_MIN_AREA:
            continue
        motion_area += cv2.contourArea(contour)

    _prev_gray[zone_id] = gray

    if motion_area / frame_area > MOTION_AREA_RATIO:
        return True
    return False


def _detect_persons(frame, zone_id, gate_id=None):
    face_persons = _detect_faces(frame, gate_id)
    if face_persons:
        return face_persons

    has_motion = _detect_motion(frame, zone_id)
    if has_motion:
        return [{'rect': (0, 0, frame.shape[1], frame.shape[0]), 'confidence': 0.5, 'method': 'motion', 'distance': 0.0}]

    return []


def _save_capture_image(frame, zone_id):
    try:
        data_dir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), 'data')
        alarm_dir = os.path.join(data_dir, 'alarm_captures')
        os.makedirs(alarm_dir, exist_ok=True)
        filename = 'zone_{}_{}.jpg'.format(zone_id, datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f'))
        filepath = os.path.join(alarm_dir, filename)
        cv2.imwrite(filepath, frame)
        return filepath
    except Exception as e:
        logger.error('Failed to save capture image: {}'.format(str(e)))
        return None


def _create_alarm(zone_id, zone_name, alarm_level, description, capture_path=None):
    now_str = datetime.utcnow().isoformat()
    alarm = AlarmEvent(
        alarm_type='danger_zone_intrusion',
        alarm_level=alarm_level,
        source_id=zone_id,
        source_type='danger_zone',
        alarm_description=description,
        capture_image_path=capture_path,
        handle_status='pending',
        alarm_time=now_str
    )
    db.session.add(alarm)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error('Failed to commit alarm: {}'.format(str(e)))
        return None
    logger.info('Alarm created: zone={} desc={}'.format(zone_name, description))
    return alarm


def process_frame_for_zone(zone_id, frame, gate_id=None):
    try:
        zone = DangerZone.query.get(zone_id)
    except Exception as e:
        db.session.rollback()
        logger.error('DB error querying zone {}: {}'.format(zone_id, str(e)))
        return None

    if not zone or zone.status != 'active':
        return None

    if gate_id:
        from app.models.gate import Gate
        try:
            gate = Gate.query.get(gate_id)
            if gate and gate.calib_distance and gate.calib_face_ratio:
                _update_gate_calib(gate_id, gate.calib_distance, gate.calib_face_ratio)
        except Exception:
            pass

    persons = _detect_persons(frame, zone_id, gate_id)

    now = time.time()

    if not persons:
        with _zone_first_seen_lock:
            if zone_id in _zone_first_seen:
                first_time = _zone_first_seen[zone_id].get('first_seen')
                if first_time and now - first_time > 10:
                    _zone_first_seen[zone_id] = {
                        'first_seen': None,
                        'last_alarm_time': _zone_first_seen[zone_id].get('last_alarm_time', 0)
                    }
        return None

    safety_distance = zone.safety_distance if zone.safety_distance else 2.0
    close_persons = []
    for p in persons:
        dist = p.get('distance', float('inf'))
        if dist <= safety_distance:
            close_persons.append(p)

    method = persons[0].get('method', 'unknown')
    min_distance = min(p.get('distance', float('inf')) for p in persons)
    logger.info('Zone {} detected {} person(s) via {}, min_dist={:.2f}m, safety={:.2f}m, close={}'.format(
        zone_id, len(persons), method, min_distance, safety_distance, len(close_persons)))

    if not close_persons:
        with _zone_first_seen_lock:
            if zone_id in _zone_first_seen:
                _zone_first_seen[zone_id]['first_seen'] = None
        return None

    with _zone_first_seen_lock:
        if zone_id not in _zone_first_seen:
            _zone_first_seen[zone_id] = {
                'first_seen': now,
                'last_alarm_time': 0
            }

        tracker = _zone_first_seen[zone_id]

        if tracker['first_seen'] is None:
            tracker['first_seen'] = now

        elapsed = now - tracker['first_seen']

        if elapsed < zone.stay_duration:
            logger.info('Zone {} elapsed {:.1f}s < {}s, waiting'.format(zone_id, elapsed, zone.stay_duration))
            return None

        if now - tracker['last_alarm_time'] < ALARM_COOLDOWN:
            return None

        tracker['last_alarm_time'] = now

    capture_path = _save_capture_image(frame, zone_id)
    min_close_dist = min(p.get('distance', float('inf')) for p in close_persons)
    desc = '禁区[{}]检测到{}人闯入(最近{:.1f}m<安全距离{:.1f}m)，已滞留{}秒'.format(
        zone.zone_name, len(close_persons), min_close_dist, safety_distance, int(elapsed))
    alarm = _create_alarm(zone.id, zone.zone_name, zone.alarm_level, desc, capture_path)
    return alarm


def draw_detection_overlay(frame, persons, safety_distance=None):
    for person in persons:
        x1, y1, x2, y2 = person['rect']
        dist = person.get('distance', float('inf'))
        is_close = safety_distance is not None and dist <= safety_distance
        color = (0, 0, 255) if is_close else (0, 165, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = 'INTRUSION' if is_close else 'PERSON'
        if dist < float('inf'):
            label = '{} {:.1f}m'.format(label, dist)
        cv2.putText(frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return frame
