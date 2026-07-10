"""
数据库模型 - 门禁终端
"""
from datetime import datetime
from app import db


class Gate(db.Model):
    """门禁终端模型"""
    __tablename__ = 'gates'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gate_name = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    camera_id = db.Column(db.Integer, nullable=False)  # 关联人脸采集摄像头
    pass_time_config = db.Column(db.String(500), nullable=False)  # 通行时段配置
    allowed_persons = db.Column(db.String(500), nullable=False)  # 可通行人员范围
    status = db.Column(db.String(20), default='online')  # online/offline/maintenance
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'gate_name': self.gate_name,
            'location': self.location,
            'camera_id': self.camera_id,
            'pass_time_config': self.pass_time_config,
            'allowed_persons': self.allowed_persons,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }