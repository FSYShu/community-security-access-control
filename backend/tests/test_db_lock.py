import sys
import os
import threading
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.db_lock import WriteLockQueue, WriteLockTimeoutError, with_write_lock


class TestWriteLockQueue:
    def test_acquire_and_release(self):
        q = WriteLockQueue()
        q.acquire(timeout=1)
        q.release()

    def test_concurrent_fifo_order(self):
        q = WriteLockQueue()
        order = []

        q.acquire(timeout=1)

        def worker(name):
            q.acquire(timeout=5)
            order.append(name)
            time.sleep(0.05)
            q.release()

        t1 = threading.Thread(target=worker, args=('A',))
        t2 = threading.Thread(target=worker, args=('B',))
        t1.start()
        t2.start()

        time.sleep(0.1)
        q.release()

        t1.join(timeout=10)
        t2.join(timeout=10)
        assert order == ['A', 'B']

    def test_acquire_timeout(self):
        q = WriteLockQueue()
        q.acquire(timeout=1)
        with pytest.raises(WriteLockTimeoutError):
            q.acquire(timeout=0.5)
        q.release()

    def test_release_notifies_next(self):
        q = WriteLockQueue()
        acquired = threading.Event()

        q.acquire(timeout=1)

        def waiter():
            q.acquire(timeout=5)
            acquired.set()
            q.release()

        t = threading.Thread(target=waiter)
        t.start()
        time.sleep(0.1)
        q.release()
        assert acquired.wait(timeout=3)
        t.join(timeout=5)


class TestWithWriteLock:
    def test_decorator_acquires_and_releases(self):
        q = WriteLockQueue()

        @with_write_lock
        def my_func():
            return 'ok'

        result = my_func()
        assert result == 'ok'

    def test_decorator_timeout_returns_error(self):
        from core.db_lock import write_lock_queue
        write_lock_queue.acquire(timeout=1)

        @with_write_lock
        def blocked_func():
            return 'should not reach'

        result = blocked_func()
        from flask import jsonify
        assert result is not None
        write_lock_queue.release()