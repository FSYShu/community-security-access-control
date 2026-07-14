"""
视频监控模块蓝图
提供RTMP视频流拉取、MJPEG转发、历史视频回放等接口
"""
import logging
import re
import time
import base64
import threading
from collections import deque

from datetime import datetime, timezone, timedelta

import cv2
import numpy as np
import requests as http_requests
from flask import Blueprint, Response, jsonify, current_app, request as flask_request
from flask_jwt_extended import jwt_required, get_jwt

from app import limiter
from app import db
from app.models.gate import Gate
from utils import error_response
from utils.response import success_response

_CST = timezone(timedelta(hours=8))
from core.audit_logger import log_audit
from core.rtmp_relay import start_rtmp_pull, read_jpeg_frame_from_pull, stop_rtmp_pull, get_push_latency_ms
from core.shared_frame_store import update_frame as _update_shared_frame

video_monitor_bp = Blueprint('video_monitor', __name__)

logger = logging.getLogger(__name__)


def _try_connect_rtmp_ffmpeg(stream_url, fps=20, max_width=640, timeout=10):
    entry = start_rtmp_pull(stream_url, fps=fps, max_width=max_width)
    if entry is None:
        return None
    return entry


def _extract_push_key_from_url(stream_url):
    parts = stream_url.rstrip('/').split('/')
    return parts[-1] if parts else ''



def generate_frames_ffmpeg(stream_url, fps=20, max_width=640):
    entry = _try_connect_rtmp_ffmpeg(stream_url, fps=fps, max_width=max_width)
    if entry is None:
        return

    push_key = _extract_push_key_from_url(stream_url)

    buf = deque(maxlen=10)
    buf_lock = threading.Lock()
    buf_event = threading.Event()
    alive = {'flag': True}

    def reader():
        while alive['flag']:
            if entry['process'].poll() is not None:
                alive['flag'] = False
                buf_event.set()
                break
            jpeg = read_jpeg_frame_from_pull(entry)
            if jpeg is None:
                alive['flag'] = False
                buf_event.set()
                break
            with buf_lock:
                buf.append(jpeg)
                _update_shared_frame(stream_url, jpeg)
            buf_event.set()

    reader_thread = threading.Thread(target=reader, daemon=True)
    reader_thread.start()

    try:
        while alive['flag']:
            with buf_lock:
                frames = list(buf)
                buf.clear()
            if not frames:
                buf_event.clear()
                buf_event.wait(timeout=0.1)
                with buf_lock:
                    frames = list(buf)
                    buf.clear()
                if not frames:
                    if not alive['flag']:
                        break
                    continue
            buf_event.clear()

            for jpeg in frames:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n')
    except GeneratorExit:
        pass
    finally:
        alive['flag'] = False
        stop_rtmp_pull(stream_url)



@video_monitor_bp.route('/gate-push-frame', methods=['POST'])
@limiter.exempt
def gate_push_frame():
    """接收门禁端JPEG帧，通过FFmpeg推流到RTMP服务器"""
    data = flask_request.get_json(force=True, silent=True)
    if not data or not data.get('push_key') or not data.get('frame'):
        return jsonify({'error': '缺少push_key或frame参数'}), 400
    push_key = data['push_key']
    try:
        jpeg_bytes = base64.b64decode(data['frame'])
    except Exception:
        return jsonify({'error': 'frame解码失败'}), 400
    ts_ms = data.get('ts')
    if ts_ms:
        from core.rtmp_relay import update_push_timestamp
        update_push_timestamp(push_key, int(ts_ms))
    config = current_app.config
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    rtmp_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, push_key)
    from core.rtmp_relay import push_jpeg_frame
    push_jpeg_frame(push_key, jpeg_bytes, rtmp_url)
    gate = Gate.query.filter_by(push_key=push_key).first()
    if gate:
        gate.last_heartbeat = datetime.now(_CST).isoformat()
        gate.status = 'online'
        db.session.commit()
    return jsonify({'code': 0, 'message': 'ok'})


@video_monitor_bp.route('/gate-latency/<push_key>', methods=['GET'])
@limiter.exempt
def gate_latency(push_key):
    from core.rtmp_relay import get_push_latency_ms, get_pull_fps
    latency = get_push_latency_ms(push_key)
    config = current_app.config
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    rtmp_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, push_key)
    fps = get_pull_fps(rtmp_url)
    return jsonify({'code': 0, 'data': {'push_key': push_key, 'latency_ms': latency, 'fps': fps}})


@video_monitor_bp.route('/pull-processes', methods=['GET'])
@jwt_required()
def get_pull_processes():
    """获取所有拉流进程状态，用于监控和调试"""
    from core.rtmp_relay import get_all_pull_processes
    processes = get_all_pull_processes()
    return jsonify({'code': 0, 'data': {'processes': processes, 'count': len(processes)}})


@video_monitor_bp.route('/gate-warmup/gate/<int:gate_id>', methods=['GET', 'POST'])
def gate_warmup_by_gate(gate_id):
    from app.models.gate import Gate
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'code': -1, 'message': '门禁终端不存在或未绑定推流码'}), 404
    config = current_app.config
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    rtmp_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, gate.push_key)
    fps = config.get('VIDEO_FPS', 20)
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    entry = start_rtmp_pull(rtmp_url, fps=fps, max_width=max_width)
    if entry is None:
        return jsonify({'code': -1, 'message': 'warmup failed'})
    return jsonify({'code': 0, 'message': 'warmup started'})


@video_monitor_bp.route('/gate-warmup/<push_key>', methods=['POST'])
def gate_warmup(push_key):
    config = current_app.config
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    rtmp_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, push_key)
    fps = config.get('VIDEO_FPS', 20)
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    entry = start_rtmp_pull(rtmp_url, fps=fps, max_width=max_width)
    if entry is None:
        return jsonify({'code': -1, 'message': 'warmup failed'})
    return jsonify({'code': 0, 'message': 'warmup started'})


def _mjpeg_response(generator):
    resp = Response(generator, mimetype='multipart/x-mixed-replace; boundary=frame')
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['X-Accel-Buffering'] = 'no'
    resp.headers['Connection'] = 'keep-alive'
    return resp


@video_monitor_bp.route('/video_feed/<stream_id>')
@limiter.exempt
def video_feed(stream_id):
    """获取MJPEG视频流（通过stream_id拼接RTMP地址，FFmpeg拉流）"""
    config = current_app.config
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    stream_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, stream_id)
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    fps = config.get('VIDEO_FPS', 20)
    try:
        return _mjpeg_response(
            generate_frames_ffmpeg(stream_url, fps=fps, max_width=max_width)
        )
    except Exception as e:
        logger.error('Failed to stream video for ID {}: {}'.format(stream_id, str(e)))
        return jsonify({'error': 'Failed to process video stream'}), 500


@video_monitor_bp.route('/video_feed/gate/<int:gate_id>')
@limiter.exempt
def video_feed_by_gate(gate_id):
    """获取门禁终端的MJPEG视频流（FFmpeg从RTMP拉取）"""
    from app.models.gate import Gate
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': '门禁终端不存在或未绑定推流码'}), 404
    config = current_app.config
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    stream_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, gate.push_key)
    fps = config.get('VIDEO_FPS', 20)
    try:
        return _mjpeg_response(
            generate_frames_ffmpeg(stream_url, fps=fps, max_width=max_width)
        )
    except Exception as e:
        logger.error('Failed to stream video for gate {}: {}'.format(gate_id, str(e)))
        return jsonify({'error': 'Failed to process video stream'}), 500


@video_monitor_bp.route('/video_feed/gate/<int:gate_id>/detect')
@limiter.exempt
def video_feed_by_gate_with_detection(gate_id):
    """获取门禁终端带人脸检测标注的MJPEG视频流（FFmpeg从RTMP拉取）"""
    from app.models.gate import Gate
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': '门禁终端不存在或未绑定推流码'}), 404
    config = current_app.config
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    stream_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, gate.push_key)
    fps = config.get('VIDEO_FPS', 20)
    detect_width = config.get('VIDEO_DETECT_WIDTH', 320)
    try:
        from .face_detection_stream import generate_frames_with_detection_ffmpeg
        return _mjpeg_response(
            generate_frames_with_detection_ffmpeg(stream_url, fps=fps, max_width=max_width, detect_width=detect_width)
        )
    except Exception as e:
        logger.error('Failed to stream video with detection for gate {}: {}'.format(gate_id, str(e)))
        return jsonify({'error': 'Failed to process video stream with detection'}), 500


@video_monitor_bp.route('/face-detection/<int:gate_id>/stream')
@limiter.exempt
def face_detection_sse(gate_id):
    """人脸检测SSE事件流，推送检测框JSON数据（不修改视频帧）"""
    from app.models.gate import Gate
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': '门禁终端不存在或未绑定推流码'}), 404

    config = current_app.config
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    stream_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, gate.push_key)
    fps = config.get('VIDEO_FPS', 20)
    detect_width = config.get('VIDEO_DETECT_WIDTH', 320)
    try:
        from .face_detection_stream import generate_detection_sse
        from flask import stream_with_context

        def generate():
            for event in generate_detection_sse(stream_url, fps=fps, max_width=max_width, detect_width=detect_width):
                yield event

        resp = Response(stream_with_context(generate()), mimetype='text/event-stream')
        resp.headers['Cache-Control'] = 'no-cache'
        resp.headers['X-Accel-Buffering'] = 'no'
        resp.headers['Connection'] = 'keep-alive'
        return resp
    except Exception as e:
        logger.error('Failed to stream face detection for gate {}: {}'.format(gate_id, str(e)))
        return jsonify({'error': 'Failed to process face detection stream'}), 500


@video_monitor_bp.route('/video_feed/gate/<int:gate_id>/danger-detect')
@limiter.exempt
def video_feed_by_gate_with_danger_detect(gate_id):
    """获取门禁终端带禁区入侵检测标注的MJPEG视频流"""
    from app.models.gate import Gate
    from app.models.danger_zone import DangerZone
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': '门禁终端不存在或未绑定推流码'}), 404

    gate_id_str = str(gate_id)
    zones = DangerZone.query.filter(
        DangerZone.camera_ids.contains(gate_id_str),
        DangerZone.status == 'active'
    ).all()
    if not zones:
        return jsonify({'error': '该摄像头未关联活跃禁区'}), 404

    config = current_app.config
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    stream_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, gate.push_key)
    try:
        from .danger_detect_stream import generate_frames_with_danger_detect
        return Response(
            generate_frames_with_danger_detect(stream_url, zones, max_width=max_width),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        logger.error('Failed to stream danger detect for gate {}: {}'.format(gate_id, str(e)))
        return jsonify({'error': 'Failed to process danger detection stream'}), 500


@video_monitor_bp.route('/video_feed/gate/<int:gate_id>/tamper')
@limiter.exempt
def video_feed_by_gate_with_tamper_detection(gate_id):
    """Return the gate stream with camera tamper detection annotations."""
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': 'Gate not found or push key is missing'}), 404

    config = current_app.config
    stream_url = 'rtmp://{}:{}/live/{}'.format(
        config.get('RTMP_SERVER_HOST', '20.214.147.223'),
        config.get('RTMP_SERVER_PORT', 9090),
        gate.push_key,
    )
    app = current_app._get_current_object()
    try:
        from .device_tamper_stream import (
            generate_frames_from_background_monitor,
            generate_frames_with_tamper_detection,
        )
        monitor = app.extensions.get('device_tamper_monitor')
        if monitor is not None:
            generator = generate_frames_from_background_monitor(
                monitor,
                gate_id=gate.id,
                max_width=config.get('VIDEO_MAX_WIDTH', 640),
                offline_timeout=config.get('DEVICE_OFFLINE_TIMEOUT', 5),
            )
        else:
            generator = generate_frames_with_tamper_detection(
                app,
                stream_url,
                gate_id=gate.id,
                max_width=config.get('VIDEO_MAX_WIDTH', 640),
                confirm_frames=config.get('DEVICE_TAMPER_CONFIRM_FRAMES', 3),
                blocked_confirm_frames=config.get('DEVICE_BLOCKED_CONFIRM_FRAMES', 8),
                recovery_frames=config.get('DEVICE_TAMPER_RECOVERY_FRAMES', 4),
                offline_timeout=config.get('DEVICE_OFFLINE_TIMEOUT', 5),
                open_timeout=config.get('DEVICE_STREAM_OPEN_TIMEOUT', 20),
                alarm_cooldown=config.get('DEVICE_ALARM_COOLDOWN', 60),
                check_interval=config.get('DEVICE_TAMPER_CHECK_INTERVAL', 0.1),
                impact_confirm_frames=config.get('DEVICE_IMPACT_CONFIRM_FRAMES', 1),
                impact_motion_threshold=config.get('DEVICE_IMPACT_MOTION_THRESHOLD', 6.0),
                impact_coherence_threshold=config.get('DEVICE_IMPACT_COHERENCE_THRESHOLD', 0.6),
                impact_reversal_cosine=config.get('DEVICE_IMPACT_REVERSAL_COSINE', -0.35),
                impact_window_frames=config.get('DEVICE_IMPACT_WINDOW_FRAMES', 6),
                impact_blur_drop_threshold=config.get('DEVICE_IMPACT_BLUR_DROP_THRESHOLD', 0.35),
                impact_min_tracked_points=config.get('DEVICE_IMPACT_MIN_TRACKED_POINTS', 20),
                impact_scene_change_limit=config.get('DEVICE_IMPACT_SCENE_CHANGE_LIMIT', 0.60),
                impact_sudden_multiplier=config.get('DEVICE_IMPACT_SUDDEN_MULTIPLIER', 1.25),
            )
        return Response(generator, mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception:
        logger.exception('Failed to start tamper detection for gate %s', gate_id)
        return jsonify({'error': 'Failed to process tamper detection stream'}), 500


@video_monitor_bp.route('/video_feed/gate/<int:gate_id>/tailgating')
@limiter.exempt
def video_feed_by_gate_with_tailgating(gate_id):
    """Return an independent real-time tailgating detection stream."""
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': 'Gate not found or push key is missing'}), 404

    config = current_app.config
    stream_url = 'rtmp://{}:{}/live/{}'.format(
        config.get('RTMP_SERVER_HOST', '127.0.0.1'),
        config.get('RTMP_SERVER_PORT', 9090),
        gate.push_key,
    )
    app = current_app._get_current_object()
    try:
        from .tailgating_stream import generate_frames_with_tailgating
        generator = generate_frames_with_tailgating(
            app,
            stream_url,
            gate_id=gate.id,
            prototxt_path=config.get('TAILGATING_PROTOTXT_PATH'),
            model_path=config.get('TAILGATING_MODEL_PATH'),
            max_width=config.get('VIDEO_MAX_WIDTH', 640),
            confidence=config.get('TAILGATING_CONFIDENCE', 0.25),
            detection_interval=config.get('TAILGATING_DETECTION_INTERVAL', 0.10),
            line_ratio=config.get('TAILGATING_LINE_RATIO', 0.62),
            crossing_window=config.get('TAILGATING_CROSSING_WINDOW', 5.0),
            max_horizontal_gap_ratio=config.get('TAILGATING_MAX_HORIZONTAL_GAP_RATIO', 0.28),
            authorized_entries=config.get('TAILGATING_AUTHORIZED_ENTRIES', 1),
            direction=config.get('TAILGATING_DIRECTION', 'both'),
            status_hold_seconds=config.get('TAILGATING_STATUS_HOLD_SECONDS', 3.0),
            alarm_cooldown=config.get('TAILGATING_ALARM_COOLDOWN', 60),
            open_timeout=config.get('DEVICE_STREAM_OPEN_TIMEOUT', 20),
        )
        return Response(generator, mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception:
        logger.exception('Failed to start tailgating detection for gate %s', gate_id)
        return jsonify({'error': 'Failed to process tailgating stream'}), 500


@video_monitor_bp.route('/video_feed/gate/<int:gate_id>/dangerous-behavior')
@limiter.exempt
def video_feed_by_gate_with_dangerous_behavior(gate_id):
    """Unified device-tamper, fire/smoke, and tailgating stream."""
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': 'Gate not found or push key is missing'}), 404

    config = current_app.config
    app = current_app._get_current_object()
    monitor = app.extensions.get('device_tamper_monitor')
    stream_url = 'rtmp://{}:{}/live/{}'.format(
        config.get('RTMP_SERVER_HOST', '20.214.147.223'),
        config.get('RTMP_SERVER_PORT', 9090),
        gate.push_key,
    )
    try:
        from .dangerous_behavior_stream import generate_frames_with_dangerous_behavior
        generator = generate_frames_with_dangerous_behavior(
            app,
            monitor,
            gate_id=gate.id,
            prototxt_path=config.get('TAILGATING_PROTOTXT_PATH'),
            model_path=config.get('TAILGATING_MODEL_PATH'),
            stream_url=stream_url,
            max_width=config.get('VIDEO_MAX_WIDTH', 640),
            confidence=config.get('TAILGATING_CONFIDENCE', 0.25),
            detection_interval=config.get('TAILGATING_DETECTION_INTERVAL', 0.10),
            line_ratio=config.get('TAILGATING_LINE_RATIO', 0.62),
            crossing_window=config.get('TAILGATING_CROSSING_WINDOW', 5.0),
            max_horizontal_gap_ratio=config.get('TAILGATING_MAX_HORIZONTAL_GAP_RATIO', 0.28),
            authorized_entries=config.get('TAILGATING_AUTHORIZED_ENTRIES', 1),
            direction=config.get('TAILGATING_DIRECTION', 'both'),
            status_hold_seconds=config.get('TAILGATING_STATUS_HOLD_SECONDS', 3.0),
            alarm_cooldown=config.get('TAILGATING_ALARM_COOLDOWN', 60),
            offline_timeout=config.get('DEVICE_OFFLINE_TIMEOUT', 5),
            open_timeout=config.get('DEVICE_STREAM_OPEN_TIMEOUT', 20),
        )
        return Response(generator, mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception:
        logger.exception('Failed to start dangerous behavior stream for gate %s', gate_id)
        return jsonify({'error': 'Failed to process dangerous behavior stream'}), 500


@video_monitor_bp.route('/danger-distance/<int:gate_id>/stream')
@limiter.exempt
def danger_distance_sse(gate_id):
    """禁区距离检测SSE事件流，推送人员距离数据（近大远小）"""
    from app.models.gate import Gate
    from app.models.danger_zone import DangerZone
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': '门禁终端不存在或未绑定推流码'}), 404

    gate_id_str = str(gate_id)
    zones = DangerZone.query.filter(
        DangerZone.camera_ids.contains(gate_id_str),
        DangerZone.status == 'active'
    ).all()


    config = current_app.config
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    stream_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, gate.push_key)
    fps = config.get('VIDEO_FPS', 20)
    detect_width = config.get('VIDEO_DETECT_WIDTH', 320)
    calib_near_dist = gate.calib_near_dist
    calib_near_ratio = gate.calib_near_ratio
    calib_far_dist = gate.calib_far_dist
    calib_far_ratio = gate.calib_far_ratio
    try:
        from .danger_distance_sse import generate_danger_distance_sse
        from flask import stream_with_context

        def generate():
            for event in generate_danger_distance_sse(stream_url, zones, fps=fps, max_width=max_width, detect_width=detect_width, calib_near_dist=calib_near_dist, calib_near_ratio=calib_near_ratio, calib_far_dist=calib_far_dist, calib_far_ratio=calib_far_ratio):
                yield event

        resp = Response(stream_with_context(generate()), mimetype='text/event-stream')
        resp.headers['Cache-Control'] = 'no-cache'
        resp.headers['X-Accel-Buffering'] = 'no'
        resp.headers['Connection'] = 'keep-alive'
        return resp
    except Exception as e:
        logger.error('Failed to stream danger distance for gate {}: {}'.format(gate_id, str(e)))
        return jsonify({'error': 'Failed to process danger distance stream'}), 500


@video_monitor_bp.route('/dangerous-behavior/<int:gate_id>/stream')
@limiter.exempt
def dangerous_behavior_sse(gate_id):
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': 'Gate not found or push key is missing'}), 404

    config = current_app.config
    app = current_app._get_current_object()
    monitor = app.extensions.get('device_tamper_monitor')
    stream_url = 'rtmp://{}:{}/live/{}'.format(
        config.get('RTMP_SERVER_HOST', '20.214.147.223'),
        config.get('RTMP_SERVER_PORT', 9090),
        gate.push_key,
    )
    try:
        from .dangerous_behavior_sse import generate_dangerous_behavior_sse
        from flask import stream_with_context

        def generate():
            for event in generate_dangerous_behavior_sse(
                app, monitor, gate_id, stream_url,
                prototxt_path=config.get('TAILGATING_PROTOTXT_PATH'),
                model_path=config.get('TAILGATING_MODEL_PATH'),
                fps=config.get('VIDEO_FPS', 20),
                max_width=config.get('VIDEO_MAX_WIDTH', 640),
                confidence=config.get('TAILGATING_CONFIDENCE', 0.25),
                detection_interval=config.get('TAILGATING_DETECTION_INTERVAL', 0.10),
                line_ratio=config.get('TAILGATING_LINE_RATIO', 0.62),
                crossing_window=config.get('TAILGATING_CROSSING_WINDOW', 5.0),
                max_horizontal_gap_ratio=config.get('TAILGATING_MAX_HORIZONTAL_GAP_RATIO', 0.28),
                authorized_entries=config.get('TAILGATING_AUTHORIZED_ENTRIES', 1),
                direction=config.get('TAILGATING_DIRECTION', 'both'),
                status_hold_seconds=config.get('TAILGATING_STATUS_HOLD_SECONDS', 3.0),
                alarm_cooldown=config.get('TAILGATING_ALARM_COOLDOWN', 60),
                offline_timeout=config.get('DEVICE_OFFLINE_TIMEOUT', 5),
            ):
                yield event

        resp = Response(stream_with_context(generate()), mimetype='text/event-stream')
        resp.headers['Cache-Control'] = 'no-cache'
        resp.headers['X-Accel-Buffering'] = 'no'
        resp.headers['Connection'] = 'keep-alive'
        return resp
    except Exception:
        logger.exception('Failed to start dangerous behavior SSE for gate %s', gate_id)
        return jsonify({'error': 'Failed to process dangerous behavior stream'}), 500



@video_monitor_bp.route('/detect-distance/<int:gate_id>', methods=['POST'])
@limiter.exempt
def detect_distance(gate_id):
    """检测当前画面中人脸的估算距离"""
    from app.models.gate import Gate
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': '门禁终端不存在或未绑定推流码'}), 404

    if not gate.calib_near_dist or not gate.calib_near_ratio:
        return jsonify({'code': 0, 'data': {'persons': [], 'calibrated': False}})

    import cv2
    import numpy as np

    frame = None
    frame_file = flask_request.files.get('frame')
    if frame_file:
        try:
            frame_bytes = frame_file.read()
            arr = np.frombuffer(frame_bytes, dtype=np.uint8).copy()
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception:
            pass

    if frame is None:
        return jsonify({'code': 0, 'data': {'persons': [], 'calibrated': True}})

    try:
        from core.face_recognition import FaceRecognizer
        recognizer = FaceRecognizer()
        rgb_image = np.ascontiguousarray(frame[:, :, ::-1])
        faces = recognizer.detect_faces_rgb(rgb_image)
    except Exception:
        faces = []

    persons = []
    for face_rect in faces:
        face_pixel_height = face_rect[3] - face_rect[1]
        frame_height = frame.shape[0]
        face_ratio = face_pixel_height / frame_height if frame_height > 0 else 0
        distance = None
        if gate.calib_near_ratio and face_ratio > 0:
            if gate.calib_far_ratio and gate.calib_far_dist and gate.calib_near_dist:
                k1 = gate.calib_near_dist * gate.calib_near_ratio
                k2 = gate.calib_far_dist * gate.calib_far_ratio
                k = (k1 + k2) / 2.0
                distance = round(k / face_ratio, 2)
            else:
                distance = round(gate.calib_near_dist * gate.calib_near_ratio / face_ratio, 2)
        persons.append({'distance': distance})

    return jsonify({'code': 0, 'data': {'persons': persons, 'calibrated': True}})


@video_monitor_bp.route('/calibrate-distance/<int:gate_id>', methods=['POST'])
@limiter.exempt
def calibrate_distance(gate_id):
    """距离校准：支持两点校准，point=near或far"""
    from app.models.gate import Gate
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': '门禁终端不存在或未绑定推流码'}), 404

    data = {}
    try:
        data = flask_request.get_json(force=True, silent=True) or {}
    except Exception:
        pass
    known_distance = data.get('distance')
    point = data.get('point')
    if not known_distance:
        known_distance = flask_request.form.get('distance')
    if not point:
        point = flask_request.form.get('point', 'near')
    try:
        known_distance = float(known_distance)
    except (TypeError, ValueError):
        return jsonify({'error': '请提供有效的已知距离(米)'}), 400
    if known_distance <= 0:
        return jsonify({'error': '请提供有效的已知距离(米)'}), 400
    if point not in ('near', 'far'):
        return jsonify({'error': 'point参数应为near或far'}), 400

    import cv2
    import numpy as np
    import base64 as _base64

    frame = None
    frame_file = flask_request.files.get('frame')
    if frame_file:
        try:
            frame_bytes = frame_file.read()
            arr = np.frombuffer(frame_bytes, dtype=np.uint8).copy()
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception as e:
            logger.warning('Failed to decode uploaded frame: {}'.format(str(e)))

    frame_base64 = data.get('frame_base64')
    if frame is None and frame_base64:
        try:
            jpeg_data = _base64.b64decode(frame_base64)
            arr = np.frombuffer(jpeg_data, dtype=np.uint8).copy()
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception as e:
            logger.warning('Failed to decode frame_base64: {}'.format(str(e)))

    if frame is None:
        config = current_app.config
        rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
        rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
        stream_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, gate.push_key)

        from core.rtmp_relay import start_rtmp_pull, read_cv2_frame_from_pull, stop_rtmp_pull
        from core.shared_frame_store import get_frame as _get_shared_frame

        jpeg = _get_shared_frame(stream_url)
        if jpeg is not None:
            arr = np.frombuffer(jpeg, dtype=np.uint8).copy()
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        if frame is None:
            entry = start_rtmp_pull(stream_url, fps=5, max_width=640)
            if entry is not None:
                for _ in range(20):
                    ok, f = read_cv2_frame_from_pull(entry)
                    if ok and f is not None:
                        frame = f
                        break
                    time.sleep(0.2)
                stop_rtmp_pull(stream_url)

    if frame is None:
        return jsonify({'error': '无法获取视频帧，请确认摄像头在线'}), 400

    try:
        from core.face_recognition import FaceRecognizer
        recognizer = FaceRecognizer()
        rgb_image = np.ascontiguousarray(frame[:, :, ::-1])
        faces = recognizer.detect_faces_rgb(rgb_image)
    except Exception as e:
        logger.error('Calibration face detection error: {}'.format(str(e)))
        return jsonify({'error': '人脸检测失败: {}'.format(str(e))}), 500

    if not faces:
        return jsonify({'error': '未检测到人脸，请站在摄像头前重试'}), 400

    face_rect = faces[0]
    face_pixel_height = face_rect[3] - face_rect[1]
    frame_height = frame.shape[0]
    face_ratio = round(face_pixel_height / frame_height, 6)

    if point == 'near':
        gate.calib_near_dist = float(known_distance)
        gate.calib_near_ratio = face_ratio
    else:
        gate.calib_far_dist = float(known_distance)
        gate.calib_far_ratio = face_ratio
    db.session.commit()

    logger.info('Gate {} calibrated {} point: distance={}m, ratio={}'.format(gate_id, point, known_distance, face_ratio))
    return jsonify({
        'code': 0,
        'data': {
            'gate_id': gate_id,
            'point': point,
            'calib_near_dist': gate.calib_near_dist,
            'calib_near_ratio': gate.calib_near_ratio,
            'calib_far_dist': gate.calib_far_dist,
            'calib_far_ratio': gate.calib_far_ratio,
            'face_pixel_height': face_pixel_height,
            'frame_height': frame_height
        }
    })


@video_monitor_bp.route('/recordings', methods=['GET'])
def get_recordings():
    """获取历史录像列表，按push_key分类，按时间排序"""
    config = current_app.config
    base_url = config.get('RECORDINGS_BASE_URL', 'http://20.214.147.223:9092')
    push_key = flask_request.args.get('push_key', '')

    try:
        resp = http_requests.get(base_url + '/', timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.error('Failed to fetch recordings index: {}'.format(str(e)))
        return error_response(message='无法获取录像列表', code=500)

    html = resp.text
    line_pattern = re.compile(
        r'href="([^"]+\.(?:flv|mp4))"'   # filename
        r'[^>]*>\s*\1\s*</a>'             # link text
        r'\s+(\d{2}-\w{3}-\d{4}\s+\d{2}:\d{2})'  # date
        r'\s+([\d.]+[KMG]?)'              # size
    )

    from app.models.gate import Gate
    gates = {g.push_key: g.to_dict() for g in Gate.query.all() if g.push_key}

    grouped = {}
    for m in line_pattern.finditer(html):
        filename = m.group(1)
        size_str = m.group(3)
        file_size = _parse_size(size_str)

        parts = filename.rsplit('-', 1)
        if len(parts) != 2:
            continue
        pk, time_str = parts[0], parts[1].rsplit('.', 1)[0]
        if push_key and pk != push_key:
            continue
        try:
            dt = datetime.strptime(time_str, '%Y%m%d_%H%M%S')
        except ValueError:
            continue
        if pk not in grouped:
            gate_info = gates.get(pk)
            grouped[pk] = {
                'push_key': pk,
                'gate_name': gate_info['gate_name'] if gate_info else pk,
                'gate_id': gate_info['id'] if gate_info else None,
                'files': []
            }
        grouped[pk]['files'].append({
            'filename': filename,
            'url': '/api/v1/video-monitor/recordings/file/{}'.format(filename),
            'datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': dt.timestamp(),
            'file_size': file_size,
            'file_size_text': _format_size(file_size),
            'duration_text': _estimate_duration(file_size)
        })

    for pk in grouped:
        grouped[pk]['files'].sort(key=lambda x: x['timestamp'], reverse=True)

    result = sorted(grouped.values(), key=lambda x: x['push_key'])
    return success_response(data=result)


@video_monitor_bp.route('/recordings/<path:filename>', methods=['DELETE'])
@jwt_required()
def delete_recording(filename):
    """删除历史录像文件"""
    role = get_jwt().get('role', '')
    if role != 'admin':
        return error_response(message='仅管理员可删除录像', code=403)

    config = current_app.config
    base_url = config.get('RECORDINGS_BASE_URL', 'http://20.214.147.223:9092')
    remote_url = '{}/{}'.format(base_url, filename)

    try:
        resp = http_requests.delete(remote_url, timeout=10)
        if resp.status_code == 405:
            http_requests.request('DELETE', remote_url, timeout=10)
    except Exception as e:
        logger.error('Failed to delete recording {}: {}'.format(filename, str(e)))
        return error_response(message='删除录像失败: {}'.format(str(e)), code=500)

    log_audit(operation_type='delete_recording', operation_content='删除录像: {}'.format(filename))
    return success_response(message='删除成功')


@video_monitor_bp.route('/recordings/file/<path:filename>', methods=['GET'])
def get_recording_file(filename):
    """代理历史录像文件，解决跨域问题"""
    config = current_app.config
    base_url = config.get('RECORDINGS_BASE_URL', 'http://20.214.147.223:9092')
    remote_url = '{}/{}'.format(base_url, filename)

    range_header = flask_request.headers.get('Range')
    headers = {}
    if range_header:
        headers['Range'] = range_header

    try:
        resp = http_requests.get(remote_url, headers=headers, stream=True, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.error('Failed to fetch recording file {}: {}'.format(filename, str(e)))
        return error_response(message='无法获取录像文件', code=500)

    excluded = {'transfer-encoding', 'connection', 'content-encoding'}
    response_headers = {}
    for k, v in resp.headers.items():
        if k.lower() not in excluded:
            response_headers[k] = v

    def generate():
        try:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    yield chunk
        finally:
            resp.close()

    return Response(
        generate(),
        status=resp.status_code,
        headers=response_headers,
        mimetype=resp.headers.get('Content-Type', 'video/x-flv')
    )




def _parse_size(size_str):
    """将nginx目录列表的大小字符串转为字节数"""
    size_str = size_str.strip()
    if not size_str:
        return 0
    units = {'K': 1024, 'M': 1024 * 1024, 'G': 1024 * 1024 * 1024}
    if size_str[-1].upper() in units:
        try:
            return int(float(size_str[:-1]) * units[size_str[-1].upper()])
        except ValueError:
            return 0
    try:
        return int(size_str)
    except ValueError:
        return 0


def _format_size(size_bytes):
    """将字节数格式化为可读字符串"""
    if size_bytes <= 0:
        return '0B'
    units = ['B', 'KB', 'MB', 'GB']
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    if i == 0:
        return '{}B'.format(int(size))
    return '{:.1f}{}'.format(size, units[i])


def _estimate_duration(file_size):
    if file_size <= 0:
        return '--:--'
    bitrate = 1000 * 1024 / 8
    seconds = int(file_size / bitrate)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return '{}:{:02d}:{:02d}'.format(hours, minutes, secs)
    return '{:02d}:{:02d}'.format(minutes, secs)
