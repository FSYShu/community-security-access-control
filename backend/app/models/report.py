"""
数据库模型 - 安防监控日报
"""
from datetime import datetime
from app import db


class DailyReport(db.Model):
    """安防监控日报模型"""
    __tablename__ = 'daily_reports'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    report_date = db.Column(db.Text, unique=True, nullable=False)
    pass_stats = db.Column(db.Text, default='{}')
    alarm_stats = db.Column(db.Text, default='{}')
    abnormal_events = db.Column(db.Text, default='[]')
    ai_summary = db.Column(db.Text, default='')
    risk_level = db.Column(db.Text, default='low')
    risk_score = db.Column(db.Integer, default=0)
    recommendations = db.Column(db.Text, default='[]')
    workflow_source = db.Column(db.Text, default='local_rules')
    generate_status = db.Column(db.Text, default='generating')
    generated_at = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'report_date': self.report_date,
            'pass_stats': self.pass_stats,
            'alarm_stats': self.alarm_stats,
            'abnormal_events': self.abnormal_events,
            'ai_summary': self.ai_summary,
            'risk_level': self.risk_level,
            'risk_score': self.risk_score,
            'recommendations': self.recommendations,
            'workflow_source': self.workflow_source,
            'generate_status': self.generate_status,
            'generated_at': self.generated_at
        }
