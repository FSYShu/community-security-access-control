"""
数据库模型 - 告警事件
"""
import os
from datetime import datetime, timezone, timedelta

_CST = timezone(timedelta(hours=8))

_CAPTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'data', 'alarm_captures'
)


def _path_to_capture_url(abs_path):
    if not abs_path:
        return None
    if abs_path.startswith('alarm_captures/'):
        return abs_path
    try:
        rel = os.path.relpath(abs_path, _CAPTURE_DIR)
        if not rel.startswith('..'):
            return 'alarm_captures/{}'.format(rel.replace(os.sep, '/'))
    except ValueError:
        pass
    if 'alarm_captures' in abs_path:
        filename = abs_path.rsplit('alarm_captures', 1)[-1].replace(os.sep, '/').lstrip('/')
        if filename:
            return 'alarm_captures/{}'.format(filename)
    return abs_path


def _to_cst_str(time_str):
    if not time_str:
        return time_str
    try:
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        if dt.tzinfo is not None:
            dt = dt.astimezone(_CST)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, AttributeError):
        return time_str
from app import db


class AlarmEvent(db.Model):
    """告警事件模型"""
    __tablename__ = 'alarm_events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alarm_type = db.Column(db.Text, nullable=False)
    alarm_level = db.Column(db.Text, nullable=False)
    source_id = db.Column(db.Integer, nullable=False)
    source_type = db.Column(db.Text, nullable=False)
    alarm_description = db.Column(db.Text, nullable=False)
    capture_image_path = db.Column(db.Text, nullable=True)
    video_path = db.Column(db.Text, nullable=True)
    handle_status = db.Column(db.Text, default='pending')
    handler_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    handle_time = db.Column(db.Text, nullable=True)
    handle_remark = db.Column(db.Text, nullable=True)
    alarm_time = db.Column(db.Text, default=lambda: datetime.now(_CST).isoformat())

    def to_dict(self):
        return {
            'id': self.id,
            'alarm_type': self.alarm_type,
            'alarm_level': self.alarm_level,
            'source_id': self.source_id,
            'source_type': self.source_type,
            'alarm_description': self.alarm_description,
            'capture_image_path': _path_to_capture_url(self.capture_image_path),
            'video_path': _path_to_capture_url(self.video_path),
            'handle_status': self.handle_status,
            'handler_id': self.handler_id,
            'handle_time': _to_cst_str(self.handle_time),
            'handle_remark': self.handle_remark,
            'alarm_time': _to_cst_str(self.alarm_time)
        }
