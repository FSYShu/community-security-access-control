import argparse
import json
import os
import sys

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.fire_smoke_detector import FireSmokeDetector
from core.tailgating_detector import MobileNetPersonDetector, TailgatingDetector


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('tailgating', 'fire-smoke'), required=True)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--prototxt')
    parser.add_argument('--model')
    parser.add_argument('--max-frames', type=int, default=0)
    args = parser.parse_args()

    capture = cv2.VideoCapture(args.input)
    if not capture.isOpened():
        raise SystemExit('Cannot open input video: ' + args.input)
    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
    events = []
    frame_index = 0

    if args.mode == 'tailgating':
        if not args.prototxt or not args.model:
            raise SystemExit('tailgating mode requires --prototxt and --model')
        object_detector = MobileNetPersonDetector(args.prototxt, args.model)
        event_detector = TailgatingDetector()
    else:
        event_detector = FireSmokeDetector()

    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if args.max_frames and frame_index >= args.max_frames:
            break
        timestamp = frame_index / fps
        if args.mode == 'tailgating':
            boxes = object_detector.detect(frame)
            result = event_detector.update(boxes, frame.shape, timestamp)
            line_y = int(height * event_detector.line_ratio)
            cv2.line(frame, (0, line_y), (width, line_y), (0, 255, 255), 2)
            for track_id, track in result.tracks.items():
                if track['missing']:
                    continue
                x1, y1, x2, y2 = track['box'][:4]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, 'ID {}'.format(track_id), (x1, max(20, y1 - 5)), 0, 0.6, (0, 255, 0), 2)
            if result.event:
                events.append({'time': timestamp, 'type': 'tailgating', 'track_ids': result.track_ids})
                cv2.putText(frame, 'TAILGATING', (20, 45), 0, 1.0, (0, 0, 255), 3)
        else:
            result = event_detector.analyze(frame)
            if result.fire or result.smoke:
                label = 'FIRE' if result.fire else 'SMOKE'
                cv2.putText(frame, label, (20, 45), 0, 1.0, (0, 0, 255), 3)
            if result.event:
                events.append({'time': timestamp, 'type': 'fire' if result.fire else 'smoke', **result.metrics})
        writer.write(frame)
        frame_index += 1

    capture.release()
    writer.release()
    with open(os.path.splitext(args.output)[0] + '.json', 'w', encoding='utf-8') as target:
        json.dump(events, target, ensure_ascii=False, indent=2)
    print(json.dumps({'frames': frame_index, 'events': len(events), 'output': args.output}, ensure_ascii=False))


if __name__ == '__main__':
    main()
