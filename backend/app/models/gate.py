"""
数据库模型 - 门禁终端
"""
from datetime import datetime
from app import db


class Gate(db.Model):
    """门禁终端模型"""
    __tablename__ = 'gates'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gate_name = db.Column(db.Text, nullable=False)

    gate_level = db.Column(db.Text, nullable=False, default='community_gate')
    building_unit = db.Column(db.Text, default='')
    camera_id = db.Column(db.Integer, nullable=True)
    stream_channel_id = db.Column(db.Text, db.ForeignKey('stream_channels.channel_id'), nullable=True)
    push_key = db.Column(db.Text, default='')
    pass_time_config = db.Column(db.Text, default='{}')
    allowed_persons = db.Column(db.Text, default='{}')
    custom_pass_policy = db.Column(db.Text, default='{}')
    require_secondary_auth = db.Column(db.Integer, default=0)
    status = db.Column(db.Text, default='online')
    bound = db.Column(db.Integer, default=0)
    last_heartbeat = db.Column(db.Text, default='')
    calib_near_dist = db.Column(db.Float, nullable=True, default=None)
    calib_near_ratio = db.Column(db.Float, nullable=True, default=None)
    calib_far_dist = db.Column(db.Float, nullable=True, default=None)
    calib_far_ratio = db.Column(db.Float, nullable=True, default=None)
    created_at = db.Column(db.Text, default=lambda: datetime.utcnow().isoformat())
    updated_at = db.Column(db.Text, default=lambda: datetime.utcnow().isoformat(),
                           onupdate=lambda: datetime.utcnow().isoformat())

    def to_dict(self):
        return {
            'id': self.id,
            'gate_name': self.gate_name,

            'gate_level': self.gate_level,
            'building_unit': self.building_unit,
            'camera_id': self.camera_id,
            'stream_channel_id': self.stream_channel_id,
            'push_key': self.push_key,
            'pass_time_config': self.pass_time_config,
            'allowed_persons': self.allowed_persons,
            'custom_pass_policy': self.custom_pass_policy,
            'require_secondary_auth': bool(self.require_secondary_auth),
            'status': self.status,
            'bound': bool(self.bound),
            'display_status': 'unbound' if not self.bound else self.status,
            'last_heartbeat': self.last_heartbeat,
            'calib_near_dist': self.calib_near_dist,
            'calib_near_ratio': self.calib_near_ratio,
            'calib_far_dist': self.calib_far_dist,
            'calib_far_ratio': self.calib_far_ratio,
            'created_at': self.created_at
        }
