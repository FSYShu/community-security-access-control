import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.fire_smoke_detector import FireSmokeDetector
from core.tailgating_detector import TailgatingDetector
from app.video_monitor.dangerous_behavior_stream import _draw_people_and_line


def test_close_people_crossing_line_triggers_tailgating():
    detector = TailgatingDetector(line_ratio=0.5, crossing_window=2.0)
    shape = (200, 300, 3)
    detector.update([(80, 30, 120, 90, 0.9), (125, 35, 165, 95, 0.9)], shape, 0.0)
    result = detector.update([(80, 80, 120, 150, 0.9), (125, 85, 165, 155, 0.9)], shape, 0.5)
    assert result.event is True
    assert len(result.track_ids) == 2


def test_single_person_does_not_trigger_tailgating():
    detector = TailgatingDetector(line_ratio=0.5)
    shape = (200, 300, 3)
    detector.update([(80, 30, 120, 90, 0.9)], shape, 0.0)
    result = detector.update([(80, 80, 120, 150, 0.9)], shape, 0.5)
    assert result.event is False


def test_two_people_crossing_up_triggers_when_both_directions_enabled():
    detector = TailgatingDetector(
        line_ratio=0.5,
        crossing_window=2.0,
        direction='both',
    )
    shape = (200, 300, 3)
    detector.update([(80, 150, 120, 190, 0.9), (125, 145, 165, 185, 0.9)], shape, 0.0)
    result = detector.update([(80, 70, 120, 125, 0.9), (125, 65, 165, 120, 0.9)], shape, 0.5)

    assert result.event is True
    assert len(result.track_ids) == 2


def test_far_apart_people_do_not_trigger_tailgating():
    detector = TailgatingDetector(line_ratio=0.5, max_horizontal_gap_ratio=0.2)
    shape = (200, 300, 3)
    detector.update([(20, 30, 60, 90, 0.9), (230, 35, 270, 95, 0.9)], shape, 0.0)
    result = detector.update([(20, 80, 60, 145, 0.9), (230, 85, 270, 150, 0.9)], shape, 0.5)

    assert result.event is False


def test_single_track_does_not_draw_tailgating_helpers():
    frame = np.zeros((200, 300, 3), dtype=np.uint8)
    tracks = {1: {'box': (80, 30, 120, 150), 'missing': 0}}

    _draw_people_and_line(frame, tracks, line_ratio=0.5, scale=1.0, crossing_count=0)

    assert not np.any(frame)


def test_two_tracks_draw_subtle_tailgating_helpers():
    frame = np.zeros((200, 300, 3), dtype=np.uint8)
    tracks = {
        1: {'box': (80, 30, 120, 150), 'missing': 0},
        2: {'box': (125, 35, 165, 155), 'missing': 0},
    }

    _draw_people_and_line(frame, tracks, line_ratio=0.5, scale=1.0, crossing_count=0)

    assert np.any(frame)
    assert np.count_nonzero(frame[100]) < frame.shape[1] * frame.shape[2] // 2


def test_tailgating_survives_a_short_person_detection_gap():
    detector = TailgatingDetector(line_ratio=0.5, crossing_window=5.0)
    shape = (200, 300, 3)
    detector.update([(80, 30, 120, 90, 0.9), (125, 35, 165, 95, 0.9)], shape, 0.0)
    detector.update([], shape, 0.2)
    result = detector.update(
        [(80, 80, 120, 150, 0.9), (125, 85, 165, 155, 0.9)], shape, 0.5
    )

    assert result.event is True


def test_box_edge_crossing_survives_missing_center_crossing_frame():
    detector = TailgatingDetector(line_ratio=0.5, crossing_window=5.0)
    shape = (200, 300, 3)
    detector.update([(70, 30, 110, 90, 0.9), (120, 35, 160, 95, 0.9)], shape, 0.0)
    result = detector.update(
        [(70, 50, 110, 115, 0.9), (120, 55, 160, 120, 0.9)], shape, 0.3
    )

    assert result.event is True


def test_moving_fire_colored_region_is_confirmed():
    detector = FireSmokeDetector(confirm_frames=2, fire_ratio_threshold=0.003)
    results = []
    for offset in (0, 8, 0, 8):
        frame = np.zeros((180, 320, 3), dtype=np.uint8)
        cv2.rectangle(frame, (120 + offset, 70), (190 + offset, 150), (0, 65, 180), -1)
        cv2.rectangle(frame, (135 + offset, 82), (180 + offset, 145), (0, 145, 255), -1)
        cv2.rectangle(frame, (150 + offset, 95), (170 + offset, 138), (20, 230, 255), -1)
        results.append(detector.analyze(frame))
    assert any(result.fire for result in results)


def test_moving_gray_object_does_not_trigger_smoke():
    detector = FireSmokeDetector(confirm_frames=3, smoke_ratio_threshold=0.10)
    results = []
    for offset in range(0, 48, 4):
        frame = np.full((180, 320, 3), 35, dtype=np.uint8)
        cv2.rectangle(frame, (20 + offset, 70), (55 + offset, 115), (130, 130, 130), -1)
        results.append(detector.analyze(frame))
    assert not any(result.smoke for result in results)


def test_large_moving_gray_person_shape_does_not_trigger_smoke():
    detector = FireSmokeDetector(confirm_frames=3)
    results = []
    for offset in range(0, 36, 3):
        frame = np.full((180, 320, 3), 145, dtype=np.uint8)
        cv2.rectangle(frame, (75 + offset, 30), (205 + offset, 179), (205, 205, 205), -1)
        cv2.circle(frame, (140 + offset, 42), 28, (175, 175, 175), -1)
        results.append(detector.analyze(frame))

    assert not any(result.smoke for result in results)


def test_textured_gray_motion_does_not_trigger_smoke_at_low_threshold():
    detector = FireSmokeDetector(confirm_frames=3, smoke_ratio_threshold=0.10)
    results = []
    rng = np.random.default_rng(7)
    texture = rng.integers(70, 221, size=(180, 320), dtype=np.uint8)
    for offset in range(8):
        shifted = np.roll(texture, offset * 5, axis=1)
        frame = cv2.cvtColor(shifted, cv2.COLOR_GRAY2BGR)
        frame[:, :, 2] = np.clip(frame[:, :, 2].astype(np.int16) + 25, 0, 255)
        results.append(detector.analyze(frame))

    assert not any(result.smoke for result in results)


def test_full_frame_end_card_is_ignored_as_scene_change():
    detector = FireSmokeDetector(confirm_frames=2, scene_change_ratio=0.35)
    frames = [
        np.zeros((180, 320, 3), dtype=np.uint8),
        np.full((180, 320, 3), 255, dtype=np.uint8),
        np.full((180, 320, 3), 255, dtype=np.uint8),
    ]
    results = [detector.analyze(frame) for frame in frames]
    assert not any(result.fire or result.smoke for result in results)


def test_static_fire_picture_is_confirmed():
    detector = FireSmokeDetector(
        confirm_frames=3,
        warmup_frames=0,
        static_fire_ratio_threshold=0.01,
    )
    frame = np.full((180, 320, 3), 35, dtype=np.uint8)
    cv2.ellipse(frame, (160, 105), (32, 58), 0, 0, 360, (0, 70, 180), -1)
    cv2.ellipse(frame, (160, 115), (24, 45), 0, 0, 360, (0, 150, 255), -1)
    cv2.ellipse(frame, (160, 125), (14, 30), 0, 0, 360, (20, 230, 255), -1)

    results = [detector.analyze(frame) for _ in range(4)]

    assert results[-1].fire is True
    assert results[-1].metrics['static_fire_ratio'] >= 0.01


def test_static_brown_floor_is_not_fire():
    detector = FireSmokeDetector(confirm_frames=3, warmup_frames=0)
    frame = np.full((180, 320, 3), (45, 85, 135), dtype=np.uint8)
    for y in range(20, 180, 20):
        cv2.line(frame, (0, y), (319, y), (35, 65, 110), 2)

    results = [detector.analyze(frame) for _ in range(6)]

    assert not any(result.fire for result in results)


def test_uniform_orange_lens_cover_is_not_fire():
    detector = FireSmokeDetector(confirm_frames=3, warmup_frames=0)
    frame = np.full((180, 320, 3), (30, 80, 180), dtype=np.uint8)

    results = [detector.analyze(frame) for _ in range(6)]

    assert not any(result.fire for result in results)
