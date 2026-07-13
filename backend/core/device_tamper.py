"""Frame-based camera tamper detection.

The detector intentionally uses conservative image-quality and scene-change
signals. It is an initial tamper alarm, not a claim that a person struck the
camera; that requires an audio or hardware sensor signal as well.
"""

from collections import deque
from dataclasses import dataclass

import cv2
import numpy as np


NORMAL = 'normal'
BLOCKED = 'device_blocked'
BLURRED = 'device_blurred'
MOVED = 'device_moved'
IMPACT = 'camera_impact'


@dataclass
class TamperResult:
    status: str
    event: bool
    metrics: dict


class DeviceTamperDetector:
    """Confirm a tamper state across several frames to reduce false alarms."""

    def __init__(self, confirm_frames=3, recovery_frames=4, baseline_frames=5,
                 blocked_confirm_frames=None,
                 impact_confirm_frames=1, impact_motion_threshold=6.0,
                 impact_coherence_threshold=0.6,
                 impact_reversal_cosine=-0.35, impact_window_frames=6,
                 impact_blur_drop_threshold=0.35,
                 impact_min_tracked_points=20,
                 impact_scene_change_limit=0.60,
                 impact_sudden_multiplier=1.25):
        self.confirm_frames = confirm_frames
        self.blocked_confirm_frames = blocked_confirm_frames or confirm_frames
        self.recovery_frames = recovery_frames
        self.baseline_frames = baseline_frames
        self.impact_confirm_frames = impact_confirm_frames
        self.impact_motion_threshold = impact_motion_threshold
        self.impact_coherence_threshold = impact_coherence_threshold
        self.impact_reversal_cosine = impact_reversal_cosine
        self.impact_blur_drop_threshold = impact_blur_drop_threshold
        self.impact_min_tracked_points = impact_min_tracked_points
        self.impact_scene_change_limit = impact_scene_change_limit
        self.impact_sudden_multiplier = impact_sudden_multiplier
        self._baseline = None
        self._baseline_count = 0
        self._previous_gray = None
        self._previous_sharpness = None
        self._motion_history = deque(maxlen=impact_window_frames)
        self._candidate = NORMAL
        self._candidate_count = 0
        self.status = NORMAL
        self._recovery_count = 0

    def analyze(self, frame):
        gray = self._prepare(frame)
        metrics = self._metrics(gray)

        impact_signal, impact_metrics = self._detect_impact(metrics)
        metrics['impact_signal'] = impact_signal
        metrics.update(impact_metrics)
        candidate = self._classify(metrics)
        if self._baseline is None and candidate == NORMAL:
            self._learn_baseline(gray)
        elif (
            candidate == NORMAL
            and metrics['scene_change'] < 0.08
            and metrics['global_motion'] < 1.0
        ):
            self._update_baseline(gray)

        if candidate == self._candidate:
            self._candidate_count += 1
        else:
            self._candidate = candidate
            self._candidate_count = 1

        event = False
        required_frames = (
            self.impact_confirm_frames if candidate == IMPACT
            else self.blocked_confirm_frames if candidate == BLOCKED
            else self.confirm_frames
        )
        if self.status == NORMAL:
            if candidate != NORMAL and self._candidate_count >= required_frames:
                self.status = candidate
                self._recovery_count = 0
                event = True
        elif candidate == self.status:
            self._recovery_count = 0
        elif candidate == NORMAL:
            self._recovery_count += 1
            if self._recovery_count >= self.recovery_frames:
                self.status = NORMAL
                self._recovery_count = 0
        elif self._candidate_count >= required_frames:
            self.status = candidate
            self._recovery_count = 0
            event = True

        return TamperResult(self.status, event, metrics)

    def reset(self):
        self._baseline = None
        self._baseline_count = 0
        self._previous_gray = None
        self._previous_sharpness = None
        self._motion_history.clear()
        self._candidate = NORMAL
        self._candidate_count = 0
        self.status = NORMAL
        self._recovery_count = 0

    @staticmethod
    def _prepare(frame):
        if frame is None or not isinstance(frame, np.ndarray):
            raise ValueError('frame must be a numpy array')
        if frame.ndim == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        return cv2.resize(gray, (320, 180), interpolation=cv2.INTER_AREA)

    def _metrics(self, gray):
        edges = cv2.Canny(gray, 50, 150)
        active_mask = (gray > 12).astype(np.uint8)
        interior_mask = cv2.erode(active_mask, np.ones((5, 5), dtype=np.uint8)) > 0
        valid_ratio = float(np.mean(active_mask))
        if np.count_nonzero(interior_mask) < 100:
            interior_mask = active_mask > 0

        valid_pixels = gray[interior_mask]
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        if valid_pixels.size:
            brightness = float(np.mean(valid_pixels))
            contrast = float(np.std(valid_pixels))
            sharpness = float(np.var(laplacian[interior_mask]))
            edge_density = float(np.mean(edges[interior_mask] > 0))
            histogram = np.bincount(valid_pixels, minlength=256).astype(np.float64)
            probabilities = histogram[histogram > 0] / histogram.sum()
            entropy = float(-np.sum(probabilities * np.log2(probabilities)))
        else:
            brightness = float(np.mean(gray))
            contrast = 0.0
            sharpness = 0.0
            edge_density = 0.0
            entropy = 0.0

        motion = self._global_motion(gray)
        blur_drop = 0.0
        if self._previous_sharpness and self._previous_sharpness > 0:
            blur_drop = max(0.0, (self._previous_sharpness - sharpness) / self._previous_sharpness)
        self._previous_sharpness = sharpness
        return {
            'brightness': brightness,
            'raw_brightness': float(np.mean(gray)),
            'contrast': contrast,
            'sharpness': sharpness,
            'edge_density': edge_density,
            'entropy': entropy,
            'valid_ratio': valid_ratio,
            'scene_change': self._scene_change(edges),
            'global_motion': motion['magnitude'],
            'motion_dx': motion['dx'],
            'motion_dy': motion['dy'],
            'motion_coherence': motion['coherence'],
            'tracked_points': motion['tracked_points'],
            'blur_drop': blur_drop,
        }

    def _global_motion(self, gray):
        result = {
            'magnitude': 0.0,
            'dx': 0.0,
            'dy': 0.0,
            'coherence': 0.0,
            'tracked_points': 0,
        }
        previous = self._previous_gray
        self._previous_gray = gray.copy()
        if previous is None:
            return result

        points = cv2.goodFeaturesToTrack(
            previous,
            maxCorners=160,
            qualityLevel=0.01,
            minDistance=7,
            blockSize=7,
        )
        if points is None or len(points) < 12:
            return result

        next_points, status, _ = cv2.calcOpticalFlowPyrLK(
            previous,
            gray,
            points,
            None,
            winSize=(21, 21),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
        )
        if next_points is None or status is None:
            return result

        valid = status.reshape(-1) == 1
        old = points.reshape(-1, 2)[valid]
        new = next_points.reshape(-1, 2)[valid]
        if len(old) < 12:
            return result

        vectors = new - old
        median_vector = np.median(vectors, axis=0)
        residuals = np.linalg.norm(vectors - median_vector, axis=1)
        magnitude = float(np.linalg.norm(median_vector))
        tolerance = max(2.0, magnitude * 0.35)
        coherence = float(np.mean(residuals <= tolerance))
        return {
            'magnitude': magnitude,
            'dx': float(median_vector[0]),
            'dy': float(median_vector[1]),
            'coherence': coherence,
            'tracked_points': int(len(old)),
        }

    def _detect_impact(self, metrics):
        vector = np.array([metrics['motion_dx'], metrics['motion_dy']], dtype=np.float32)
        magnitude = metrics['global_motion']
        enough_points = metrics['tracked_points'] >= self.impact_min_tracked_points
        coherent = metrics['motion_coherence'] >= self.impact_coherence_threshold
        stable_scene = metrics['scene_change'] <= self.impact_scene_change_limit
        strong_motion = (
            magnitude >= self.impact_motion_threshold
            and coherent
            and enough_points
            and stable_scene
        )
        reversed_motion = False
        previous_magnitude = 0.0

        if self._motion_history:
            previous_magnitude = float(np.linalg.norm(self._motion_history[-1]))

        if strong_motion:
            for previous in self._motion_history:
                previous_magnitude = float(np.linalg.norm(previous))
                if previous_magnitude < self.impact_motion_threshold:
                    continue
                cosine = float(
                    np.dot(previous, vector) / max(previous_magnitude * magnitude, 1e-6)
                )
                if cosine <= self.impact_reversal_cosine:
                    reversed_motion = True
                    break

        sudden_motion = (
            strong_motion
            and magnitude >= self.impact_motion_threshold * self.impact_sudden_multiplier
            and previous_magnitude < self.impact_motion_threshold * 0.35
        )
        blur_impact = strong_motion and metrics['blur_drop'] >= self.impact_blur_drop_threshold
        impact_score = (2 if reversed_motion else 0) + int(sudden_motion) + int(blur_impact)
        self._motion_history.append(vector if strong_motion else np.zeros(2, dtype=np.float32))
        return impact_score >= 2, {
            'impact_score': impact_score,
            'impact_reversal': reversed_motion,
            'impact_sudden_motion': sudden_motion,
            'impact_blur': blur_impact,
        }

    def _scene_change(self, edges):
        if self._baseline is None:
            return 0.0
        difference = np.abs(edges.astype(np.float32) - self._baseline)
        return float(np.mean(difference) / 255.0)

    def _classify(self, metrics):
        if metrics['raw_brightness'] <= 18 or metrics['valid_ratio'] <= 0.08:
            return BLOCKED
        low_texture_signals = sum((
            metrics['contrast'] <= 18,
            metrics['sharpness'] <= 30,
            metrics['edge_density'] <= 0.008,
            metrics['entropy'] <= 3.5,
        ))
        # Bright, uniform end cards and exposure fades are common in test
        # videos. Treating every such frame as a covered lens causes fire
        # videos to be mislabeled as LENS BLOCKED.
        if low_texture_signals >= 2 and metrics['raw_brightness'] <= 200:
            return BLOCKED
        if metrics['sharpness'] <= 20:
            return BLURRED
        if metrics.get('impact_signal'):
            return IMPACT
        if metrics['scene_change'] >= 0.16:
            return MOVED
        return NORMAL

    def _learn_baseline(self, gray):
        edges = cv2.Canny(gray, 50, 150).astype(np.float32)
        if self._baseline is None:
            self._baseline = edges
        else:
            self._baseline = (self._baseline * self._baseline_count + edges) / (self._baseline_count + 1)
        self._baseline_count += 1
        if self._baseline_count > self.baseline_frames:
            self._baseline_count = self.baseline_frames

    def _update_baseline(self, gray):
        if self._baseline is None:
            return
        edges = cv2.Canny(gray, 50, 150).astype(np.float32)
        self._baseline = self._baseline * 0.995 + edges * 0.005
