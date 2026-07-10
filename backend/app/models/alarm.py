"""
数据库模型 - 告警事件
"""
from datetime import datetime
from app import db


class AlarmEvent(db.Model):
    """告警事件模型"""
    __tablename__ = 'alarm_events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alarm_type = db.Column(db.String(30), nullable=False)  # face_alarm/zone_intrusion/behavior_abnormal/danger_alarm
    alarm_level = db.Column(db.String(20), nullable=False)  # normal/warning/critical
    source_id = db.Column(db.Integer, nullable=False)  # 门禁终端ID或监控区域ID
    source_type = db.Column(db.String(30), nullable=False)  # gate/monitor
    alarm_description = db.Column(db.Text, nullable=False)
    capture_image_path = db.Column(db.String(500), nullable=True)
    video_path = db.Column(db.String(500), nullable=True)
    handle_status = db.Column(db.String(20), default='pending')  # pending/processing/handled/false_alarm
    handler_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    handle_time = db.Column(db.DateTime, nullable=True)
    handle_remark = db.Column(db.Text, nullable=True)
    alarm_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
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
            'handle_time': self.handle_time.isoformat() if self.handle_time else None,
            'handle_remark': self.handle_remark,
            'alarm_time': self.alarm_time.isoformat() if self.alarm_time else None
        }