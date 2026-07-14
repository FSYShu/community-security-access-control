"""
数据库模型 - 视频推流通道
"""
from datetime import datetime, timezone, timedelta
from app import db

_CST = timezone(timedelta(hours=8))


class StreamChannel(db.Model):
    """视频推流通道模型"""
    __tablename__ = 'stream_channels'

    channel_id = db.Column(db.Text, primary_key=True)
    channel_name = db.Column(db.Text, nullable=False)
    push_key = db.Column(db.Text, nullable=False)
    camera_type = db.Column(db.Text, default='fixed')
    related_gate_id = db.Column(db.Integer, db.ForeignKey('gates.id'), nullable=True)
    related_zone_id = db.Column(db.Integer, db.ForeignKey('danger_zones.id'), nullable=True)
    push_protocol = db.Column(db.Text, default='rtmp')
    play_protocols = db.Column(db.Text, default='["rtmp","hls","flv"]')
    push_status = db.Column(db.Text, default='offline')
    record_storage_path = db.Column(db.Text, default='')
    created_at = db.Column(db.Text, default=lambda: datetime.now(_CST).isoformat())

    def to_dict(self):
        return {
            'channel_id': self.channel_id,
            'channel_name': self.channel_name,
            'camera_type': self.camera_type,
            'related_gate_id': self.related_gate_id,
            'related_zone_id': self.related_zone_id,
            'push_protocol': self.push_protocol,
            'play_protocols': self.play_protocols,
            'push_status': self.push_status,
            'record_storage_path': self.record_storage_path,
            'created_at': self.created_at
        }