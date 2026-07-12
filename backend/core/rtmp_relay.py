"""
门禁端RTMP推流中继服务
接收JPEG帧，通过FFmpeg转推到RTMP服务器
"""
import logging
import subprocess
import threading
import time

logger = logging.getLogger(__name__)

_ffmpeg_processes = {}
_ffmpeg_lock = threading.Lock()
_LAST_DATA_TIMEOUT = 30


def get_ffmpeg_cmd(rtmp_url):
    return [
        'ffmpeg',
        '-re',
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        '-i', 'pipe:0',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-b:v', '500k',
        '-maxrate', '500k',
        '-bufsize', '1000k',
        '-pix_fmt', 'yuv420p',
        '-g', '30',
        '-f', 'flv',
        rtmp_url
    ]


def push_jpeg_frame(push_key, jpeg_bytes, rtmp_url):
    with _ffmpeg_lock:
        entry = _ffmpeg_processes.get(push_key)
        if not entry or entry['process'].poll() is not None:
            if entry:
                try:
                    entry['process'].kill()
                except Exception:
                    pass
                del _ffmpeg_processes[push_key]

            cmd = get_ffmpeg_cmd(rtmp_url)
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except FileNotFoundError:
                logger.error('FFmpeg not found, cannot push RTMP stream')
                return
            except Exception as e:
                logger.error('Failed to start FFmpeg: {}'.format(str(e)))
                return

            entry = {
                'process': proc,
                'last_data': time.time()
            }
            _ffmpeg_processes[push_key] = entry
            logger.info('Started FFmpeg RTMP push for key: {}'.format(push_key))

        try:
            entry['process'].stdin.write(jpeg_bytes)
            entry['process'].stdin.flush()
            entry['last_data'] = time.time()
        except Exception:
            try:
                entry['process'].kill()
            except Exception:
                pass
            _ffmpeg_processes.pop(push_key, None)


def stop_ffmpeg(push_key):
    with _ffmpeg_lock:
        entry = _ffmpeg_processes.pop(push_key, None)
        if entry:
            try:
                entry['process'].stdin.close()
            except Exception:
                pass
            try:
                entry['process'].kill()
                entry['process'].wait(timeout=3)
            except Exception:
                pass
            logger.info('Stopped FFmpeg RTMP push for key: {}'.format(push_key))


def cleanup_stale():
    now = time.time()
    with _ffmpeg_lock:
        stale_keys = []
        for key, entry in _ffmpeg_processes.items():
            if now - entry['last_data'] > _LAST_DATA_TIMEOUT:
                stale_keys.append(key)
        for key in stale_keys:
            entry = _ffmpeg_processes.pop(key)
            try:
                entry['process'].stdin.close()
            except Exception:
                pass
            try:
                entry['process'].kill()
            except Exception:
                pass
            logger.info('Cleaned up stale FFmpeg for key: {}'.format(key))
