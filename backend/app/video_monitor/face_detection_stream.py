import json
import logging
import threading
import time


import cv2
import numpy as np
from flask import Response, current_app

from core.face_recognition import FaceRecognizer, load_registered_faces
from core.rtmp_relay import start_rtmp_pull, read_cv2_frame_from_pull, stop_rtmp_pull, get_push_latency_ms

logger = logging.getLogger(__name__)

DETECT_INTERVAL = 2.0
DETECT_WIDTH = 160
BUFFER_DELAY_SECONDS = 5.0


def _extract_push_key_from_url(stream_url):
    parts = stream_url.rstrip('/').split('/')
    return parts[-1] if parts else ''


def _overlay_latency_on_frame(frame, latency_ms):
    if latency_ms < 0:
        return frame
    if latency_ms > 2000:
        color = (0, 0, 255)
    elif latency_ms > 800:
        color = (0, 165, 255)
    else:
        color = (0, 200, 0)
    text = 'LATENCY: {}ms'.format(latency_ms)
    h, w = frame.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = max(0.4, min(w, h) / 800)
    thickness = max(1, int(scale * 2))
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    cv2.rectangle(frame, (8, h - th - 18), (8 + tw + 12, h - 6), (0, 0, 0), -1)
    cv2.putText(frame, text, (14, h - 14), font, scale, color, thickness, cv2.LINE_AA)
    return frame


def generate_frames_with_detection(stream_id):
    config = current_app.config
    rtmp_host = config.get('RTMP_SERVER_HOST', '127.0.0.1')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    stream_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, stream_id)
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    return generate_frames_with_detection_ffmpeg(stream_url, fps=10, max_width=max_width)


def generate_frames_with_detection_url(stream_url, frame_skip=5, max_width=640, detect_width=320, cap=None, first_frame=None):
    return generate_frames_with_detection_ffmpeg(stream_url, fps=10, max_width=max_width, detect_width=detect_width)


def generate_frames_with_detection_ffmpeg(stream_url, fps=10, max_width=640, detect_width=320):
    entry = start_rtmp_pull(stream_url, fps=fps, max_width=max_width)
    if entry is None:
        return

    push_key = _extract_push_key_from_url(stream_url)

    try:
        recognizer = FaceRecognizer()
    except Exception as e:
        logger.error('FaceRecognizer init failed: {}'.format(str(e)))
        stop_rtmp_pull(stream_url)
        return

    try:
        registered_faces = load_registered_faces()
    except Exception as e:
        logger.error('load_registered_faces failed: {}'.format(str(e)))
        registered_faces = []

    slot = {'frame': None, 'alive': True}

    detection_state = {
        'boxes': [],
        'lock': threading.Lock(),
        'last_time': 0.0,
    }

    def reader():
        while slot['alive']:
            if entry['process'].poll() is not None:
                break
            ok, f = read_cv2_frame_from_pull(entry)
            if not ok or f is None:
                time.sleep(0.01)
                continue
            slot['frame'] = f

    reader_thread = threading.Thread(target=reader, daemon=True)
    reader_thread.start()

    def detector():
        while slot['alive']:
            now = time.time()
            elapsed = now - detection_state['last_time']
            if elapsed < DETECT_INTERVAL:
                time.sleep(DETECT_INTERVAL - elapsed)
                continue

            frame = slot['frame']
            if frame is None:
                time.sleep(0.1)
                continue

            try:
                h, w = frame.shape[:2]
                if w > max_width:
                    scale = max_width / w
                    frame = cv2.resize(frame, (max_width, int(h * scale)), interpolation=cv2.INTER_LINEAR)

                detect_scale = 1.0
                if frame.shape[1] > DETECT_WIDTH:
                    detect_scale = DETECT_WIDTH / frame.shape[1]
                    detect_frame = cv2.resize(frame, (DETECT_WIDTH, int(frame.shape[0] * detect_scale)),
                                              interpolation=cv2.INTER_NEAREST)
                else:
                    detect_frame = frame

                rgb_image = np.ascontiguousarray(detect_frame[:, :, ::-1])
                faces = recognizer.detect_faces_rgb(rgb_image)
                boxes = []
                for face_rect in faces:
                    face_descriptor = recognizer.compute_face_descriptor_rgb(rgb_image, face_rect)
                    matched_name, matched_id, distance = recognizer.compare_faces(
                        face_descriptor, registered_faces, tolerance=0.4
                    )
                    if detect_scale != 1.0:
                        x1, y1, x2, y2 = face_rect
                        face_rect = (int(x1 / detect_scale), int(y1 / detect_scale),
                                     int(x2 / detect_scale), int(y2 / detect_scale))
                    boxes.append({
                        'rect': face_rect,
                        'name': matched_name,
                        'is_stranger': matched_name == '陌生人',
                    })
                with detection_state['lock']:
                    detection_state['boxes'] = boxes
                    detection_state['last_time'] = time.time()
            except Exception as e:
                logger.error('Face detection error: {}'.format(str(e)))
                with detection_state['lock']:
                    detection_state['last_time'] = time.time()

    detector_thread = threading.Thread(target=detector, daemon=True)
    detector_thread.start()


    try:
        while slot['alive']:
            frame = slot['frame']
            if frame is None:
                time.sleep(0.01)
                continue

            h, w = frame.shape[:2]
            if w > max_width:
                scale = max_width / w
                frame = cv2.resize(frame, (max_width, int(h * scale)), interpolation=cv2.INTER_LINEAR)

            with detection_state['lock']:
                boxes = list(detection_state['boxes'])

            for box in boxes:
                x1, y1, x2, y2 = box['rect']
                if box['is_stranger']:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, '陌生人', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, box['name'], (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

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
    finally:
        slot['alive'] = False
        stop_rtmp_pull(stream_url)


def generate_detection_sse(stream_url, fps=10, max_width=640, detect_width=320):
    """生成人脸检测SSE事件流，优先从共享帧存储读取，否则启动独立RTMP拉流"""
    from core.shared_frame_store import get_frame as _get_shared_frame

    yield 'event: connected\ndata: {}\n\n'.format(json.dumps({}))

    own_pull = False
    entry = None
    slot = {'alive': True}

    for _ in range(10):
        if _get_shared_frame(stream_url) is not None:
            break
        time.sleep(0.5)
    else:
        entry = start_rtmp_pull(stream_url, fps=fps, max_width=max_width)
        if entry is not None:
            own_pull = True

    detection_state = {
        'boxes': [],
        'frame_width': 0,
        'frame_height': 0,
        'lock': threading.Lock(),
        'last_time': 0.0,
    }

    def detector():
        try:
            recognizer = FaceRecognizer()
        except Exception as e:
            logger.error('FaceRecognizer init failed: {}'.format(str(e)))
            with detection_state['lock']:
                detection_state['last_time'] = time.time()
            return
        try:
            registered_faces = load_registered_faces()
        except Exception as e:
            logger.error('load_registered_faces failed: {}'.format(str(e)))
            registered_faces = []

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
                boxes = []
                for face_rect in faces:
                    face_descriptor = recognizer.compute_face_descriptor_rgb(rgb_image, face_rect)
                    matched_name, matched_id, distance = recognizer.compare_faces(
                        face_descriptor, registered_faces, tolerance=0.4
                    )
                    if detect_scale != 1.0:
                        x1, y1, x2, y2 = face_rect
                        face_rect = (int(x1 / detect_scale), int(y1 / detect_scale),
                                     int(x2 / detect_scale), int(y2 / detect_scale))
                    boxes.append({
                        'rect': list(face_rect),
                        'name': matched_name,
                        'is_stranger': matched_name == '陌生人',
                    })
                with detection_state['lock']:
                    detection_state['boxes'] = boxes
                    detection_state['frame_width'] = w
                    detection_state['frame_height'] = h
                    detection_state['last_time'] = time.time()
            except Exception as e:
                logger.error('Face detection error: {}'.format(str(e)))
                with detection_state['lock']:
                    detection_state['last_time'] = time.time()

    detector_thread = threading.Thread(target=detector, daemon=True)
    detector_thread.start()


    try:
        time.sleep(0.5)
        while slot['alive']:
            with detection_state['lock']:
                boxes = list(detection_state['boxes'])
                frame_w = detection_state['frame_width']
                frame_h = detection_state['frame_height']

            data = json.dumps({
                'boxes': boxes,
                'frame_width': frame_w,
                'frame_height': frame_h,
            })

            yield 'event: detection\ndata: {}\n\n'.format(data)

            time.sleep(1.0)
    finally:
        slot['alive'] = False
        if own_pull and entry is not None:
            stop_rtmp_pull(stream_url)
