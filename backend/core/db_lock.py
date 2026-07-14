"""
SQLite并发写入锁排队模块
使用threading.Lock + threading.Condition实现FIFO写入锁排队
"""
import logging
import threading
from functools import wraps

logger = logging.getLogger(__name__)


class WriteLockTimeoutError(Exception):
    """写入锁获取超时异常"""
    pass


class WriteLockQueue:
    """SQLite写入锁排队管理器，支持多线程FIFO顺序获取锁"""

    def __init__(self):
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._locked = False
        self._waiters = 0

    def acquire(self, timeout=5):
        """请求写入锁，超时后抛出WriteLockTimeoutError"""
        with self._lock:
            if not self._locked:
                self._locked = True
                return True
            self._waiters += 1
            try:
                result = self._condition.wait(timeout=timeout)
                if not result:
                    logger.error(f'WriteLock acquire timeout after {timeout}s, waiters={self._waiters}')
                    raise WriteLockTimeoutError(f'获取写入锁超时（{timeout}秒）')
                self._locked = True
                return True
            finally:
                self._waiters -= 1

    def release(self):
        """释放写入锁并通知队列中下一个等待者"""
        with self._lock:
            self._locked = False
            self._condition.notify()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


write_lock_queue = WriteLockQueue()


def with_write_lock(fn):
    """装饰器：自动获取和释放写入锁，超时时返回错误响应"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            write_lock_queue.acquire(timeout=5)
        except WriteLockTimeoutError as e:
            from flask import has_app_context
            from utils.response import error_response
            logger.error(f'with_write_lock timeout for {fn.__name__}: {str(e)}')
            if not has_app_context():
                return {'code': 408, 'message': str(e), 'data': None}, 408
            return error_response(message=str(e), code=408, http_status=408)
        try:
            return fn(*args, **kwargs)
        finally:
            write_lock_queue.release()
    return wrapper
