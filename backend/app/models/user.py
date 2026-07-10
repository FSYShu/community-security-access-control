"""
数据库模型 - 用户
"""
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    real_name = db.Column(db.Text, nullable=False)
    role = db.Column(db.Text, nullable=False, default='owner')
    phone = db.Column(db.Text, unique=True, nullable=True)
    status = db.Column(db.Text, default='active')
    created_at = db.Column(db.Text, default=lambda: datetime.utcnow().isoformat())
    updated_at = db.Column(db.Text, default=lambda: datetime.utcnow().isoformat(),
                           onupdate=lambda: datetime.utcnow().isoformat())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'role': self.role,
            'phone': self.phone,
            'status': self.status,
            'created_at': self.created_at
        }
