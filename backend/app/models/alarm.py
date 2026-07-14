"""
数据库模型 - 告警事件
"""
from datetime import datetime, timezone, timedelta

_CST = timezone(timedelta(hours=8))


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
            'capture_image_path': self.capture_image_path,
            'video_path': self.video_path,
            'handle_status': self.handle_status,
            'handler_id': self.handler_id,
            'handle_time': _to_cst_str(self.handle_time),
            'handle_remark': self.handle_remark,
            'alarm_time': _to_cst_str(self.alarm_time)
        }
