import os
import sys
import threading
import time

import cv2
import numpy as np
from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.device_tamper import BLOCKED, IMPACT, MOVED, NORMAL, DeviceTamperDetector
from app.device_tamper_monitor import DeviceTamperMonitor, start_device_tamper_monitor
from app.video_monitor.dangerous_behavior_sse import (
    _active_alarm_states,
    _clear_alarm_states,
)


def textured_frame(seed=1):
    rng = np.random.default_rng(seed)
    frame = rng.integers(0, 256, (360, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame, (80, 60), (250, 260), (255, 255, 255), 8)
    cv2.circle(frame, (430, 180), 90, (0, 0, 0), 8)
    return frame


def shifted_frame(frame, dx, dy=0):
    matrix = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(frame, matrix, (frame.shape[1], frame.shape[0]), borderMode=cv2.BORDER_REFLECT)


def test_black_frames_confirm_lens_blocked():
    detector = DeviceTamperDetector(confirm_frames=3)
    frame = np.zeros((360, 640, 3), dtype=np.uint8)

    assert detector.analyze(frame).status == NORMAL
    assert detector.analyze(frame).status == NORMAL
    result = detector.analyze(frame)

    assert result.status == BLOCKED
    assert result.event is True


def test_normal_frames_recover_from_blocked():
    detector = DeviceTamperDetector(confirm_frames=2, recovery_frames=2)
    blocked = np.zeros((360, 640, 3), dtype=np.uint8)
    normal = textured_frame()

    detector.analyze(blocked)
    assert detector.analyze(blocked).status == BLOCKED
    detector.analyze(normal)

    assert detector.analyze(normal).status == NORMAL


def test_colored_occlusion_with_letterbox_stays_blocked():
    detector = DeviceTamperDetector(confirm_frames=3, recovery_frames=3)
    frame = np.zeros((360, 640, 3), dtype=np.uint8)
    rng = np.random.default_rng(21)
    red_cover = np.full((280, 520, 3), (35, 55, 175), dtype=np.int16)
    red_cover += rng.integers(-2, 3, red_cover.shape, dtype=np.int16)
    frame[:280, :520] = np.clip(red_cover, 0, 255).astype(np.uint8)

    detector.analyze(frame)
    detector.analyze(frame)
    result = detector.analyze(frame)

    assert result.status == BLOCKED
    assert result.metrics['valid_ratio'] < 0.8
    for _ in range(8):
        assert detector.analyze(frame).status == BLOCKED


def test_normal_letterboxed_camera_frame_is_not_blocked():
    detector = DeviceTamperDetector(confirm_frames=2)
    frame = np.zeros((360, 640, 3), dtype=np.uint8)
    frame[:280, :520] = textured_frame(22)[:280, :520]

    detector.analyze(frame)
    result = detector.analyze(frame)

    assert result.status == NORMAL


def test_bright_uniform_end_card_is_not_lens_blocked():
    detector = DeviceTamperDetector(confirm_frames=2)
    frame = np.full((360, 640, 3), 235, dtype=np.uint8)

    detector.analyze(frame)
    result = detector.analyze(frame)

    assert result.status != BLOCKED


def test_changed_camera_view_confirms_moved():
    detector = DeviceTamperDetector(confirm_frames=2, baseline_frames=2)
    normal = textured_frame(3)
    moved = cv2.flip(normal, 1)

    detector.analyze(normal)
    detector.analyze(normal)
    detector.analyze(moved)
    result = detector.analyze(moved)

    assert result.status == MOVED
    assert result.event is True


def test_reversing_global_motion_confirms_camera_impact():
    detector = DeviceTamperDetector(
        confirm_frames=2,
        impact_confirm_frames=1,
        impact_motion_threshold=4.0,
        impact_coherence_threshold=0.55,
    )
    normal = textured_frame(8)

    detector.analyze(normal)
    detector.analyze(normal)
    first_motion = detector.analyze(shifted_frame(normal, 12))
    result = detector.analyze(shifted_frame(normal, -12))

    assert first_motion.status != IMPACT
    assert result.status == IMPACT
    assert result.event is True
    assert result.metrics['global_motion'] >= 4.0
    assert result.metrics['motion_coherence'] >= 0.55


def test_same_direction_motion_is_not_camera_impact():
    detector = DeviceTamperDetector(
        confirm_frames=2,
        impact_confirm_frames=1,
        impact_motion_threshold=4.0,
        impact_coherence_threshold=0.55,
        impact_blur_drop_threshold=1.0,
    )
    normal = textured_frame(9)

    detector.analyze(normal)
    detector.analyze(shifted_frame(normal, 6))
    detector.analyze(shifted_frame(normal, 12))
    result = detector.analyze(shifted_frame(normal, 18))

    assert result.status != IMPACT
    assert result.metrics['impact_signal'] is False


def test_unrelated_scene_cut_is_not_camera_impact():
    detector = DeviceTamperDetector(
        confirm_frames=2,
        impact_confirm_frames=1,
        impact_motion_threshold=4.0,
    )
    first_scene = textured_frame(10)
    second_scene = textured_frame(11)

    detector.analyze(first_scene)
    detector.analyze(first_scene)
    result = detector.analyze(second_scene)

    assert result.status != IMPACT
    assert result.metrics['impact_signal'] is False
    assert result.metrics['impact_score'] < 2


def test_background_monitor_does_not_start_when_disabled():
    app = Flask(__name__)
    app.config.update(DEVICE_TAMPER_BACKGROUND_ENABLED=False, TESTING=False)

    assert start_device_tamper_monitor(app) is None
    assert 'device_tamper_monitor' not in app.extensions


def test_background_monitor_is_singleton(monkeypatch):
    app = Flask(__name__)
    app.config.update(DEVICE_TAMPER_BACKGROUND_ENABLED=True, TESTING=False)
    starts = []

    monkeypatch.setattr(DeviceTamperMonitor, 'start', lambda self: starts.append(self))

    first = start_device_tamper_monitor(app)
    second = start_device_tamper_monitor(app)

    assert first is second
    assert starts == [first, first]


def test_background_snapshot_returns_frame_copy():
    app = Flask(__name__)
    monitor = DeviceTamperMonitor(app)
    source = np.full((10, 10, 3), 80, dtype=np.uint8)
    monitor.workers[1] = {
        'state_lock': threading.Lock(),
        'frame': source,
        'status': NORMAL,
        'metrics': {'brightness': 80.0},
        'updated_at': time.monotonic(),
    }

    snapshot = monitor.get_snapshot(1)
    snapshot['frame'][:] = 0

    assert snapshot['status'] == NORMAL
    assert np.all(source == 80)


def test_alarm_state_is_rearmed_only_after_recovery():
    _active_alarm_states.clear()
    _active_alarm_states.add((1, 'smoke'))

    _clear_alarm_states(1, {'smoke'})
    assert (1, 'smoke') in _active_alarm_states

    _clear_alarm_states(1, set())
    assert (1, 'smoke') not in _active_alarm_states

    _active_alarm_states.add((1, 'smoke'))
    assert (1, 'smoke') in _active_alarm_states
    _active_alarm_states.clear()
