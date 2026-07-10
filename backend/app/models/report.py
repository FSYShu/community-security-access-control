"""
数据库模型 - 安防监控日报
"""
from datetime import datetime
from app import db


class DailyReport(db.Model):
    """安防监控日报模型"""
    __tablename__ = 'daily_reports'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    report_date = db.Column(db.Date, unique=True, nullable=False)
    pass_stats = db.Column(db.Text, nullable=False)  # 通行统计JSON
    alarm_stats = db.Column(db.Text, nullable=False)  # 告警统计JSON
    abnormal_events = db.Column(db.Text, nullable=True)  # 异常事件汇总JSON
    generate_status = db.Column(db.String(20), default='generating')  # generating/generated/failed
    generated_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'pass_stats': self.pass_stats,
            'alarm_stats': self.alarm_stats,
            'abnormal_events': self.abnormal_events,
            'generate_status': self.generate_status,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }