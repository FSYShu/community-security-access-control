"""
数据库模型 - 禁区配置
"""
import json
from datetime import datetime, timezone, timedelta
from app import db

_CST = timezone(timedelta(hours=8))


class DangerZone(db.Model):
    """禁区配置模型"""
    __tablename__ = 'danger_zones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    zone_name = db.Column(db.String(50), nullable=False)
    camera_ids = db.Column(db.String(500), nullable=False)
    zone_polygon = db.Column(db.Text, nullable=True)
    safety_distance = db.Column(db.Float, nullable=False, default=2.0)
    stay_duration = db.Column(db.Integer, nullable=False, default=30)
    alarm_level = db.Column(db.String(20), default='high')
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(_CST))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(_CST), onupdate=lambda: datetime.now(_CST))

    def get_polygon(self):
        if self.zone_polygon:
            try:
                return json.loads(self.zone_polygon)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def to_dict(self):
        return {
            'id': self.id,
            'zone_name': self.zone_name,
            'camera_ids': self.camera_ids,
            'zone_polygon': self.get_polygon(),
            'safety_distance': self.safety_distance,
            'stay_duration': self.stay_duration,
            'alarm_level': self.alarm_level,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }