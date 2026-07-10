"""
数据库模型 - 审计日志
"""
from datetime import datetime
from app import db


class AuditLog(db.Model):
    """审计日志模型"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    operation_type = db.Column(db.Text, nullable=False)
    operation_content = db.Column(db.Text, default='')
    operation_time = db.Column(db.Text, default=lambda: datetime.utcnow().isoformat())
    ip_address = db.Column(db.Text, default='')

    def to_dict(self):
        return {
            'id': self.id,
            'operator_id': self.operator_id,
            'operation_type': self.operation_type,
            'operation_content': self.operation_content,
            'operation_time': self.operation_time,
            'ip_address': self.ip_address
        }