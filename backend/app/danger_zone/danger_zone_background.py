"""
禁区入侵后台检测服务
持续监控所有活跃禁区关联的摄像头，自动检测人员并触发告警
使用cv2.VideoCapture独立拉流，避免与前端视频流共享FFmpeg stdout导致冲突
"""
import logging
import threading
import time

import cv2

from flask import current_app

from app import db
from app.models.danger_zone import DangerZone
from app.models.gate import Gate
from app.danger_zone.danger_zone_detector import process_frame_for_zone

logger = logging.getLogger(__name__)

_detect_thread = None
_detect_stop_event = threading.Event()
DETECT_LOOP_INTERVAL = 2.0
MAX_WIDTH = 480
_capture_entries = {}
_CAPTURE_OPEN_TIMEOUT = 45
_CAPTURE_RECONNECT_INTERVAL = 5


def start_danger_zone_detector(app):
    global _detect_thread
    if _detect_thread is not None and _detect_thread.is_alive():
        logger.info('Danger zone detector already running')
        return

    _detect_stop_event.clear()

    def delayed_start():
        global _detect_thread
        time.sleep(5)
        if _detect_stop_event.is_set():
            return
        _detect_stop_event.clear()
        _detect_thread = threading.Thread(
            target=_detection_loop,
            args=(app,),
            daemon=True,
            name='danger-zone-detector'
        )
        _detect_thread.start()
        logger.info('Danger zone detector started')

    t = threading.Thread(target=delayed_start, daemon=True)
    t.start()
    logger.info('Danger zone detector scheduled to start in 5s')


def stop_danger_zone_detector():
    _detect_stop_event.set()
    for url, cap in list(_capture_entries.items()):
        try:
            cap.release()
        except Exception:
            pass
    _capture_entries.clear()
    logger.info('Danger zone detector stopping...')


def _get_rtmp_url(push_key):
    config = current_app.config
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    return 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, push_key)


def _open_capture_with_timeout(stream_url, timeout=_CAPTURE_OPEN_TIMEOUT):
    result = {'cap': None}
    finished = threading.Event()
    abandoned = threading.Event()

    def try_open():
        cap = None
        try:
            candidate = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
            if candidate.isOpened():
                cap = candidate
            else:
                candidate.release()
        except Exception:
            logger.exception('Failed to open RTMP stream: %s', stream_url)

        if abandoned.is_set():
            if cap is not None:
                cap.release()
        else:
            result['cap'] = cap
        finished.set()

    threading.Thread(target=try_open, daemon=True).start()
    if not finished.wait(timeout=timeout):
        abandoned.set()
        logger.warning('Timed out opening RTMP stream: %s', stream_url)
        return None
    return result['cap']


def _get_capture(rtmp_url):
    if rtmp_url in _capture_entries:
        cap = _capture_entries[rtmp_url]
        if cap is not None and cap.isOpened():
            return cap
        try:
            cap.release()
        except Exception:
            pass
        del _capture_entries[rtmp_url]

    cap = _open_capture_with_timeout(rtmp_url)
    if cap is not None:
        _capture_entries[rtmp_url] = cap
    return cap


def _detection_loop(app):
    while not _detect_stop_event.is_set():
        try:
            with app.app_context():
                _run_detection_cycle()
        except Exception as e:
            logger.error('Detection cycle error: {}'.format(str(e)))

        _detect_stop_event.wait(DETECT_LOOP_INTERVAL)


def _run_detection_cycle():
    zones = DangerZone.query.filter_by(status='active').all()
    if not zones:
        return

    for zone in zones:
        if _detect_stop_event.is_set():
            return

        camera_ids_str = zone.camera_ids
        if not camera_ids_str:
            continue

        gate_ids = [int(x.strip()) for x in camera_ids_str.split(',') if x.strip().isdigit()]
        if not gate_ids:
            continue

        for gate_id in gate_ids:
            if _detect_stop_event.is_set():
                return

            try:
                gate = Gate.query.get(gate_id)
            except Exception:
                db.session.rollback()
                continue

            if not gate or not gate.push_key:
                logger.info('Zone {} gate {} has no push_key'.format(zone.id, gate_id))
                continue

            rtmp_url = _get_rtmp_url(gate.push_key)
            cap = _get_capture(rtmp_url)
            if cap is None:
                logger.info('Zone {} gate {} cannot open RTMP capture'.format(zone.id, gate_id))
                continue

            ok, frame = cap.read()
            if not ok or frame is None:
                logger.info('Zone {} gate {} no frame from capture, will reconnect'.format(zone.id, gate_id))
                try:
                    cap.release()
                except Exception:
                    pass
                _capture_entries.pop(rtmp_url, None)
                continue

            logger.info('Zone {} gate {} got frame {}x{} from RTMP'.format(zone.id, gate_id, frame.shape[1], frame.shape[0]))

            try:
                result = process_frame_for_zone(zone.id, frame, gate_id=gate_id)
                if result:
                    logger.info('Alarm triggered for zone {}: {}'.format(zone.id, result.alarm_description))
            except Exception as e:
                logger.error('Error processing zone {} gate {}: {}'.format(zone.id, gate_id, str(e)))
