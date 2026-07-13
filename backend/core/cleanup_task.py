"""
后台清理任务
定期清理过期的帧数据、时间戳等，防止内存泄漏和性能下降
"""
import threading
import time
import logging

logger = logging.getLogger(__name__)


def start_cleanup_task(app):
    """启动后台清理任务"""
    def cleanup_loop():
        interval = 30.0
        while True:
            time.sleep(interval)
            try:
                with app.app_context():
                    perform_cleanup()
            except Exception as e:
                logger.error('Cleanup task failed: {}'.format(str(e)))
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
    logger.info('Cleanup task started (interval={}s)'.format(30.0))


def perform_cleanup():
    """执行清理操作"""
    from core.rtmp_relay import (
        cleanup_stale,
        cleanup_pull_processes,
        cleanup_frame_counters,
        cleanup_push_timestamps
    )
    from core.shared_frame_store import cleanup_stale_frames
    
    results = {}
    
    try:
        cleaned = cleanup_stale()
        results['stale_ffmpeg_push'] = cleaned
    except Exception as e:
        logger.warning('cleanup_stale failed: {}'.format(str(e)))
    
    try:
        cleanup_pull_processes()
        results['stale_ffmpeg_pull'] = 'cleaned'
    except Exception as e:
        logger.warning('cleanup_pull_processes failed: {}'.format(str(e)))
    
    try:
        cleaned = cleanup_frame_counters()
        results['frame_counters'] = cleaned
    except Exception as e:
        logger.warning('cleanup_frame_counters failed: {}'.format(str(e)))
    
    try:
        cleaned = cleanup_push_timestamps()
        results['push_timestamps'] = cleaned
    except Exception as e:
        logger.warning('cleanup_push_timestamps failed: {}'.format(str(e)))
    
    try:
        cleaned = cleanup_stale_frames()
        results['stale_frames'] = cleaned
    except Exception as e:
        logger.warning('cleanup_stale_frames failed: {}'.format(str(e)))
    
    total = sum(v for v in results.values() if isinstance(v, int))
    if total > 0:
        logger.info('Cleanup completed: {}'.format(results))