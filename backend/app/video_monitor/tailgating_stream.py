"""Independent real-time tailgating detection stream."""

import logging
import os
import shutil
import threading
import time
import ctypes
import tempfile
from datetime import datetime, timezone, timedelta

import cv2

from app import db
from app.models.alarm import AlarmEvent
from core.alarm_dedup import alarm_write_transaction, has_pending_alarm
from core.tailgating_detector import MobileNetPersonDetector, TailgatingDetector

from .dangerous_behavior_sse import _open_capture, _placeholder

logger = logging.getLogger(__name__)

_alarm_lock = threading.Lock()
_last_alarm_at = {}


def generate_frames_with_tailgating(
        app, stream_url, gate_id, prototxt_path, model_path,
        max_width=640, confidence=0.35, detection_interval=0.15,
        line_ratio=0.62, crossing_window=2.5,
        max_horizontal_gap_ratio=0.28, authorized_entries=1,
        direction='both', status_hold_seconds=3.0, alarm_cooldown=60,
        open_timeout=20):
    """Analyze one gate stream without touching other detector state."""
    if not os.path.isfile(prototxt_path) or not os.path.isfile(model_path):
        logger.error('Tailgating model files are missing: %s, %s', prototxt_path, model_path)
        frame = _placeholder('TAILGATING MODEL MISSING', (max_width, int(max_width * 9 / 16)))
        yield _multipart(frame)
        return

    person_detector = MobileNetPersonDetector(
        _opencv_compatible_path(prototxt_path),
        _opencv_compatible_path(model_path),
        confidence=confidence,
    )
    tailgating_detector = TailgatingDetector(
        line_ratio=line_ratio,
        crossing_window=crossing_window,
        max_horizontal_gap_ratio=max_horizontal_gap_ratio,
        authorized_entries=authorized_entries,
        direction=direction,
    )
    cap = _open_capture(stream_url, timeout=open_timeout)
    if cap is None:
        frame = _placeholder('STREAM OFFLINE', (max_width, int(max_width * 9 / 16)))
        yield _multipart(frame)
        return
    last_detection_at = 0.0
    last_event_at = 0.0
    tracks = {}
    crossing_count = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break

            now = time.monotonic()
            if now - last_detection_at >= detection_interval:
                boxes = person_detector.detect(frame)
                result = tailgating_detector.update(boxes, frame.shape, now)
                tracks = result.tracks
                crossing_count = result.crossing_count
                last_detection_at = now
                if result.event:
                    if now - last_event_at > crossing_window:
                        last_event_at = now
                        _record_tailgating_alarm(
                            app,
                            gate_id,
                            frame,
                            result.track_ids,
                            crossing_count,
                            alarm_cooldown,
                        )

            output = frame.copy()
            if output.shape[1] > max_width:
                scale = max_width / output.shape[1]
                output = cv2.resize(
                    output,
                    (max_width, int(output.shape[0] * scale)),
                    interpolation=cv2.INTER_AREA,
                )
            else:
                scale = 1.0

            _draw_tailgating_overlay(
                output,
                tracks,
                line_ratio,
                scale,
                crossing_count,
                now - last_event_at <= status_hold_seconds,
            )
            encoded, buffer = cv2.imencode(
                '.jpg', output, [int(cv2.IMWRITE_JPEG_QUALITY), 50]
            )
            if encoded:
                yield _multipart(buffer.tobytes())
            time.sleep(0.02)
    except GeneratorExit:
        return
    except Exception:
        logger.exception('Tailgating stream failed for gate %s', gate_id)
    finally:
        cap.release()


def _opencv_compatible_path(path):
    """OpenCV's Caffe reader on Windows cannot open non-ASCII paths."""
    if os.name != 'nt' or path.isascii():
        return path
    buffer = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetShortPathNameW(
        str(path), buffer, len(buffer)
    )
    short_path = buffer.value if length else path
    if short_path.isascii():
        return short_path

    cache_dir = os.path.join(tempfile.gettempdir(), 'community_security_models')
    os.makedirs(cache_dir, exist_ok=True)
    cached_path = os.path.join(cache_dir, os.path.basename(path))
    if (
        not os.path.isfile(cached_path)
        or os.path.getsize(cached_path) != os.path.getsize(path)
    ):
        shutil.copy2(path, cached_path)
    return cached_path


def _draw_tailgating_overlay(frame, tracks, line_ratio, scale,
                              crossing_count, event_active):
    height, width = frame.shape[:2]
    line_y = int(height * line_ratio)
    cv2.line(frame, (0, line_y), (width, line_y), (0, 220, 255), 2)

    for track_id, track in tracks.items():
        if track['missing']:
            continue
        x1, y1, x2, y2 = track['box'][:4]
        x1, y1, x2, y2 = [int(value * scale) for value in (x1, y1, x2, y2)]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (70, 220, 70), 2)
        cv2.putText(
            frame,
            'ID {}'.format(track_id),
            (x1, max(20, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (70, 220, 70),
            2,
        )

    label = 'TAILGATING' if event_active else 'TAILGATING MONITOR'
    color = (0, 0, 255) if event_active else (70, 220, 70)
    cv2.rectangle(frame, (10, 10), (300, 48), (20, 20, 20), -1)
    cv2.putText(frame, label, (20, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
    cv2.putText(
        frame,
        'recent crossings: {}'.format(crossing_count),
        (10, height - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        color,
        1,
    )


def _record_tailgating_alarm(app, gate_id, frame, track_ids,
                              crossing_count, cooldown):
    now = time.monotonic()
    with _alarm_lock:
        if now - _last_alarm_at.get(gate_id, 0.0) < cooldown:
            return
        _last_alarm_at[gate_id] = now

    description = '疑似陌生人贴身尾随，短时间内有 {} 人通过门禁'.format(crossing_count)
    try:
        with app.app_context():
            with alarm_write_transaction():
                if has_pending_alarm(gate_id, 'tailgating'):
                    return
                image_path = _save_capture(app, gate_id, frame)
                db.session.add(AlarmEvent(
                    alarm_type='tailgating',
                    alarm_level='critical',
                    source_id=gate_id,
                    source_type='gate',
                    alarm_description=description,
                    capture_image_path=image_path,
                    handle_remark='track_ids={}'.format(','.join(map(str, track_ids))),
                ))
                db.session.commit()
    except Exception:
        logger.exception('Failed to persist tailgating alarm for gate %s', gate_id)
        with app.app_context():
            db.session.rollback()
        with _alarm_lock:
            _last_alarm_at.pop(gate_id, None)


def _save_capture(app, gate_id, frame):
    directory = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'data',
        'alarm_captures',
    )
    os.makedirs(directory, exist_ok=True)
    filename = '{}_gate_{}_tailgating.jpg'.format(
        datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S'), gate_id
    )
    path = os.path.join(directory, filename)
    encoded, buffer = cv2.imencode('.jpg', frame)
    if encoded:
        with open(path, 'wb') as target:
            target.write(buffer.tobytes())
    return path


def _multipart(frame):
    if not isinstance(frame, bytes):
        encoded, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes() if encoded else b''
    return b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
