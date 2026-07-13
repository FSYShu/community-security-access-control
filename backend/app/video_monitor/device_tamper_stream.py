"""RTMP stream wrapper that annotates and records camera tamper events."""

import logging
import os
import threading
import time
from datetime import datetime

import cv2
import numpy as np

from app import db
from app.models.alarm import AlarmEvent
from core.device_tamper import BLOCKED, BLURRED, IMPACT, MOVED, NORMAL, DeviceTamperDetector

logger = logging.getLogger(__name__)

_alarm_lock = threading.Lock()
_active_alarm_states = set()

STATUS_LABELS = {
    NORMAL: ('NORMAL', (80, 200, 80)),
    BLOCKED: ('LENS BLOCKED', (0, 0, 255)),
    BLURRED: ('IMAGE BLURRED', (0, 165, 255)),
    MOVED: ('CAMERA MOVED', (0, 0, 255)),
    IMPACT: ('CAMERA IMPACT', (0, 0, 255)),
    'open_flame': ('OPEN FLAME', (0, 0, 255)),
    'smoke': ('SMOKE DETECTED', (0, 165, 255)),
    'stream_offline': ('STREAM OFFLINE', (0, 0, 255)),
}


def generate_frames_from_background_monitor(monitor, gate_id, max_width=640,
                                            offline_timeout=5):
    placeholder_size = (max_width, int(max_width * 9 / 16))
    while True:
        snapshot = monitor.get_snapshot(gate_id)
        if (
            snapshot is None
            or snapshot['frame'] is None
            or time.monotonic() - snapshot['updated_at'] > offline_timeout
        ):
            output = _placeholder('STREAM OFFLINE', placeholder_size)
            status = 'stream_offline'
            metrics = {}
        else:
            output = snapshot['frame']
            status = snapshot['status']
            metrics = snapshot['metrics']
            if output.shape[1] > max_width:
                scale = max_width / output.shape[1]
                output = cv2.resize(output, (max_width, int(output.shape[0] * scale)))

        _draw_status(output, status, metrics)
        encoded, buffer = cv2.imencode('.jpg', output, [int(cv2.IMWRITE_JPEG_QUALITY), 45])
        if encoded:
            yield _multipart(buffer.tobytes())
        time.sleep(0.05)


def generate_frames_with_tamper_detection(app, stream_url, gate_id, max_width=640,
                                           confirm_frames=3, recovery_frames=4,
                                           blocked_confirm_frames=8,
                                           offline_timeout=5, open_timeout=20,
                                           alarm_cooldown=60, check_interval=0.1,
                                           impact_confirm_frames=1,
                                           impact_motion_threshold=6.0,
                                           impact_coherence_threshold=0.6,
                                           impact_reversal_cosine=-0.35,
                                           impact_window_frames=6,
                                           impact_blur_drop_threshold=0.35,
                                           impact_min_tracked_points=20,
                                           impact_scene_change_limit=0.60,
                                           impact_sudden_multiplier=1.25):
    placeholder_size = (max_width, int(max_width * 9 / 16))
    cap = None
    first_frame = None

    # Keep the MJPEG response alive so the page recovers when OBS starts later.
    while cap is None:
        cap = _open_capture(stream_url, timeout=open_timeout)
        if cap is not None:
            ok, first_frame = cap.read()
            if not ok or first_frame is None:
                cap.release()
                cap = None

        if cap is not None:
            break

        frame = _placeholder('STREAM OFFLINE', placeholder_size)
        _clear_alarm_states(gate_id, {'stream_offline'})
        _record_alarm(app, gate_id, 'stream_offline', frame, {}, alarm_cooldown)
        for _ in range(20):
            yield _multipart(frame)
            time.sleep(0.1)

    latest = {'frame': first_frame, 'updated_at': time.monotonic(), 'alive': True}
    lock = threading.Lock()

    def reader():
        while latest['alive']:
            try:
                ok, frame = cap.read()
            except cv2.error as exc:
                logger.warning('RTMP reader stopped for %s: %s', stream_url, exc)
                latest['alive'] = False
                break
            if not ok:
                time.sleep(0.05)
                continue
            with lock:
                latest['frame'] = frame
                latest['updated_at'] = time.monotonic()

    threading.Thread(target=reader, daemon=True).start()
    detector = DeviceTamperDetector(
        confirm_frames=confirm_frames,
        blocked_confirm_frames=blocked_confirm_frames,
        recovery_frames=recovery_frames,
        impact_confirm_frames=impact_confirm_frames,
        impact_motion_threshold=impact_motion_threshold,
        impact_coherence_threshold=impact_coherence_threshold,
        impact_reversal_cosine=impact_reversal_cosine,
        impact_window_frames=impact_window_frames,
        impact_blur_drop_threshold=impact_blur_drop_threshold,
        impact_min_tracked_points=impact_min_tracked_points,
        impact_scene_change_limit=impact_scene_change_limit,
        impact_sudden_multiplier=impact_sudden_multiplier,
    )
    last_check = 0.0
    result_status = NORMAL
    result_metrics = {}

    try:
        while latest['alive']:
            with lock:
                frame = latest['frame'].copy()
                updated_at = latest['updated_at']

            if time.monotonic() - updated_at > offline_timeout:
                result_status = 'stream_offline'
                result_metrics = {}
                _clear_alarm_states(gate_id, {'stream_offline'})
                _record_alarm(app, gate_id, result_status, frame, result_metrics, alarm_cooldown)
            elif time.monotonic() - last_check >= check_interval:
                result = detector.analyze(frame)
                result_status = result.status
                result_metrics = result.metrics
                last_check = time.monotonic()
                active_states = {result_status} if result_status != NORMAL else set()
                _clear_alarm_states(gate_id, active_states)
                if result.event:
                    _record_alarm(app, gate_id, result_status, frame, result_metrics, alarm_cooldown)

            output = frame
            if output.shape[1] > max_width:
                scale = max_width / output.shape[1]
                output = cv2.resize(output, (max_width, int(output.shape[0] * scale)))
            _draw_status(output, result_status, result_metrics)
            encoded, buffer = cv2.imencode('.jpg', output, [int(cv2.IMWRITE_JPEG_QUALITY), 45])
            if encoded:
                yield _multipart(buffer.tobytes())
            time.sleep(0.03)
    finally:
        latest['alive'] = False
        cap.release()


def _open_capture(stream_url, timeout):
    result = {'cap': None}
    finished = threading.Event()
    abandoned = threading.Event()

    def try_open():
        cap = None
        try:
            candidate = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
            if candidate.isOpened():
                cap = candidate
            else:
                candidate.release()
        except Exception:
            logger.exception('Failed to open RTMP stream: %s', stream_url)

        if abandoned.is_set():
            if cap is not None:
                cap.release()
        else:
            result['cap'] = cap
        finished.set()

    threading.Thread(target=try_open, daemon=True).start()
    if not finished.wait(timeout=timeout):
        abandoned.set()
        logger.warning('Timed out opening RTMP stream: %s', stream_url)
        return None
    return result['cap']


def _record_alarm(app, gate_id, alarm_type, frame, metrics, cooldown):
    key = (gate_id, alarm_type)
    with _alarm_lock:
        if key in _active_alarm_states:
            return
        _active_alarm_states.add(key)

    descriptions = {
        BLOCKED: '门禁摄像头疑似被遮挡或画面异常变暗',
        BLURRED: '门禁摄像头画面持续严重模糊',
        MOVED: '门禁摄像头视角疑似发生改变或设备被移动',
        IMPACT: '门禁摄像头疑似受到拍打或冲击，画面出现短时剧烈震动',
        'open_flame': '门禁区域疑似出现明火',
        'smoke': '门禁区域疑似出现烟雾',
        'stream_offline': '门禁视频流中断，设备可能断电或网络异常',
    }
    levels = {
        BLOCKED: 'critical',
        MOVED: 'critical',
        IMPACT: 'critical',
        'open_flame': 'critical',
        'smoke': 'critical',
        'stream_offline': 'critical',
        BLURRED: 'warning',
    }
    image_path = _save_capture(app, gate_id, alarm_type, frame)
    try:
        with app.app_context():
            db.session.add(AlarmEvent(
                alarm_type=alarm_type,
                alarm_level=levels.get(alarm_type, 'warning'),
                source_id=gate_id,
                source_type='gate',
                alarm_description=descriptions.get(alarm_type, alarm_type),
                capture_image_path=image_path,
            ))
            db.session.commit()
    except Exception:
        logger.exception('Failed to persist tamper alarm for gate %s', gate_id)
        with _alarm_lock:
            _active_alarm_states.discard(key)


def _clear_alarm_states(gate_id, active_types):
    """Allow a new alarm only after its previous state has recovered."""
    with _alarm_lock:
        for key in list(_active_alarm_states):
            if key[0] == gate_id and key[1] not in active_types:
                _active_alarm_states.remove(key)


def _save_capture(app, gate_id, alarm_type, frame):
    directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'alarm_captures')
    os.makedirs(directory, exist_ok=True)
    filename = '{}_gate_{}_{}.jpg'.format(
        datetime.utcnow().strftime('%Y%m%d_%H%M%S'), gate_id, alarm_type
    )
    path = os.path.join(directory, filename)
    encoded, buffer = cv2.imencode('.jpg', frame)
    if encoded:
        with open(path, 'wb') as target:
            target.write(buffer.tobytes())
    return path


def _draw_status(frame, status, metrics):
    label, color = STATUS_LABELS.get(status, (status.upper(), (0, 0, 255)))
    cv2.rectangle(frame, (10, 10), (250, 45), (20, 20, 20), -1)
    cv2.putText(frame, label, (20, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
    if metrics:
        detail = 'bright={:.0f} sharp={:.0f} motion={:.1f}'.format(
            metrics['brightness'], metrics['sharpness'], metrics.get('global_motion', 0.0)
        )
        cv2.putText(frame, detail, (10, frame.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)


def _placeholder(text, resolution):
    frame = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
    cv2.putText(frame, text, (20, resolution[1] // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return frame


def _multipart(frame_bytes):
    if isinstance(frame_bytes, np.ndarray):
        encoded, buffer = cv2.imencode('.jpg', frame_bytes)
        frame_bytes = buffer.tobytes() if encoded else b''
    return b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
