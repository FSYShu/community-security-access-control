"""
数据库模型 - 禁区配置
"""
from datetime import datetime
from app import db


class DangerZone(db.Model):
    """禁区配置模型"""
    __tablename__ = 'danger_zones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    zone_name = db.Column(db.String(50), nullable=False)
    camera_ids = db.Column(db.String(500), nullable=False)  # 关联摄像头ID列表
    safety_distance = db.Column(db.Float, nullable=False, default=2.0)  # 安全距离阈值(米)
    stay_duration = db.Column(db.Integer, nullable=False, default=30)  # 滞留告警时长(秒)
    status = db.Column(db.String(20), default='active')  # active/inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'zone_name': self.zone_name,
            'camera_ids': self.camera_ids,
            'safety_distance': self.safety_distance,
            'stay_duration': self.stay_duration,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }