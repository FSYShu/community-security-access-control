"""
共享帧存储
视频流MJPEG生成器将最新帧写入此处，人脸检测SSE端点从中读取
避免SSE端点单独启动RTMP拉流导致视频流中断
"""
import threading
import time

_STORE = {}
_LOCK = threading.Lock()
_MAX_AGE = 30.0


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


def cleanup_stale_frames():
    """清理过期的共享帧，防止内存泄漏"""
    now = time.time()
    with _LOCK:
        stale_urls = []
        for url, entry in _STORE.items():
            if now - entry.get('timestamp', 0) > _MAX_AGE:
                stale_urls.append(url)
        for url in stale_urls:
            del _STORE[url]
    return len(stale_urls)