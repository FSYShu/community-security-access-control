"""
禁区距离检测SSE事件流
基于近大远小原理，通过人脸在画面中的大小估算距离，实时推送距离数据到前端
"""
import json
import logging
import threading
import time

import cv2
import numpy as np

from core.rtmp_relay import start_rtmp_pull, read_cv2_frame_from_pull, stop_rtmp_pull
from core.shared_frame_store import get_frame as _get_shared_frame

logger = logging.getLogger(__name__)

DETECT_INTERVAL = 2.0
DETECT_WIDTH = 320

REFERENCE_FACE_HEIGHT_RATIO = 0.35
REFERENCE_DISTANCE = 1.0


def _estimate_face_distance(face_rect, frame_height, calib_near_dist=None, calib_near_ratio=None, calib_far_dist=None, calib_far_ratio=None):
    x1, y1, x2, y2 = face_rect
    face_pixel_height = y2 - y1
    if face_pixel_height <= 0 or frame_height <= 0:
        return float('inf')
    height_ratio = face_pixel_height / frame_height
    if height_ratio <= 0:
        return float('inf')
    inv_ratio = 1.0 / height_ratio
    if calib_near_dist and calib_near_ratio and calib_far_dist and calib_far_ratio and calib_near_ratio > 0 and calib_far_ratio > 0:
        inv_near = 1.0 / calib_near_ratio
        inv_far = 1.0 / calib_far_ratio
        if abs(inv_far - inv_near) < 1e-9:
            distance = calib_near_dist
        else:
            a = (calib_far_dist - calib_near_dist) / (inv_far - inv_near)
            b = calib_near_dist - a * inv_near
            distance = a * inv_ratio + b
    elif calib_near_dist and calib_near_ratio and calib_near_ratio > 0:
        distance = calib_near_dist * calib_near_ratio / height_ratio
    else:
        distance = REFERENCE_DISTANCE * REFERENCE_FACE_HEIGHT_RATIO / height_ratio
    return round(distance, 2)


def generate_danger_distance_sse(stream_url, zones, fps=20, max_width=640, detect_width=320, calib_near_dist=None, calib_near_ratio=None, calib_far_dist=None, calib_far_ratio=None):
    yield 'event: connected\ndata: {}\n\n'.format(json.dumps({}))

    own_pull = False
    entry = None
    slot = {'alive': True}

    for _ in range(6):
        if _get_shared_frame(stream_url) is not None:
            break
        time.sleep(0.5)
    else:
        entry = start_rtmp_pull(stream_url, fps=fps, max_width=max_width)
        if entry is not None:
            own_pull = True

    safety_distance = min((z.safety_distance for z in zones if z.safety_distance), default=2.0)

    try:
        from core.face_recognition import FaceRecognizer
        recognizer = FaceRecognizer()
    except Exception as e:
        logger.error('FaceRecognizer init failed: {}'.format(str(e)))
        return

    detection_state = {
        'persons': [],
        'frame_width': 0,
        'frame_height': 0,
        'safety_distance': safety_distance,
        'lock': threading.Lock(),
        'last_time': 0.0,
    }

    def detector():
        while slot['alive']:
            now = time.time()
            elapsed = now - detection_state['last_time']
            if elapsed < DETECT_INTERVAL:
                time.sleep(DETECT_INTERVAL - elapsed)
                continue

            frame = None
            if own_pull and entry is not None:
                if entry['process'].poll() is None:
                    ok, f = read_cv2_frame_from_pull(entry)
                    if ok and f is not None:
                        frame = f
            else:
                jpeg = _get_shared_frame(stream_url)
                if jpeg is not None:
                    arr = np.frombuffer(jpeg, dtype=np.uint8).copy()
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

            if frame is None:
                time.sleep(0.5)
                continue

            try:
                h, w = frame.shape[:2]

                detect_scale = 1.0
                if w > detect_width:
                    detect_scale = detect_width / w
                    detect_frame = cv2.resize(frame, (detect_width, int(h * detect_scale)),
                                              interpolation=cv2.INTER_NEAREST)
                else:
                    detect_frame = frame

                rgb_image = np.ascontiguousarray(detect_frame[:, :, ::-1])
                faces = recognizer.detect_faces_rgb(rgb_image)
                persons = []
                for face_rect in faces:
                    if detect_scale != 1.0:
                        x1, y1, x2, y2 = face_rect
                        face_rect = (int(x1 / detect_scale), int(y1 / detect_scale),
                                     int(x2 / detect_scale), int(y2 / detect_scale))
                    dist = _estimate_face_distance(face_rect, h, calib_near_dist, calib_near_ratio, calib_far_dist, calib_far_ratio)
                    is_close = dist <= safety_distance
                    persons.append({
                        'rect': list(face_rect),
                        'distance': dist,
                        'is_close': is_close,
                    })

                with detection_state['lock']:
                    detection_state['persons'] = persons
                    detection_state['frame_width'] = w
                    detection_state['frame_height'] = h
                    detection_state['last_time'] = time.time()
            except Exception as e:
                logger.error('Danger distance detection error: {}'.format(str(e)))
                with detection_state['lock']:
                    detection_state['last_time'] = time.time()

    detector_thread = threading.Thread(target=detector, daemon=True)
    detector_thread.start()

    try:
        time.sleep(0.5)
        while slot['alive']:
            with detection_state['lock']:
                persons = list(detection_state['persons'])
                frame_w = detection_state['frame_width']
                frame_h = detection_state['frame_height']
                s_dist = detection_state['safety_distance']

            data = json.dumps({
                'persons': persons,
                'frame_width': frame_w,
                'frame_height': frame_h,
                'safety_distance': s_dist,
            })

            yield 'event: detection\ndata: {}\n\n'.format(data)

            time.sleep(1.0)
    finally:
        slot['alive'] = False
        if own_pull and entry is not None:
            stop_rtmp_pull(stream_url)
