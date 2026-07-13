"""Unified view for independent dangerous-behavior detectors."""

import logging
import math
import os
import time

import cv2

from .device_tamper_stream import _draw_status, _multipart, _placeholder
from .tailgating_stream import (
    _opencv_compatible_path,
    _record_tailgating_alarm,
)
from core.tailgating_detector import MobileNetPersonDetector, TailgatingDetector

logger = logging.getLogger(__name__)


def generate_frames_with_dangerous_behavior(
        app, monitor, gate_id, prototxt_path, model_path,
        max_width=640, confidence=0.35, detection_interval=0.10,
        line_ratio=0.62, crossing_window=5.0,
        max_horizontal_gap_ratio=0.28, authorized_entries=1,
        direction='both', status_hold_seconds=3.0,
        alarm_cooldown=60, offline_timeout=5):
    """Render existing device status plus an independent tailgating layer."""
    if not os.path.isfile(prototxt_path) or not os.path.isfile(model_path):
        yield _multipart(_placeholder('TAILGATING MODEL MISSING', (max_width, int(max_width * 9 / 16))))
        return

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
    last_detection_at = 0.0
    last_event_at = -math.inf
    tracks = {}
    crossing_count = 0
    while True:
        snapshot = monitor.get_snapshot(gate_id) if monitor else None
        now = time.monotonic()
        if (
            snapshot is None
            or snapshot['frame'] is None
            or now - snapshot['updated_at'] > offline_timeout
        ):
            tailgating.reset()
            tracks = {}
            crossing_count = 0
            last_event_at = -math.inf
            output = _placeholder('STREAM OFFLINE', (max_width, int(max_width * 9 / 16)))
            yield _multipart(output)
            time.sleep(0.1)
            continue

        frame = snapshot['frame']
        base_status = snapshot['status']
        # Tailgating keeps its own tracking state. Device-tamper, fire, and
        # smoke labels are display states and must not erase crossing history.
        if now - last_detection_at >= detection_interval:
            boxes = detector.detect(frame)
            result = tailgating.update(boxes, frame.shape, now)
            tracks = result.tracks
            crossing_count = result.crossing_count
            last_detection_at = now
            if result.event:
                # Multiple detector IDs can describe the same group while it
                # passes the door. Do not let those duplicates extend the
                # visible alarm across the rest of the video.
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
            _draw_status(output, base_status, snapshot['metrics'])
            _draw_people_and_line(output, tracks, line_ratio, scale, crossing_count)

        encoded, buffer = cv2.imencode(
            '.jpg', output, [int(cv2.IMWRITE_JPEG_QUALITY), 50]
        )
        if encoded:
            yield _multipart(buffer.tobytes())
        time.sleep(0.02)


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
