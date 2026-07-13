"""
禁区入侵检测MJPEG视频流
从RTMP拉取视频流（FFmpeg），叠加人员检测结果和禁区标注
"""
import logging
import threading
import time

import cv2

from core.rtmp_relay import start_rtmp_pull, read_cv2_frame_from_pull, stop_rtmp_pull

logger = logging.getLogger(__name__)

DETECT_INTERVAL = 1.5
MAX_WIDTH = 640


def generate_frames_with_danger_detect(stream_url, zones, max_width=640):
    entry = start_rtmp_pull(stream_url, fps=10, max_width=max_width)
    if entry is None:
        return

    latest = {
        'frame': None,
        'lock': threading.Lock(),
        'alive': True,
    }

    detection_state = {
        'persons': [],
        'lock': threading.Lock(),
        'last_time': 0.0,
    }

    def reader():
        while latest['alive']:
            if entry['process'].poll() is not None:
                latest['alive'] = False
                break
            ok, f = read_cv2_frame_from_pull(entry)
            if not ok or f is None:
                time.sleep(0.01)
                continue
            with latest['lock']:
                latest['frame'] = f

    reader_thread = threading.Thread(target=reader, daemon=True)
    reader_thread.start()

    def detector():
        while latest['alive']:
            now = time.time()
            elapsed = now - detection_state['last_time']
            if elapsed < DETECT_INTERVAL:
                time.sleep(DETECT_INTERVAL - elapsed)
                continue

            with latest['lock']:
                frame = latest['frame']
            if frame is None:
                time.sleep(0.1)
                continue

            try:
                h, w = frame.shape[:2]
                if w > max_width:
                    scale = max_width / w
                    frame = cv2.resize(frame, (max_width, int(h * scale)),
                                       interpolation=cv2.INTER_LINEAR)

                from app.danger_zone.danger_zone_detector import _detect_persons
                persons = _detect_persons(frame)
                with detection_state['lock']:
                    detection_state['persons'] = persons
                    detection_state['last_time'] = time.time()

                for zone in zones:
                    try:
                        from app.danger_zone.danger_zone_detector import process_frame_for_zone
                        process_frame_for_zone(zone.id, frame)
                    except Exception as e:
                        logger.error('Error processing zone {}: {}'.format(zone.id, str(e)))
            except Exception as e:
                logger.error('Detection error: {}'.format(str(e)))
                with detection_state['lock']:
                    detection_state['last_time'] = time.time()

    detector_thread = threading.Thread(target=detector, daemon=True)
    detector_thread.start()

    try:
        while latest['alive']:
            with latest['lock']:
                frame = latest['frame']
            if frame is None:
                time.sleep(0.01)
                continue

            h, w = frame.shape[:2]
            if w > max_width:
                scale = max_width / w
                frame = cv2.resize(frame, (max_width, int(h * scale)),
                                   interpolation=cv2.INTER_LINEAR)

            with detection_state['lock']:
                persons = list(detection_state['persons'])

            if persons:
                from app.danger_zone.danger_zone_detector import draw_detection_overlay
                min_safety = min((z.safety_distance for z in zones if z.safety_distance), default=None)
                frame = draw_detection_overlay(frame, persons, safety_distance=min_safety)

            for zone in zones:
                cv2.putText(frame, '[{}] DANGER ZONE'.format(zone.zone_name), (10, 30 + zones.index(zone) * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            ret, buffer = cv2.imencode(
                '.jpg', frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), 45]
            )
            if not ret:
                time.sleep(0.01)
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)
    finally:
        latest['alive'] = False
        stop_rtmp_pull(stream_url)