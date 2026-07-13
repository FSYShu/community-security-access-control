"""Unified view for independent dangerous-behavior detectors."""

import logging
import math
import os
import threading
import time

import cv2

from .device_tamper_stream import _draw_status, _multipart, _placeholder, _open_capture
from .tailgating_stream import (
    _opencv_compatible_path,
    _record_tailgating_alarm,
)
from core.tailgating_detector import MobileNetPersonDetector, TailgatingDetector

logger = logging.getLogger(__name__)


def generate_frames_with_dangerous_behavior(
        app, monitor, gate_id, prototxt_path, model_path,
        stream_url=None, max_width=640, confidence=0.35, detection_interval=0.10,
        line_ratio=0.62, crossing_window=5.0,
        max_horizontal_gap_ratio=0.28, authorized_entries=1,
        direction='both', status_hold_seconds=3.0,
        alarm_cooldown=60, offline_timeout=5, open_timeout=20):
    """Render existing device status plus an independent tailgating layer.

    When *monitor* is available and has a snapshot for *gate_id*, frames are
    read from the background tamper monitor (device-tamper + fire/smoke
    status included).  When the monitor is unavailable or has no data, the
    function falls back to pulling directly from *stream_url* via
    cv2.VideoCapture so the stream is never left showing only "STREAM
    OFFLINE".
    """
    model_available = (
        os.path.isfile(prototxt_path)
        and os.path.isfile(model_path)
    )
    detector = None
    tailgating = None
    if model_available:
        try:
            detector = MobileNetPersonDetector(
                _opencv_compatible_path(prototxt_path),
                _opencv_compatible_path(model_path),
                confidence=confidence,
            )
            tailgating = TailgatingDetector(
                line_ratio=line_ratio,
                crossing_window=crossing_window,
                max_horizontal_gap_ratio=max_horizontal_gap_ratio,
                authorized_entries=authorized_entries,
                direction=direction,
            )
        except (AttributeError, cv2.error) as exc:
            logger.warning('Tailgating model init failed, running without person detection: %s', exc)
            detector = None
            tailgating = None
    last_detection_at = 0.0
    last_event_at = -math.inf
    tracks = {}
    crossing_count = 0

    fallback_cap = None
    fallback_alive = {'flag': True}
    fallback_latest = {'frame': None, 'updated_at': 0.0}
    fallback_lock = threading.Lock()

    def _start_fallback_reader(url):
        nonlocal fallback_cap
        cap = _open_capture(url, timeout=open_timeout)
        if cap is None:
            return
        fallback_cap = cap

        def reader():
            while fallback_alive['flag']:
                try:
                    ok, frame = cap.read()
                except cv2.error:
                    break
                if not ok or frame is None:
                    time.sleep(0.05)
                    continue
                with fallback_lock:
                    fallback_latest['frame'] = frame
                    fallback_latest['updated_at'] = time.monotonic()

        threading.Thread(target=reader, daemon=True).start()

    try:
        while True:
            snapshot = monitor.get_snapshot(gate_id) if monitor else None
            now = time.monotonic()
            monitor_ok = (
                snapshot is not None
                and snapshot['frame'] is not None
                and now - snapshot['updated_at'] <= offline_timeout
            )

            if not monitor_ok and stream_url and fallback_cap is None:
                logger.info('Monitor unavailable for gate %s, starting fallback RTMP pull', gate_id)
                _start_fallback_reader(stream_url)

            if monitor_ok:
                frame = snapshot['frame']
                base_status = snapshot['status']
            elif fallback_cap is not None:
                with fallback_lock:
                    frame = fallback_latest['frame']
                    fb_updated = fallback_latest['updated_at']
                if frame is None or now - fb_updated > offline_timeout:
                    if tailgating is not None:
                        tailgating.reset()
                    tracks = {}
                    crossing_count = 0
                    last_event_at = -math.inf
                    output = _placeholder('STREAM OFFLINE', (max_width, int(max_width * 9 / 16)))
                    yield _multipart(output)
                    time.sleep(0.1)
                    continue
                base_status = 'normal'
            else:
                if tailgating is not None:
                    tailgating.reset()
                tracks = {}
                crossing_count = 0
                last_event_at = -math.inf
                output = _placeholder('STREAM OFFLINE', (max_width, int(max_width * 9 / 16)))
                yield _multipart(output)
                time.sleep(0.1)
                continue

            if detector is not None and now - last_detection_at >= detection_interval:
                boxes = detector.detect(frame)
                result = tailgating.update(boxes, frame.shape, now)
                tracks = result.tracks
                crossing_count = result.crossing_count
                last_detection_at = now
                if result.event:
                    if now - last_event_at > crossing_window:
                        last_event_at = now
                        _record_tailgating_alarm(
                            app, gate_id, frame, result.track_ids,
                            crossing_count, alarm_cooldown,
                        )

            output = frame.copy()
            scale = 1.0
            if output.shape[1] > max_width:
                scale = max_width / output.shape[1]
                output = cv2.resize(
                    output,
                    (max_width, int(output.shape[0] * scale)),
                    interpolation=cv2.INTER_AREA,
                )

            tailgating_active = now - last_event_at <= status_hold_seconds
            if tailgating_active:
                _draw_tailgating_status(output, tracks, line_ratio, scale, crossing_count)
            else:
                metrics = snapshot['metrics'] if monitor_ok else {}
                _draw_status(output, base_status, metrics)
                _draw_people_and_line(output, tracks, line_ratio, scale, crossing_count)

            encoded, buffer = cv2.imencode(
                '.jpg', output, [int(cv2.IMWRITE_JPEG_QUALITY), 50]
            )
            if encoded:
                yield _multipart(buffer.tobytes())
            time.sleep(0.02)
    finally:
        fallback_alive['flag'] = False
        if fallback_cap is not None:
            try:
                fallback_cap.release()
            except Exception:
                pass


def _draw_people_and_line(frame, tracks, line_ratio, scale, crossing_count):
    height, width = frame.shape[:2]
    visible_tracks = [track for track in tracks.values() if not track['missing']]
    if not visible_tracks:
        return
    line_y = int(height * line_ratio)
    cv2.line(frame, (0, line_y), (width, line_y), (0, 220, 255), 2)
    for track_id, track in tracks.items():
        if track['missing']:
            continue
        x1, y1, x2, y2 = [int(value * scale) for value in track['box'][:4]]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (70, 220, 70), 2)
        cv2.putText(frame, 'ID {}'.format(track_id), (x1 + 5, y1 + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (70, 220, 70), 2)


def _draw_tailgating_status(frame, tracks, line_ratio, scale, crossing_count):
    _draw_people_and_line(frame, tracks, line_ratio, scale, crossing_count)
    cv2.rectangle(frame, (10, 10), (300, 48), (20, 20, 20), -1)
    cv2.putText(frame, 'TAILGATING', (20, 36), cv2.FONT_HERSHEY_SIMPLEX,
                0.65, (0, 0, 255), 2)
