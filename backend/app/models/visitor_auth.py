"""
数据库模型 - 访客临时授权
"""
from datetime import datetime
from app import db


class VisitorAuth(db.Model):
    """访客临时授权模型"""
    __tablename__ = 'visitor_auths'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    visitor_name = db.Column(db.Text, nullable=False)
    visitor_face_image_path = db.Column(db.Text, default='')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    apply_gate_levels = db.Column(db.Text, default='[]')
    apply_time_range = db.Column(db.Text, default='{}')
    apply_source = db.Column(db.Text, default='gate_web')
    approval_status = db.Column(db.Text, default='pending')
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_time = db.Column(db.Text, default='')
    apply_time = db.Column(db.Text, default=lambda: datetime.utcnow().isoformat())
    visit_address = db.Column(db.Text, default='')

    def to_dict(self):
        return {
            'id': self.id,
            'visitor_name': self.visitor_name,
            'visitor_face_image_path': self.visitor_face_image_path,
            'owner_id': self.owner_id,
            'apply_gate_levels': self.apply_gate_levels,
            'apply_time_range': self.apply_time_range,
            'apply_source': self.apply_source,
            'approval_status': self.approval_status,
            'approver_id': self.approver_id,
            'approval_time': self.approval_time,
            'apply_time': self.apply_time,
            'visit_address': self.visit_address
        }