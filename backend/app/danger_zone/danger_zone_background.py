"""
禁区入侵后台检测服务
持续监控所有活跃禁区关联的摄像头，自动检测人员并触发告警
通过RTMP拉流获取视频帧，使用FFmpeg子进程解码
"""
import logging
import threading
import time

from flask import current_app

from app import db
from app.models.danger_zone import DangerZone
from app.models.gate import Gate
from app.danger_zone.danger_zone_detector import process_frame_for_zone
from core.rtmp_relay import start_rtmp_pull, read_cv2_frame_from_pull, stop_rtmp_pull

logger = logging.getLogger(__name__)

_detect_thread = None
_detect_stop_event = threading.Event()
DETECT_LOOP_INTERVAL = 2.0
MAX_WIDTH = 480
_pull_entries = {}


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
    for url, entry in list(_pull_entries.items()):
        try:
            stop_rtmp_pull(url)
        except Exception:
            pass
    _pull_entries.clear()
    logger.info('Danger zone detector stopping...')


def _get_rtmp_url(push_key):
    config = current_app.config
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    return 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, push_key)


def _get_pull_entry(rtmp_url):
    if rtmp_url in _pull_entries:
        entry = _pull_entries[rtmp_url]
        if entry and entry['process'].poll() is None:
            return entry
        try:
            stop_rtmp_pull(rtmp_url)
        except Exception:
            pass
        del _pull_entries[rtmp_url]

    entry = start_rtmp_pull(rtmp_url, fps=5, max_width=MAX_WIDTH)
    if entry is not None:
        _pull_entries[rtmp_url] = entry
    return entry


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
            entry = _get_pull_entry(rtmp_url)
            if entry is None:
                logger.info('Zone {} gate {} cannot start RTMP pull'.format(zone.id, gate_id))
                continue

            ok, frame = read_cv2_frame_from_pull(entry)
            if not ok or frame is None:
                logger.info('Zone {} gate {} no frame from RTMP pull'.format(zone.id, gate_id))
                continue

            logger.info('Zone {} gate {} got frame {}x{} from RTMP'.format(zone.id, gate_id, frame.shape[1], frame.shape[0]))

            try:
                result = process_frame_for_zone(zone.id, frame, gate_id=gate_id)
                if result:
                    logger.info('Alarm triggered for zone {}: {}'.format(zone.id, result.alarm_description))
            except Exception as e:
                logger.error('Error processing zone {} gate {}: {}'.format(zone.id, gate_id, str(e)))
