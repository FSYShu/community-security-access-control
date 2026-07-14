"""
数据库模型 - 人脸信息
"""
from datetime import datetime
from app import db


class FaceInfo(db.Model):
    """人脸信息模型"""
    __tablename__ = 'face_info'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    person_type = db.Column(db.Text, nullable=False)
    person_name = db.Column(db.Text, nullable=False)
    face_image_path = db.Column(db.Text, nullable=False, default='')
    face_feature = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    auth_start_time = db.Column(db.Text, nullable=True)
    auth_end_time = db.Column(db.Text, nullable=True)
    allowed_gates = db.Column(db.Text, nullable=True)
    status = db.Column(db.Text, default='active')
    created_at = db.Column(db.Text, default=lambda: datetime.utcnow().isoformat())
    updated_at = db.Column(db.Text, default=lambda: datetime.utcnow().isoformat(),
                           onupdate=lambda: datetime.utcnow().isoformat())

    def to_dict(self):
        return {
            'id': self.id,
            'person_type': self.person_type,
            'person_name': self.person_name,
            'face_image_path': self.face_image_path,
            'owner_id': self.owner_id,
            'auth_start_time': self.auth_start_time,
            'auth_end_time': self.auth_end_time,
            'allowed_gates': self.allowed_gates,
            'status': self.status,
            'created_at': self.created_at
        }
