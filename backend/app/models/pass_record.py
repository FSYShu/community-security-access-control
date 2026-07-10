"""
数据库模型 - 通行记录
"""
from datetime import datetime
from app import db


class PassRecord(db.Model):
    """通行记录模型"""
    __tablename__ = 'pass_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gate_id = db.Column(db.Integer, db.ForeignKey('gates.id'), nullable=False)
    face_id = db.Column(db.Integer, db.ForeignKey('face_info.id'), nullable=True)
    pass_result = db.Column(db.String(20), nullable=False)  # pass/reject
    reject_reason = db.Column(db.String(50), nullable=True)  # stranger/blacklist/liveness_fail/auth_expired
    capture_image_path = db.Column(db.String(500), nullable=False)
    pass_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'gate_id': self.gate_id,
            'face_id': self.face_id,
            'pass_result': self.pass_result,
            'reject_reason': self.reject_reason,
            'capture_image_path': self.capture_image_path,
            'pass_time': self.pass_time.isoformat() if self.pass_time else None
        }