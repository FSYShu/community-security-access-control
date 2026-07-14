"""Unified view for independent dangerous-behavior detectors."""

import logging
import math
import os
import threading
import time

import cv2
import numpy as np

from .device_tamper_stream import _draw_status, _multipart, _placeholder
from core.rtmp_relay import start_rtmp_pull, read_cv2_frame_from_pull, stop_rtmp_pull
from core.shared_frame_store import get_frame_with_info as _get_shared_frame_with_info
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
    function first checks the shared frame store for recent frames, then
    falls back to pulling from *stream_url* via the shared FFmpeg relay
    (rtmp_relay) so the stream is never left showing only "STREAM OFFLINE".
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

    fallback_pull = None
    fallback_alive = {'flag': True}
    fallback_latest = {'frame': None, 'updated_at': 0.0}
    fallback_lock = threading.Lock()

    def _start_fallback_reader(url):
        nonlocal fallback_pull
        pull = start_rtmp_pull(url, fps=25, max_width=max_width)
        if pull is None:
            logger.warning('FFmpeg pull unavailable for gate %s fallback', gate_id)
            return
        fallback_pull = pull

        def reader():
            while fallback_alive['flag']:
                if pull['process'].poll() is not None:
                    break
                try:
                    ok, frame = read_cv2_frame_from_pull(pull)
                except Exception:
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

            if not monitor_ok and stream_url and fallback_pull is None:
                shared_jpeg, shared_ts = _get_shared_frame_with_info(stream_url)
                if shared_jpeg is not None and shared_ts is not None and time.time() - shared_ts <= offline_timeout:
                    pass
                else:
                    logger.info('Monitor unavailable for gate %s, starting shared RTMP pull', gate_id)
                    _start_fallback_reader(stream_url)

            if monitor_ok:
                frame = snapshot['frame']
                base_status = snapshot['status']
            elif fallback_pull is not None:
                with fallback_lock:
                    frame = fallback_latest['frame']
                    fb_updated = fallback_latest['updated_at']
                if frame is None or now - fb_updated > offline_timeout:
                    shared_jpeg, shared_ts = _get_shared_frame_with_info(stream_url) if stream_url else (None, None)
                    if shared_jpeg is not None and shared_ts is not None and time.time() - shared_ts <= offline_timeout:
                        arr = np.frombuffer(shared_jpeg, dtype=np.uint8)
                        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                        if frame is not None:
                            base_status = 'normal'
                            shared_jpeg = None
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
                else:
                    base_status = 'normal'
            else:
                shared_jpeg, shared_ts = _get_shared_frame_with_info(stream_url) if stream_url else (None, None)
                if shared_jpeg is not None and shared_ts is not None and time.time() - shared_ts <= offline_timeout:
                    arr = np.frombuffer(shared_jpeg, dtype=np.uint8)
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if frame is not None:
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
        if fallback_pull is not None:
            try:
                stop_rtmp_pull(fallback_pull['url'])
            except Exception:
                pass


def _draw_people_and_line(frame, tracks, line_ratio, scale, crossing_count):
    height, width = frame.shape[:2]
    visible_tracks = [track for track in tracks.values() if not track['missing']]
    if len(visible_tracks) < 2:
        return
    line_y = int(height * line_ratio)
    line_color = (180, 130, 70)
    for start_x in range(0, width, 32):
        cv2.line(
            frame,
            (start_x, line_y),
            (min(start_x + 10, width - 1), line_y),
            line_color,
            1,
        )
    for track in tracks.values():
        if track['missing']:
            continue
        x1, y1, x2, y2 = [int(value * scale) for value in track['box'][:4]]
        _draw_track_corners(frame, x1, y1, x2, y2, line_color)


def _draw_track_corners(frame, x1, y1, x2, y2, color):
    corner = max(8, min(18, (x2 - x1) // 4, (y2 - y1) // 4))
    segments = (
        ((x1, y1), (x1 + corner, y1)), ((x1, y1), (x1, y1 + corner)),
        ((x2, y1), (x2 - corner, y1)), ((x2, y1), (x2, y1 + corner)),
        ((x1, y2), (x1 + corner, y2)), ((x1, y2), (x1, y2 - corner)),
        ((x2, y2), (x2 - corner, y2)), ((x2, y2), (x2, y2 - corner)),
    )
    for start, end in segments:
        cv2.line(frame, start, end, color, 1)


def _draw_tailgating_status(frame, tracks, line_ratio, scale, crossing_count):
    _draw_people_and_line(frame, tracks, line_ratio, scale, crossing_count)
    cv2.rectangle(frame, (10, 10), (300, 48), (20, 20, 20), -1)
    cv2.putText(frame, 'TAILGATING', (20, 36), cv2.FONT_HERSHEY_SIMPLEX,
                0.65, (0, 0, 255), 2)
