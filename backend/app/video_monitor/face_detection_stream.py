import logging
import threading
import time

import cv2
import numpy as np
from flask import Response, current_app

from core.face_recognition import FaceRecognizer, load_registered_faces

logger = logging.getLogger(__name__)

DETECT_INTERVAL = 2.0
DETECT_WIDTH = 160


def generate_frames_with_detection(stream_id):
    config = current_app.config
    rtmp_host = config.get('RTMP_SERVER_HOST', '127.0.0.1')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    stream_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, stream_id)
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    return _do_generate_frames_with_detection(stream_url, max_width)


def generate_frames_with_detection_url(stream_url, frame_skip=5, max_width=640, detect_width=320):
    return _do_generate_frames_with_detection(stream_url, max_width)


def _do_generate_frames_with_detection(stream_url, max_width=640):
    cap_result = {'cap': None, 'opened': False}
    cap_error = threading.Event()

    def try_open():
        try:
            cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
            cap_result['cap'] = cap
            cap_result['opened'] = cap.isOpened()
        except Exception:
            cap_result['opened'] = False
        cap_error.set()

    t = threading.Thread(target=try_open, daemon=True)
    t.start()
    placeholder_size = (max_width, int(max_width * 9 / 16))
    if not cap_error.wait(timeout=8):
        from . import _generate_placeholder
        placeholder = _generate_placeholder('RTMP连接超时', placeholder_size)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
        return

    if not cap_result['opened']:
        from . import _generate_placeholder
        placeholder = _generate_placeholder('RTMP连接失败', placeholder_size)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
        return

    cap = cap_result['cap']

    try:
        recognizer = FaceRecognizer()
    except Exception as e:
        logger.error('FaceRecognizer init failed: {}'.format(str(e)))
        cap.release()
        from . import _generate_placeholder
        placeholder = _generate_placeholder('人脸识别初始化失败', placeholder_size)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
        return

    try:
        registered_faces = load_registered_faces()
    except Exception as e:
        logger.error('load_registered_faces failed: {}'.format(str(e)))
        registered_faces = []

    latest = {
        'frame': None,
        'lock': threading.Lock(),
        'alive': True,
    }

    detection_state = {
        'boxes': [],
        'lock': threading.Lock(),
        'last_time': 0.0,
    }

    def reader():
        while latest['alive']:
            ok, f = cap.read()
            if not ok:
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
        while latest['alive']:
            with latest['lock']:
                frame = latest['frame']
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
            time.sleep(0.03)
    finally:
        latest['alive'] = False
        cap.release()
