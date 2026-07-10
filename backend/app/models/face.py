"""
数据库模型 - 人脸信息
"""
from datetime import datetime
from app import db


class FaceInfo(db.Model):
    """人脸信息模型"""
    __tablename__ = 'face_info'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    person_type = db.Column(db.String(20), nullable=False)  # owner/visitor/blacklist
    person_name = db.Column(db.String(50), nullable=False)
    face_image_path = db.Column(db.String(500), nullable=False)
    face_feature = db.Column(db.Text, nullable=True)  # 人脸特征向量
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 访客关联业主
    auth_start_time = db.Column(db.DateTime, nullable=True)  # 访客授权开始时间
    auth_end_time = db.Column(db.DateTime, nullable=True)  # 访客授权结束时间
    allowed_gates = db.Column(db.String(500), nullable=True)  # 可通行门禁ID列表
    status = db.Column(db.String(20), default='active')  # active/expired/disabled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'person_type': self.person_type,
            'person_name': self.person_name,
            'face_image_path': self.face_image_path,
            'owner_id': self.owner_id,
            'auth_start_time': self.auth_start_time.isoformat() if self.auth_start_time else None,
            'auth_end_time': self.auth_end_time.isoformat() if self.auth_end_time else None,
            'allowed_gates': self.allowed_gates,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }