"""Person tracking and gate-line tailgating detection."""

from dataclasses import dataclass
from math import hypot

import cv2
import numpy as np


PERSON_CLASS_ID = 15


class MobileNetPersonDetector:
    def __init__(self, prototxt_path, model_path, confidence=0.45,
                 nms_threshold=0.4):
        self.net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
        self.confidence = confidence
        self.nms_threshold = nms_threshold

    def detect(self, frame):
        height, width = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5
        )
        self.net.setInput(blob)
        detections = self.net.forward()
        boxes = []
        nms_boxes = []
        confidences = []
        for index in range(detections.shape[2]):
            confidence = float(detections[0, 0, index, 2])
            class_id = int(detections[0, 0, index, 1])
            if class_id != PERSON_CLASS_ID or confidence < self.confidence:
                continue
            x1, y1, x2, y2 = detections[0, 0, index, 3:7] * np.array(
                [width, height, width, height]
            )
            box = (
                max(0, int(x1)), max(0, int(y1)),
                min(width - 1, int(x2)), min(height - 1, int(y2)),
                confidence,
            )
            boxes.append(box)
            nms_boxes.append([
                box[0], box[1], box[2] - box[0], box[3] - box[1]
            ])
            confidences.append(confidence)

        if not boxes:
            return []
        indices = cv2.dnn.NMSBoxes(
            nms_boxes, confidences, self.confidence, self.nms_threshold
        )
        return [boxes[int(index)] for index in np.array(indices).reshape(-1)]


class CentroidTracker:
    def __init__(self, max_distance=140, max_missing=15):
        self.max_distance = max_distance
        self.max_missing = max_missing
        self.next_id = 1
        self.tracks = {}

    def update(self, boxes):
        detections = []
        for box in boxes:
            x1, y1, x2, y2 = box[:4]
            detections.append(((x1 + x2) / 2.0, (y1 + y2) / 2.0, box))

        unmatched = set(range(len(detections)))
        for track_id, track in list(self.tracks.items()):
            best_index = None
            best_distance = self.max_distance
            for index in unmatched:
                cx, cy, _ = detections[index]
                distance = hypot(cx - track['centroid'][0], cy - track['centroid'][1])
                if distance < best_distance:
                    best_distance = distance
                    best_index = index
            if best_index is None:
                track['missing'] += 1
                if track['missing'] > self.max_missing:
                    self.tracks.pop(track_id, None)
                continue
            cx, cy, box = detections[best_index]
            unmatched.remove(best_index)
            track['previous'] = track['centroid']
            track['centroid'] = (cx, cy)
            track['box'] = box
            track['missing'] = 0

        for index in unmatched:
            cx, cy, box = detections[index]
            self.tracks[self.next_id] = {
                'centroid': (cx, cy), 'previous': (cx, cy),
                'box': box, 'missing': 0, 'crossed': False,
            }
            self.next_id += 1
        return self.tracks


@dataclass
class TailgatingResult:
    event: bool
    track_ids: list
    crossing_count: int
    tracks: dict


class TailgatingDetector:
    def __init__(self, line_ratio=0.62, crossing_window=5.0,
                 max_horizontal_gap_ratio=0.28, authorized_entries=1,
                 direction='down'):
        self.line_ratio = line_ratio
        self.crossing_window = crossing_window
        self.max_horizontal_gap_ratio = max_horizontal_gap_ratio
        self.authorized_entries = authorized_entries
        if direction not in ('down', 'up', 'both'):
            raise ValueError('direction must be down, up, or both')
        self.direction = direction
        self.tracker = CentroidTracker()
        self.crossings = []
        self.reported_pairs = set()

    def reset(self):
        """Clear tracks when the unified stream is in another danger state."""
        self.tracker = CentroidTracker()
        self.crossings.clear()
        self.reported_pairs.clear()

    def update(self, boxes, frame_shape, timestamp):
        height, width = frame_shape[:2]
        line_y = height * self.line_ratio
        tracks = self.tracker.update(boxes)
        for track_id, track in tracks.items():
            if track['missing'] or track['crossed']:
                continue
            previous_y = track['previous'][1]
            current_y = track['centroid'][1]
            x1, y1, x2, y2 = track['box'][:4]
            track['seen_above'] = track.get('seen_above', False) or current_y < line_y
            track['seen_below'] = track.get('seen_below', False) or current_y > line_y
            moving_down = current_y > previous_y + 1
            moving_up = current_y < previous_y - 1
            crossed_down = (
                previous_y < line_y <= current_y
                or (track['seen_above'] and y2 >= line_y and moving_down)
            )
            crossed_up = (
                previous_y > line_y >= current_y
                or (track['seen_below'] and y1 <= line_y and moving_up)
            )
            if (
                (self.direction in ('down', 'both') and crossed_down)
                or (self.direction in ('up', 'both') and crossed_up)
            ):
                track['crossed'] = True
                self.crossings.append({
                    'id': track_id,
                    'time': timestamp,
                    'x': track['centroid'][0],
                })

        self.crossings = [
            item for item in self.crossings
            if timestamp - item['time'] <= self.crossing_window
        ]
        event_ids = []
        if len(self.crossings) > self.authorized_entries:
            recent = sorted(self.crossings, key=lambda item: item['time'])
            for first in recent:
                for second in recent:
                    if first['id'] >= second['id']:
                        continue
                    close_in_space = abs(first['x'] - second['x']) <= width * self.max_horizontal_gap_ratio
                    close_in_time = abs(first['time'] - second['time']) <= self.crossing_window
                    pair = (first['id'], second['id'])
                    if close_in_space and close_in_time and pair not in self.reported_pairs:
                        self.reported_pairs.add(pair)
                        event_ids = [first['id'], second['id']]
                        break
                if event_ids:
                    break

        return TailgatingResult(
            event=bool(event_ids),
            track_ids=event_ids,
            crossing_count=len(self.crossings),
            tracks=tracks,
        )
