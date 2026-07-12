"""
门禁端RTMP推流中继服务
接收JPEG帧，通过FFmpeg转推到RTMP服务器
"""
import logging
import os
import subprocess
import threading
import time

logger = logging.getLogger(__name__)

_ffmpeg_processes = {}
_ffmpeg_lock = threading.Lock()
_key_locks = {}
_key_lock_lock = threading.Lock()
_LAST_DATA_TIMEOUT = 30
_ffmpeg_available = None
_ffmpeg_cmd = None


def _get_key_lock(push_key):
    with _key_lock_lock:
        if push_key not in _key_locks:
            _key_locks[push_key] = threading.Lock()
        return _key_locks[push_key]


def _find_ffmpeg():
    global _ffmpeg_cmd
    if _ffmpeg_cmd is not None:
        return _ffmpeg_cmd
    try:
        import imageio_ffmpeg
        _ffmpeg_cmd = imageio_ffmpeg.get_ffmpeg_exe()
        logger.info('Using imageio-ffmpeg: {}'.format(_ffmpeg_cmd))
        return _ffmpeg_cmd
    except Exception:
        pass
    _ffmpeg_cmd = 'ffmpeg'
    return _ffmpeg_cmd


def _check_ffmpeg():
    global _ffmpeg_available
    if _ffmpeg_available is not None:
        return _ffmpeg_available
    ffmpeg = _find_ffmpeg()
    try:
        proc = subprocess.run(
            [ffmpeg, '-version'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        if proc.returncode == 0:
            _ffmpeg_available = True
            logger.info('FFmpeg available: {}'.format(ffmpeg))
        else:
            _ffmpeg_available = False
            logger.error('FFmpeg returned non-zero exit code')
    except FileNotFoundError:
        _ffmpeg_available = False
        logger.error('FFmpeg not found! Install: pip install imageio-ffmpeg')
    except Exception as e:
        _ffmpeg_available = False
        logger.error('FFmpeg check failed: {}'.format(str(e)))
    return _ffmpeg_available


def get_ffmpeg_cmd(rtmp_url):
    ffmpeg = _find_ffmpeg()
    return [
        ffmpeg,
        '-loglevel', 'warning',
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        '-framerate', '5',
        '-fflags', '+genpts',
        '-i', 'pipe:0',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-b:v', '500k',
        '-maxrate', '500k',
        '-bufsize', '1000k',
        '-pix_fmt', 'yuv420p',
        '-g', '15',
        '-keyint_min', '15',
        '-f', 'flv',
        rtmp_url
    ]


def _get_or_create_process(push_key, rtmp_url):
    key_lock = _get_key_lock(push_key)
    if not key_lock.acquire(blocking=False):
        return None

    try:
        with _ffmpeg_lock:
            entry = _ffmpeg_processes.get(push_key)
            if entry and entry['process'].poll() is None:
                return entry
            if entry:
                logger.warning('FFmpeg process for key {} exited with code {}, restarting'.format(
                    push_key, entry['process'].returncode))
                try:
                    entry['process'].stdin.close()
                except Exception:
                    pass
                try:
                    entry['process'].kill()
                    entry['process'].wait(timeout=3)
                except Exception:
                    pass
                del _ffmpeg_processes[push_key]

        time.sleep(1)

        cmd = get_ffmpeg_cmd(rtmp_url)
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
        except FileNotFoundError:
            global _ffmpeg_available
            _ffmpeg_available = False
            logger.error('FFmpeg not found, cannot push RTMP stream')
            return None
        except Exception as e:
            logger.error('Failed to start FFmpeg: {}'.format(str(e)))
            return None

        entry = {
            'process': proc,
            'last_data': time.time()
        }
        with _ffmpeg_lock:
            _ffmpeg_processes[push_key] = entry
        logger.info('Started FFmpeg RTMP push for key: {} -> {}'.format(push_key, rtmp_url))

        def log_stderr(p, key):
            try:
                for line in p.stderr:
                    msg = line.decode('utf-8', errors='replace').strip()
                    if msg:
                        logger.warning('FFmpeg[{}]: {}'.format(key, msg))
            except Exception:
                pass

        t = threading.Thread(target=log_stderr, args=(proc, push_key), daemon=True)
        t.start()
        return entry
    finally:
        key_lock.release()


def push_jpeg_frame(push_key, jpeg_bytes, rtmp_url):
    if not _check_ffmpeg():
        return

    entry = _get_or_create_process(push_key, rtmp_url)
    if not entry:
        with _ffmpeg_lock:
            entry = _ffmpeg_processes.get(push_key)
        if not entry or entry['process'].poll() is not None:
            return

    try:
        entry['process'].stdin.write(jpeg_bytes)
        entry['process'].stdin.flush()
        entry['last_data'] = time.time()
    except BrokenPipeError:
        logger.error('FFmpeg stdin broken for key {}, will restart next frame'.format(push_key))
        _remove_process(push_key)
    except Exception as e:
        logger.error('FFmpeg write error for key {}: {}'.format(push_key, str(e)))
        _remove_process(push_key)


def _remove_process(push_key):
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
                entry['process'].wait(timeout=3)
            except Exception:
                pass
            logger.info('Cleaned up stale FFmpeg for key: {}'.format(key))


_PULL_PROCESSES = {}
_PULL_LOCK = threading.Lock()


def start_rtmp_pull(rtmp_url, fps=10, max_width=640):
    cmd = [
        _find_ffmpeg(),
        '-loglevel', 'warning',
        '-rw_timeout', '5000000',
        '-analyzeduration', '2000000',
        '-probesize', '500000',
        '-i', rtmp_url,
        '-vf', 'fps={},scale={}:-1'.format(fps, max_width),
        '-q:v', '5',
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        'pipe:1'
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except Exception as e:
        logger.error('Failed to start FFmpeg pull from {}: {}'.format(rtmp_url, str(e)))
        return None

    def log_stderr(p, url):
        try:
            for line in p.stderr:
                msg = line.decode('utf-8', errors='replace').strip()
                if msg:
                    logger.warning('FFmpeg-pull[{}]: {}'.format(url, msg))
        except Exception:
            pass

    t = threading.Thread(target=log_stderr, args=(proc, rtmp_url), daemon=True)
    t.start()

    entry = {
        'process': proc,
        'url': rtmp_url,
        'started': time.time()
    }
    with _PULL_LOCK:
        _PULL_PROCESSES[rtmp_url] = entry
    logger.info('Started FFmpeg RTMP pull from: {}'.format(rtmp_url))
    return entry


def read_jpeg_frame_from_pull(pull_entry):
    proc = pull_entry['process']
    stdout = proc.stdout

    header = b''
    while True:
        b = stdout.read(1)
        if not b:
            return None
        header += b
        if header.endswith(b'\xff\xd8'):
            break
        if len(header) > 65536:
            header = header[-4:]

    jpeg_data = b'\xff\xd8'
    while True:
        b = stdout.read(1)
        if not b:
            return None
        jpeg_data += b
        if len(jpeg_data) >= 2 and jpeg_data[-2:] == b'\xff\xd9':
            return jpeg_data
        if len(jpeg_data) > 1048576:
            logger.warning('JPEG frame too large, discarding')
            return None


def read_cv2_frame_from_pull(pull_entry):
    jpeg_data = read_jpeg_frame_from_pull(pull_entry)
    if jpeg_data is None:
        return False, None
    import cv2
    import numpy as np
    arr = np.frombuffer(jpeg_data, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return False, None
    return True, frame


def stop_rtmp_pull(rtmp_url):
    with _PULL_LOCK:
        entry = _PULL_PROCESSES.pop(rtmp_url, None)
    if entry:
        try:
            entry['process'].kill()
            entry['process'].wait(timeout=5)
        except Exception:
            pass
        logger.info('Stopped FFmpeg RTMP pull from: {}'.format(rtmp_url))


def cleanup_pull_processes():
    with _PULL_LOCK:
        stale = []
        for url, entry in _PULL_PROCESSES.items():
            if entry['process'].poll() is not None:
                stale.append(url)
        for url in stale:
            del _PULL_PROCESSES[url]


_PUSH_TIMESTAMPS = {}
_PUSH_TS_LOCK = threading.Lock()


def update_push_timestamp(push_key, ts_ms):
    with _PUSH_TS_LOCK:
        _PUSH_TIMESTAMPS[push_key] = ts_ms


def get_push_latency_ms(push_key):
    with _PUSH_TS_LOCK:
        ts = _PUSH_TIMESTAMPS.get(push_key)
    if ts is None:
        return -1
    return int(time.time() * 1000) - ts
