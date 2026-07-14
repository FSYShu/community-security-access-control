"""
数据库模型 - 用户
"""
from datetime import datetime, timezone, timedelta
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

_CST = timezone(timedelta(hours=8))


class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)

    role = db.Column(db.Text, nullable=False, default='owner')

    status = db.Column(db.Text, default='active')
    created_at = db.Column(db.Text, default=lambda: datetime.now(_CST).isoformat())
    updated_at = db.Column(db.Text, default=lambda: datetime.now(_CST).isoformat(),
                           onupdate=lambda: datetime.now(_CST).isoformat())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at
        }
