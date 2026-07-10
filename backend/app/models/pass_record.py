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
    pass_result = db.Column(db.Text, nullable=False)
    reject_reason = db.Column(db.Text, nullable=True)
    capture_image_path = db.Column(db.Text, default='')
    pass_time = db.Column(db.Text, default=lambda: datetime.utcnow().isoformat())

    def to_dict(self):
        return {
            'id': self.id,
            'gate_id': self.gate_id,
            'face_id': self.face_id,
            'pass_result': self.pass_result,
            'reject_reason': self.reject_reason,
            'capture_image_path': self.capture_image_path,
            'pass_time': self.pass_time
        }
