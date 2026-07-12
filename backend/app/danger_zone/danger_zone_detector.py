"""
禁区入侵检测核心模块
使用运动检测+HOG行人检测双重策略
运动检测灵敏度高，HOG减少误报
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

_hog_detector = None
_hog_lock = threading.Lock()

_zone_first_seen = {}
_zone_first_seen_lock = threading.Lock()

_prev_gray = {}


def _get_hog_detector():
    global _hog_detector
    with _hog_lock:
        if _hog_detector is None:
            _hog_detector = cv2.HOGDescriptor()
            _hog_detector.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        return _hog_detector


def _detect_persons_hog(frame):
    hog = _get_hog_detector()
    h, w = frame.shape[:2]
    if w > DETECT_WIDTH:
        scale = DETECT_WIDTH / w
        detect_frame = cv2.resize(frame, (DETECT_WIDTH, int(h * scale)),
                                  interpolation=cv2.INTER_LINEAR)
    else:
        detect_frame = frame
        scale = 1.0

    try:
        boxes, weights = hog.detectMultiScale(
            detect_frame,
            winStride=(8, 8),
            padding=(4, 4),
            scale=1.05
        )
    except Exception as e:
        logger.error('HOG detection error: {}'.format(str(e)))
        return []

    persons = []
    for i, (x, y, bw, bh) in enumerate(boxes):
        confidence = weights[i][0] if i < len(weights) and len(weights[i]) > 0 else 0
        if confidence < 0.05:
            continue
        if scale != 1.0:
            x = int(x / scale)
            y = int(y / scale)
            bw = int(bw / scale)
            bh = int(bh / scale)
        persons.append({
            'rect': (x, y, x + bw, y + bh),
            'confidence': float(confidence),
            'method': 'hog'
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


def _detect_persons(frame, zone_id):
    hog_persons = _detect_persons_hog(frame)
    if hog_persons:
        return hog_persons

    has_motion = _detect_motion(frame, zone_id)
    if has_motion:
        return [{'rect': (0, 0, frame.shape[1], frame.shape[0]), 'confidence': 0.5, 'method': 'motion'}]

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


def process_frame_for_zone(zone_id, frame):
    try:
        zone = DangerZone.query.get(zone_id)
    except Exception as e:
        db.session.rollback()
        logger.error('DB error querying zone {}: {}'.format(zone_id, str(e)))
        return None

    if not zone or zone.status != 'active':
        return None

    persons = _detect_persons(frame, zone_id)

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

    method = persons[0].get('method', 'unknown')
    logger.info('Zone {} detected {} person(s) via {}'.format(zone_id, len(persons), method))

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
    desc = '禁区[{}]检测到{}人闯入，已滞留{}秒'.format(
        zone.zone_name, len(persons), int(elapsed))
    alarm = _create_alarm(zone.id, zone.zone_name, zone.alarm_level, desc, capture_path)
    return alarm


def draw_detection_overlay(frame, persons):
    for person in persons:
        x1, y1, x2, y2 = person['rect']
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(frame, 'INTRUSION', (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    return frame
