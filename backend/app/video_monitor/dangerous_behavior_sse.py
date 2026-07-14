"""SSE event stream for dangerous behavior detection (tailgating + device tamper status)."""

import json
import logging
import math
import os
import threading
import time

import cv2
import numpy as np

from core.rtmp_relay import start_rtmp_pull, read_cv2_frame_from_pull, stop_rtmp_pull
from core.shared_frame_store import get_frame_with_info as _get_shared_frame_with_info
from .tailgating_stream import _opencv_compatible_path, _record_tailgating_alarm
from .device_tamper_stream import _clear_alarm_states, _record_alarm, _placeholder
from core.tailgating_detector import MobileNetPersonDetector, TailgatingDetector
from core.device_tamper import NORMAL, DeviceTamperDetector
from core.fire_smoke_detector import FireSmokeDetector

logger = logging.getLogger(__name__)

DETECT_INTERVAL = 0.5
SSE_PUSH_INTERVAL = 0.5


def generate_dangerous_behavior_sse(
        app, monitor, gate_id, stream_url, prototxt_path, model_path,
        fps=20, max_width=640, confidence=0.35, detection_interval=0.10,
        line_ratio=0.62, crossing_window=5.0,
        max_horizontal_gap_ratio=0.28, authorized_entries=1,
        direction='both', status_hold_seconds=3.0,
        alarm_cooldown=60, offline_timeout=5):
    yield 'event: connected\ndata: {}\n\n'.format(json.dumps({}))

    own_pull = False
    entry = None
    slot = {'alive': True}

    for _ in range(6):
        shared_jpeg, shared_ts = _get_shared_frame_with_info(stream_url)
        if shared_jpeg is not None and shared_ts is not None and time.time() - shared_ts <= offline_timeout:
            break
        time.sleep(0.5)
    else:
        entry = start_rtmp_pull(stream_url, fps=fps, max_width=max_width)
        if entry is not None:
            own_pull = True

    model_available = (
        os.path.isfile(prototxt_path)
        and os.path.isfile(model_path)
    )
    logger.info('Tailgating model check: prototxt=%s exists=%s, model=%s exists=%s, model_available=%s',
                prototxt_path, os.path.isfile(prototxt_path), model_path, os.path.isfile(model_path), model_available)
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
            logger.warning('Tailgating model init failed: %s', exc)
            detector = None
            tailgating = None

    tamper_detector = DeviceTamperDetector(
        confirm_frames=app.config.get('DEVICE_TAMPER_CONFIRM_FRAMES', 3),
        blocked_confirm_frames=app.config.get('DEVICE_BLOCKED_CONFIRM_FRAMES', 8),
        recovery_frames=app.config.get('DEVICE_TAMPER_RECOVERY_FRAMES', 4),
        impact_confirm_frames=app.config.get('DEVICE_IMPACT_CONFIRM_FRAMES', 1),
        impact_motion_threshold=app.config.get('DEVICE_IMPACT_MOTION_THRESHOLD', 6.0),
        impact_coherence_threshold=app.config.get('DEVICE_IMPACT_COHERENCE_THRESHOLD', 0.6),
        impact_reversal_cosine=app.config.get('DEVICE_IMPACT_REVERSAL_COSINE', -0.35),
        impact_window_frames=app.config.get('DEVICE_IMPACT_WINDOW_FRAMES', 6),
        impact_blur_drop_threshold=app.config.get('DEVICE_IMPACT_BLUR_DROP_THRESHOLD', 0.35),
        impact_min_tracked_points=app.config.get('DEVICE_IMPACT_MIN_TRACKED_POINTS', 20),
        impact_scene_change_limit=app.config.get('DEVICE_IMPACT_SCENE_CHANGE_LIMIT', 0.60),
        impact_sudden_multiplier=app.config.get('DEVICE_IMPACT_SUDDEN_MULTIPLIER', 1.25),
    )
    emergency_detector = FireSmokeDetector(
        confirm_frames=app.config.get('FIRE_SMOKE_CONFIRM_FRAMES', 4),
        recovery_frames=app.config.get('FIRE_SMOKE_RECOVERY_FRAMES', 60),
        fire_recovery_frames=app.config.get('FIRE_RECOVERY_FRAMES', 10),
        fire_ratio_threshold=app.config.get('FIRE_RATIO_THRESHOLD', 0.006),
        smoke_ratio_threshold=app.config.get('SMOKE_RATIO_THRESHOLD', 0.10),
        warmup_frames=app.config.get('FIRE_SMOKE_WARMUP_FRAMES', 10),
        scene_change_ratio=app.config.get('FIRE_SMOKE_SCENE_CHANGE_RATIO', 0.35),
        static_fire_ratio_threshold=app.config.get('STATIC_FIRE_RATIO_THRESHOLD', 0.02),
    )

    detection_state = {
        'tracks': {},
        'crossing_count': 0,
        'tailgating_active': False,
        'tamper_status': 'normal',
        'tamper_metrics': {},
        'frame_width': 0,
        'frame_height': 0,
        'lock': threading.Lock(),
        'last_time': 0.0,
    }

    def _get_frame():
        if own_pull and entry is not None:
            if entry['process'].poll() is None:
                ok, f = read_cv2_frame_from_pull(entry)
                if ok and f is not None:
                    return f
            return None
        shared_jpeg, shared_ts = _get_shared_frame_with_info(stream_url)
        if shared_jpeg is not None and shared_ts is not None and time.time() - shared_ts <= offline_timeout:
            arr = np.frombuffer(shared_jpeg, dtype=np.uint8).copy()
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return None

    def detector_thread():
        last_detection_at = 0.0
        last_event_at = -math.inf
        while slot['alive']:
            now = time.monotonic()
            elapsed = now - last_detection_at
            if elapsed < detection_interval:
                time.sleep(detection_interval - elapsed)
                continue

            frame = _get_frame()
            if frame is None:
                time.sleep(0.3)
                continue

            try:
                h, w = frame.shape[:2]

                tamper_result = tamper_detector.analyze(frame)
                emergency_result = emergency_detector.analyze(frame)

                tamper_status = tamper_result.status
                tamper_metrics = tamper_result.metrics

                active_states = {tamper_status} if tamper_status != NORMAL else set()
                if emergency_result.fire:
                    active_states.add('open_flame')
                if emergency_result.smoke:
                    active_states.add('smoke')
                _clear_alarm_states(gate_id, active_states)

                if tamper_result.event:
                    _record_alarm(
                        app, gate_id, tamper_result.status,
                        frame, tamper_result.metrics, alarm_cooldown,
                    )

                display_status = tamper_status
                if tamper_status == 'device_blocked':
                    display_status = tamper_status
                elif emergency_result.fire:
                    display_status = 'open_flame'
                elif emergency_result.smoke:
                    display_status = 'smoke'

                if emergency_result.event:
                    if emergency_result.fire:
                        _record_alarm(
                            app, gate_id, 'open_flame', frame,
                            emergency_result.metrics, alarm_cooldown,
                        )
                    if emergency_result.smoke:
                        _record_alarm(
                            app, gate_id, 'smoke', frame,
                            emergency_result.metrics, alarm_cooldown,
                        )

                tamper_status = display_status
                tamper_metrics = {**tamper_metrics, **emergency_result.metrics}

                tracks = {}
                crossing_count = 0
                tailgating_active = False

                if detector is not None:
                    boxes = detector.detect(frame)
                    result = tailgating.update(boxes, frame.shape, now)
                    tracks = result.tracks
                    crossing_count = result.crossing_count
                    if result.event:
                        if now - last_event_at > crossing_window:
                            last_event_at = now
                            _record_tailgating_alarm(
                                app, gate_id, frame, result.track_ids,
                                crossing_count, alarm_cooldown,
                            )
                    tailgating_active = now - last_event_at <= status_hold_seconds

                serializable_tracks = {}
                for tid, t in tracks.items():
                    serializable_tracks[str(tid)] = {
                        'box': [float(v) for v in t['box'][:4]],
                        'missing': t['missing'],
                    }

                effective_status = tamper_status if tamper_status != 'normal' else ('tailgating' if tailgating_active else 'normal')

                with detection_state['lock']:
                    detection_state['tracks'] = serializable_tracks
                    detection_state['crossing_count'] = crossing_count
                    detection_state['tailgating_active'] = tailgating_active
                    detection_state['tamper_status'] = effective_status
                    detection_state['tamper_metrics'] = tamper_metrics
                    detection_state['frame_width'] = w
                    detection_state['frame_height'] = h
                    detection_state['last_time'] = time.time()

                last_detection_at = now
            except Exception as e:
                logger.error('Dangerous behavior detection error: %s', str(e))
                with detection_state['lock']:
                    detection_state['last_time'] = time.time()

    t = threading.Thread(target=detector_thread, daemon=True)
    t.start()

    try:
        time.sleep(0.5)
        while slot['alive']:
            with detection_state['lock']:
                tracks = dict(detection_state['tracks'])
                crossing_count = detection_state['crossing_count']
                tailgating_active = detection_state['tailgating_active']
                tamper_status = detection_state['tamper_status']
                tamper_metrics = dict(detection_state['tamper_metrics'])
                frame_w = detection_state['frame_width']
                frame_h = detection_state['frame_height']

            data = json.dumps({
                'tracks': tracks,
                'crossing_count': crossing_count,
                'tailgating_active': tailgating_active,
                'tamper_status': tamper_status,
                'tamper_metrics': tamper_metrics,
                'frame_width': frame_w,
                'frame_height': frame_h,
                'line_ratio': line_ratio,
                'model_available': detector is not None,
            })

            yield 'event: detection\ndata: {}\n\n'.format(data)

            time.sleep(SSE_PUSH_INTERVAL)
    finally:
        slot['alive'] = False
        if own_pull and entry is not None:
            stop_rtmp_pull(stream_url)