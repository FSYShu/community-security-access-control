"""Temporal fire and smoke candidate detection using OpenCV signals."""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class FireSmokeResult:
    fire: bool
    smoke: bool
    event: bool
    metrics: dict
    fire_mask: np.ndarray
    smoke_mask: np.ndarray


class FireSmokeDetector:
    def __init__(self, confirm_frames=5, recovery_frames=20, fire_recovery_frames=10,
                 fire_ratio_threshold=0.006, smoke_ratio_threshold=0.10,
                 warmup_frames=0, scene_change_ratio=0.35,
                 static_fire_ratio_threshold=0.02):
        self.confirm_frames = confirm_frames
        self.recovery_frames = recovery_frames
        self.fire_recovery_frames = fire_recovery_frames
        self.fire_ratio_threshold = fire_ratio_threshold
        self.smoke_ratio_threshold = smoke_ratio_threshold
        self.warmup_frames = warmup_frames
        self.scene_change_ratio = scene_change_ratio
        self.static_fire_ratio_threshold = static_fire_ratio_threshold
        self.previous_gray = None
        self.smoke_memory = None
        self.fire_count = 0
        self.smoke_count = 0
        self.fire_recovery_count = 0
        self.smoke_recovery_count = 0
        self.fire_active = False
        self.smoke_active = False
        self.frame_count = 0

    def analyze(self, frame):
        small = cv2.resize(frame, (320, 180), interpolation=cv2.INTER_AREA)
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        h, s, v = cv2.split(hsv)

        fire_appearance = ((h <= 35) & (s >= 100) & (v >= 120)).astype(np.uint8)
        smoke_appearance = ((s <= 60) & (v >= 55) & (v <= 235)).astype(np.uint8)
        motion = np.zeros_like(gray, dtype=np.uint8)
        if self.previous_gray is not None:
            difference = cv2.absdiff(gray, self.previous_gray)
            motion = (difference >= 10).astype(np.uint8)
        self.previous_gray = gray
        self.frame_count += 1
        motion_ratio = float(np.mean(motion > 0))

        kernel = np.ones((5, 5), dtype=np.uint8)
        expanded_motion = cv2.dilate(motion, np.ones((7, 7), dtype=np.uint8))
        fire_mask = cv2.morphologyEx(fire_appearance * expanded_motion, cv2.MORPH_OPEN, kernel)
        smoke_seed = cv2.morphologyEx(smoke_appearance * expanded_motion, cv2.MORPH_OPEN, kernel)

        # A scene cut, fade, or end card changes most pixels at once. It is
        # not a physical fire/smoke signal and must not start an alarm.
        scene_change = motion_ratio >= self.scene_change_ratio
        if scene_change or self.frame_count <= self.warmup_frames:
            fire_mask.fill(0)
            smoke_seed.fill(0)

        fire_mask = self._filter_fire_regions(fire_mask)
        static_fire_mask = cv2.morphologyEx(fire_appearance, cv2.MORPH_OPEN, kernel)
        static_fire_mask = self._filter_fire_regions(static_fire_mask)
        fire_pixels = fire_appearance > 0
        if np.count_nonzero(fire_pixels):
            fire_hue_std = float(np.std(h[fire_pixels]))
            fire_value_std = float(np.std(v[fire_pixels]))
            fire_value_mean = float(np.mean(v[fire_pixels]))
        else:
            fire_hue_std = 0.0
            fire_value_std = 0.0
            fire_value_mean = 0.0
        if self.smoke_memory is None:
            self.smoke_memory = np.zeros_like(gray, dtype=np.float32)
        self.smoke_memory *= 0.96
        self.smoke_memory[smoke_seed > 0] = 1.0
        smoke_mask = ((self.smoke_memory >= 0.15) & (smoke_appearance > 0)).astype(np.uint8)
        smoke_mask = cv2.morphologyEx(smoke_mask, cv2.MORPH_OPEN, kernel)
        if scene_change or self.frame_count <= self.warmup_frames:
            smoke_mask.fill(0)
        fire_ratio = float(np.mean(fire_mask > 0))
        static_fire_ratio = float(np.mean(static_fire_mask > 0))
        smoke_signal_ratio = float(np.mean(smoke_seed > 0))
        smoke_ratio = float(np.mean(smoke_mask > 0))
        smoke_pixels = smoke_seed > 0
        frame_saturation_mean = float(np.mean(s))
        smoke_saturation_mean = (
            float(np.mean(s[smoke_pixels])) if np.count_nonzero(smoke_pixels) else 0.0
        )
        smoke_saturation_std = (
            float(np.std(s[smoke_pixels])) if np.count_nonzero(smoke_pixels) else 0.0
        )

        fire_threshold = self.fire_ratio_threshold * (0.5 if self.fire_active else 1.0)
        # Keep the recovery threshold close to the activation threshold. A
        # large hysteresis made moving people and gray walls sustain smoke
        # alarms long after the original candidate disappeared.
        smoke_threshold = self.smoke_ratio_threshold * (0.80 if self.smoke_active else 1.0)
        dynamic_fire_quality = (
            fire_hue_std >= 4.0
            and fire_value_std >= 20.0
            and fire_value_mean >= 155.0
        )
        static_fire_quality = (
            fire_hue_std >= 5.0
            and fire_value_std >= 30.0
            and fire_value_mean >= 170.0
        )
        static_fire_signal = (
            self.static_fire_ratio_threshold <= static_fire_ratio <= 0.35
            and static_fire_quality
            and not scene_change
            and self.frame_count > self.warmup_frames
        )
        fire_signal = (
            fire_ratio >= fire_threshold and dynamic_fire_quality
        ) or static_fire_signal
        self.fire_count = self.fire_count + 1 if fire_signal else 0
        # Smoke is normally a soft, nearly neutral region. Gray buildings,
        # clothing, and moving people have much larger saturation variation
        # even when their candidate area exceeds the unchanged 10% threshold.
        smoke_signal = (
            smoke_signal_ratio >= smoke_threshold
            and frame_saturation_mean >= 10.0
            and smoke_saturation_mean >= 10.0
            and smoke_saturation_std <= 12.0
        )
        self.smoke_count = self.smoke_count + 1 if smoke_signal else 0
        event = False
        if self.fire_count >= self.confirm_frames:
            event = event or not self.fire_active
            self.fire_active = True
            self.fire_recovery_count = 0
        elif self.fire_active and not fire_signal:
            self.fire_recovery_count += 1
            if self.fire_recovery_count >= self.fire_recovery_frames:
                self.fire_active = False
                self.fire_recovery_count = 0

        if self.smoke_count >= self.confirm_frames:
            event = event or not self.smoke_active
            self.smoke_active = True
            self.smoke_recovery_count = 0
        elif self.smoke_active and not smoke_signal:
            self.smoke_recovery_count += 1
            if self.smoke_recovery_count >= self.recovery_frames:
                self.smoke_active = False
                self.smoke_recovery_count = 0

        return FireSmokeResult(
            fire=self.fire_active,
            smoke=self.smoke_active,
            event=event,
            metrics={
                'fire_ratio': fire_ratio,
                'static_fire_ratio': static_fire_ratio,
                'fire_candidate': fire_signal,
                'fire_hue_std': fire_hue_std,
                'fire_value_std': fire_value_std,
                'fire_value_mean': fire_value_mean,
                'smoke_ratio': smoke_ratio,
                'smoke_signal_ratio': smoke_signal_ratio,
                'frame_saturation_mean': frame_saturation_mean,
                'smoke_saturation_mean': smoke_saturation_mean,
                'smoke_saturation_std': smoke_saturation_std,
                'motion_ratio': motion_ratio,
                'scene_change': scene_change,
            },
            fire_mask=fire_mask,
            smoke_mask=smoke_mask,
        )

    @staticmethod
    def _filter_fire_regions(mask):
        """Remove tiny, border-attached overlays such as logos and captions."""
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        filtered = np.zeros_like(mask)
        height, width = mask.shape
        min_area = max(80, int(height * width * 0.0025))
        for label in range(1, count):
            x, y, w, h, area = stats[label]
            touches_border = x == 0 or y == 0 or x + w >= width or y + h >= height
            if area >= min_area and not touches_border and h >= 8:
                filtered[labels == label] = 1
        return filtered
