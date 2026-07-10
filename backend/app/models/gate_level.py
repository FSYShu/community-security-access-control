"""
数据库模型 - 门禁终端层级
"""
from datetime import datetime
from app import db


class GateLevel(db.Model):
    """门禁终端层级模型"""
    __tablename__ = 'gate_levels'

    level_code = db.Column(db.Text, primary_key=True)
    level_name = db.Column(db.Text, nullable=False)
    security_level = db.Column(db.Text, nullable=False, default='一般')
    default_pass_policy = db.Column(db.Text, default='{}')
    allow_custom_override = db.Column(db.Integer, default=1)
    related_gate_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Text, default='active')

    def to_dict(self):
        return {
            'level_code': self.level_code,
            'level_name': self.level_name,
            'security_level': self.security_level,
            'default_pass_policy': self.default_pass_policy,
            'allow_custom_override': bool(self.allow_custom_override),
            'related_gate_count': self.related_gate_count,
            'status': self.status
        }