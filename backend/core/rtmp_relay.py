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
        '-framerate', '30',
        '-fflags', '+genpts+fastseek+discardcorrupt',
        '-i', 'pipe:0',
        '-c:v', 'libx264',
        '-preset', 'faster',
        '-tune', 'zerolatency',
        '-b:v', '3000k',
        '-maxrate', '4000k',
        '-bufsize', '4000k',
        '-pix_fmt', 'yuv420p',
        '-g', '30',
        '-keyint_min', '15',
        '-threads', '6',
        '-thread_type', 'slice',
        '-x264-params', 'nal-hrd=cbr:force-cfr=1',
        '-movflags', '+faststart',
        '-flush_packets', '1',
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


def start_rtmp_pull(rtmp_url, fps=25, max_width=640):
    with _PULL_LOCK:
        existing = _PULL_PROCESSES.get(rtmp_url)
        if existing and existing['process'].poll() is None:
            existing['ref_count'] = existing.get('ref_count', 1) + 1
            logger.info('Reusing existing FFmpeg pull for: {} (ref_count={})'.format(rtmp_url, existing['ref_count']))
            return existing
        old = _PULL_PROCESSES.pop(rtmp_url, None)
    if old:
        try:
            old['process'].stdout.close()
        except Exception:
            pass
        try:
            old['process'].stderr.close()
        except Exception:
            pass
        try:
            old['process'].kill()
            old['process'].wait(timeout=3)
        except Exception:
            pass
        logger.info('Killed stale FFmpeg pull for: {}'.format(rtmp_url))
        time.sleep(0.05)

    cmd = [
        _find_ffmpeg(),
        '-loglevel', 'warning',
        '-fflags', '+genpts+nobuffer+fastseek+discardcorrupt',
        '-rw_timeout', '5000000',
        '-analyzeduration', '500000',
        '-probesize', '300000',
        '-i', rtmp_url,
        '-map', '0:v:0',
        '-an',
        '-vf', 'scale={}:-1'.format(max_width),
        '-q:v', '2',
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        '-threads', '4',
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
        'started': time.time(),
        'ref_count': 1
    }
    with _PULL_LOCK:
        _PULL_PROCESSES[rtmp_url] = entry
    logger.info('Started FFmpeg RTMP pull from: {}'.format(rtmp_url))
    return entry


_JPEG_SOI = b'\xff\xd8'
_JPEG_EOI = b'\xff\xd9'
_READ_CHUNK = 131072


def read_jpeg_frame_from_pull(pull_entry):
    proc = pull_entry['process']
    stdout = proc.stdout

    scan = b''
    while True:
        idx = scan.find(_JPEG_SOI)
        if idx >= 0:
            scan = scan[idx:]
            break
        chunk = stdout.read(_READ_CHUNK)
        if not chunk:
            return None
        scan = scan[-3:] + chunk

    while True:
        idx = scan.find(_JPEG_EOI)
        if idx >= 0:
            frame = scan[:idx + 2]
            record_pull_frame(pull_entry['url'])
            return frame
        chunk = stdout.read(_READ_CHUNK)
        if not chunk:
            return None
        scan += chunk
        if len(scan) > 1048576:
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
        entry = _PULL_PROCESSES.get(rtmp_url)
        if not entry:
            return
        entry['ref_count'] = entry.get('ref_count', 1) - 1
        if entry['ref_count'] > 0:
            logger.info('Decrementing FFmpeg pull ref for: {} (ref_count={})'.format(rtmp_url, entry['ref_count']))
            return
        _PULL_PROCESSES.pop(rtmp_url, None)
    proc = entry['process']
    try:
        proc.stdout.close()
    except Exception:
        pass
    try:
        proc.stderr.close()
    except Exception:
        pass
    try:
        proc.kill()
        proc.wait(timeout=3)
    except Exception:
        pass
    logger.info('Stopped FFmpeg RTMP pull from: {}'.format(rtmp_url))


def get_pull_process_info(rtmp_url):
    """获取拉流进程信息，用于监控和调试"""
    with _PULL_LOCK:
        entry = _PULL_PROCESSES.get(rtmp_url)
        if not entry:
            return None
        return {
            'url': rtmp_url,
            'ref_count': entry.get('ref_count', 1),
            'started': entry.get('started'),
            'alive': entry['process'].poll() is None
        }


def get_all_pull_processes():
    """获取所有拉流进程信息"""
    result = []
    with _PULL_LOCK:
        for url, entry in _PULL_PROCESSES.items():
            result.append({
                'url': url,
                'ref_count': entry.get('ref_count', 1),
                'started': entry.get('started'),
                'alive': entry['process'].poll() is None
            })
    return result


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


_PULL_FRAME_COUNTERS = {}
_PULL_FC_LOCK = threading.Lock()
_PULL_FC_WINDOW = 2.0


def record_pull_frame(rtmp_url):
    now = time.time()
    with _PULL_FC_LOCK:
        if rtmp_url not in _PULL_FRAME_COUNTERS:
            _PULL_FRAME_COUNTERS[rtmp_url] = []
        timestamps = _PULL_FRAME_COUNTERS[rtmp_url]
        timestamps.append(now)
        cutoff = now - _PULL_FC_WINDOW
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)


def get_pull_fps(rtmp_url):
    now = time.time()
    with _PULL_FC_LOCK:
        timestamps = _PULL_FRAME_COUNTERS.get(rtmp_url)
        if not timestamps:
            return 0
        cutoff = now - _PULL_FC_WINDOW
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)
        if len(timestamps) < 2:
            return 0
        elapsed = timestamps[-1] - timestamps[0]
        if elapsed <= 0:
            return 0
        fps = (len(timestamps) - 1) / elapsed
    return round(fps, 1)


def cleanup_frame_counters():
    """清理过期的帧计数器，防止内存泄漏"""
    now = time.time()
    cleaned = 0
    with _PULL_FC_LOCK:
        stale_urls = []
        for url, timestamps in _PULL_FRAME_COUNTERS.items():
            cutoff = now - _PULL_FC_WINDOW
            while timestamps and timestamps[0] < cutoff:
                timestamps.pop(0)
            if not timestamps:
                stale_urls.append(url)
        for url in stale_urls:
            del _PULL_FRAME_COUNTERS[url]
            cleaned += 1
    return cleaned


def cleanup_push_timestamps():
    """清理过期的推流时间戳，防止内存泄漏"""
    now = time.time()
    max_age = 60.0
    cleaned = 0
    with _PUSH_TS_LOCK:
        stale_keys = []
        for key, ts in _PUSH_TIMESTAMPS.items():
            if now * 1000 - ts > max_age * 1000:
                stale_keys.append(key)
        for key in stale_keys:
            del _PUSH_TIMESTAMPS[key]
            cleaned += 1
    return cleaned
