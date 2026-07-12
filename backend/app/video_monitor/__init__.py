"""
视频监控模块蓝图
提供RTMP视频流拉取、MJPEG转发、历史视频回放等接口
"""
import logging
import re
import time
import base64
import threading
from datetime import datetime

import cv2
import requests as http_requests
from flask import Blueprint, Response, jsonify, current_app, request as flask_request
from flask_jwt_extended import jwt_required, get_jwt

from app import limiter
from utils import error_response
from utils.response import success_response
from core.audit_logger import log_audit

video_monitor_bp = Blueprint('video_monitor', __name__)

logger = logging.getLogger(__name__)

_gate_push_frames = {}
_gate_push_lock = threading.Lock()
_GATE_FRAME_TTL = 10


def _store_gate_frame(push_key, jpeg_bytes):
    with _gate_push_lock:
        _gate_push_frames[push_key] = {
            'frame': jpeg_bytes,
            'timestamp': time.time()
        }


def _get_gate_frame(push_key):
    with _gate_push_lock:
        entry = _gate_push_frames.get(push_key)
        if not entry:
            return None
        if time.time() - entry['timestamp'] > _GATE_FRAME_TTL:
            del _gate_push_frames[push_key]
            return None
        return entry['frame']


def _has_gate_frames(push_key):
    with _gate_push_lock:
        entry = _gate_push_frames.get(push_key)
        if not entry:
            return False
        if time.time() - entry['timestamp'] > _GATE_FRAME_TTL:
            del _gate_push_frames[push_key]
            return False
        return True


def _try_connect_rtmp(stream_url, timeout=8):
    import threading
    cap_result = {'cap': None, 'opened': False, 'error': None}
    cap_error = threading.Event()

    def try_open():
        try:
            cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
            cap_result['cap'] = cap
            cap_result['opened'] = cap.isOpened()
        except Exception as e:
            cap_result['opened'] = False
            cap_result['error'] = str(e)
        cap_error.set()

    t = threading.Thread(target=try_open, daemon=True)
    t.start()
    if not cap_error.wait(timeout=timeout):
        logger.error('Timeout opening RTMP stream: {}'.format(stream_url))
        return None, 'RTMP连接超时'

    if not cap_result['opened']:
        logger.error('Failed to open RTMP stream: {}'.format(stream_url))
        return None, 'RTMP连接失败'

    cap = cap_result['cap']
    success, frame = cap.read()
    if not success or frame is None:
        logger.warning('Failed to read first frame from stream: {}'.format(stream_url))
        cap.release()
        return None, '无法读取视频帧'

    return cap, frame


def generate_frames(stream_url, frame_skip=3, max_width=640, cap=None, first_frame=None):
    import threading
    if cap is None:
        cap, first_frame = _try_connect_rtmp(stream_url)
    if cap is None:
        return

    latest = {'frame': first_frame, 'lock': threading.Lock(), 'alive': True}

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

    try:
        while latest['alive']:
            with latest['lock']:
                current = latest['frame']
            if current is None:
                time.sleep(0.01)
                continue

            h, w = current.shape[:2]
            if w > max_width:
                scale = max_width / w
                current = cv2.resize(current, (max_width, int(h * scale)), interpolation=cv2.INTER_LINEAR)
            ret, buffer = cv2.imencode(
                '.jpg', current,
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


def generate_frames_from_push(push_key, max_width=640):
    while True:
        frame_bytes = _get_gate_frame(push_key)
        if frame_bytes is None:
            time.sleep(0.1)
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05)


@video_monitor_bp.route('/gate-push-frame', methods=['POST'])
@limiter.exempt
def gate_push_frame():
    data = flask_request.get_json(force=True, silent=True)
    if not data or not data.get('push_key') or not data.get('frame'):
        return jsonify({'error': '缺少push_key或frame参数'}), 400
    push_key = data['push_key']
    try:
        jpeg_bytes = base64.b64decode(data['frame'])
    except Exception:
        return jsonify({'error': 'frame解码失败'}), 400
    _store_gate_frame(push_key, jpeg_bytes)
    config = current_app.config
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    rtmp_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, push_key)
    from core.rtmp_relay import push_jpeg_frame
    push_jpeg_frame(push_key, jpeg_bytes, rtmp_url)
    return jsonify({'code': 0, 'message': 'ok'})



@video_monitor_bp.route('/video_feed/<stream_id>')
@limiter.exempt
def video_feed(stream_id):
    """获取MJPEG视频流（通过stream_id拼接RTMP地址）"""
    config = current_app.config
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    stream_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, stream_id)
    frame_skip = config.get('VIDEO_FRAME_SKIP', 5)
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    try:
        cap, first_frame = _try_connect_rtmp(stream_url)
        if cap is None:
            return jsonify({'error': 'RTMP连接失败', 'code': 503}), 503
        return Response(
            generate_frames(stream_url, frame_skip=frame_skip, max_width=max_width, cap=cap, first_frame=first_frame),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        logger.error('Failed to stream video for ID {}: {}'.format(stream_id, str(e)))
        return jsonify({'error': 'Failed to process video stream'}), 500


@video_monitor_bp.route('/video_feed/gate/<int:gate_id>')
@limiter.exempt
def video_feed_by_gate(gate_id):
    """获取门禁终端的MJPEG视频流（优先使用门禁端推流帧，否则从RTMP拉取）"""
    from app.models.gate import Gate
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': '门禁终端不存在或未绑定推流码'}), 404
    config = current_app.config
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    if _has_gate_frames(gate.push_key):
        return Response(
            generate_frames_from_push(gate.push_key, max_width=max_width),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    stream_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, gate.push_key)
    frame_skip = config.get('VIDEO_FRAME_SKIP', 5)
    try:
        cap, first_frame = _try_connect_rtmp(stream_url)
        if cap is None:
            return jsonify({'error': 'RTMP连接失败', 'code': 503}), 503
        return Response(
            generate_frames(stream_url, frame_skip=frame_skip, max_width=max_width, cap=cap, first_frame=first_frame),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        logger.error('Failed to stream video for gate {}: {}'.format(gate_id, str(e)))
        return jsonify({'error': 'Failed to process video stream'}), 500


@video_monitor_bp.route('/video_feed/gate/<int:gate_id>/detect')
@limiter.exempt
def video_feed_by_gate_with_detection(gate_id):
    """获取门禁终端带人脸检测标注的MJPEG视频流（优先使用门禁端推流帧，否则从RTMP拉取）"""
    from app.models.gate import Gate
    gate = Gate.query.get(gate_id)
    if not gate or not gate.push_key:
        return jsonify({'error': '门禁终端不存在或未绑定推流码'}), 404
    config = current_app.config
    max_width = config.get('VIDEO_MAX_WIDTH', 640)
    if _has_gate_frames(gate.push_key):
        from .face_detection_stream import generate_frames_with_detection_from_push
        return Response(
            generate_frames_with_detection_from_push(gate.push_key, max_width=max_width),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    rtmp_host = config.get('RTMP_SERVER_HOST', '20.214.147.223')
    rtmp_port = config.get('RTMP_SERVER_PORT', 9090)
    stream_url = 'rtmp://{}:{}/live/{}'.format(rtmp_host, rtmp_port, gate.push_key)
    frame_skip = config.get('VIDEO_FRAME_SKIP', 5)
    detect_width = config.get('VIDEO_DETECT_WIDTH', 320)
    try:
        cap, first_frame = _try_connect_rtmp(stream_url)
        if cap is None:
            return jsonify({'error': 'RTMP连接失败', 'code': 503}), 503
        from .face_detection_stream import generate_frames_with_detection_url
        return Response(
            generate_frames_with_detection_url(stream_url, frame_skip=frame_skip, max_width=max_width, detect_width=detect_width, cap=cap, first_frame=first_frame),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        logger.error('Failed to stream video with detection for gate {}: {}'.format(gate_id, str(e)))
        return jsonify({'error': 'Failed to process video stream with detection'}), 500


@video_monitor_bp.route('/list', methods=['GET'])
def get_monitor_list():
    """获取监控区域列表"""
    return error_response(message='监控区域列表接口开发中', code=-1)


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


@video_monitor_bp.route('/<int:monitor_id>/playback', methods=['GET'])
def get_video_playback(monitor_id):
    """获取视频回放地址"""
    return error_response(message='视频回放接口开发中', code=-1)


def _generate_placeholder(text, resolution=(480, 480)):
    import numpy as np
    img = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
    cv2.putText(img, text, (10, resolution[1] // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    ret, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes() if ret else b''


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
    """根据文件大小估算FLV录像时长（假设2Mbps码率）"""
    if file_size <= 0:
        return '--:--'
    bitrate = 2 * 1024 * 1024 / 8  # 2Mbps = 256KB/s
    seconds = int(file_size / bitrate)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return '{}:{:02d}:{:02d}'.format(hours, minutes, secs)
    return '{:02d}:{:02d}'.format(minutes, secs)
