"""Helpers for preventing duplicate pending alarms."""

import threading
from contextlib import contextmanager


_alarm_write_lock = threading.Lock()


@contextmanager
def alarm_write_transaction():
    """Serialize alarm lookup plus insert across all detector threads."""
    with _alarm_write_lock:
        yield


def has_pending_alarm(source_id, alarm_type, source_type='gate'):
    """Return whether the latest alarm of this type is still unhandled."""
    from app.models.alarm import AlarmEvent

    latest = (
        AlarmEvent.query
        .filter_by(
            source_id=source_id,
            source_type=source_type,
            alarm_type=alarm_type,
        )
        .order_by(AlarmEvent.alarm_time.desc(), AlarmEvent.id.desc())
        .first()
    )
    return latest is not None and latest.handle_status != 'handled'
