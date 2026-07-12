"""
共享帧存储
视频流MJPEG生成器将最新帧写入此处，人脸检测SSE端点从中读取
避免SSE端点单独启动RTMP拉流导致视频流中断
"""
import threading
import time

_STORE = {}
_LOCK = threading.Lock()


def update_frame(stream_url, jpeg_bytes):
    with _LOCK:
        _STORE[stream_url] = {
            'jpeg': jpeg_bytes,
            'timestamp': time.time(),
        }


def get_frame(stream_url):
    with _LOCK:
        entry = _STORE.get(stream_url)
    if entry:
        return entry['jpeg']
    return None


def remove_frame(stream_url):
    with _LOCK:
        _STORE.pop(stream_url, None)