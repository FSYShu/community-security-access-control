"""
模型包 - 统一导出所有模型
"""
from app.models.user import User
from app.models.face import FaceInfo
from app.models.pass_record import PassRecord
from app.models.alarm import AlarmEvent
from app.models.danger_zone import DangerZone
from app.models.gate import Gate
from app.models.report import DailyReport

__all__ = [
    'User',
    'FaceInfo',
    'PassRecord',
    'AlarmEvent',
    'DangerZone',
    'Gate',
    'DailyReport'
]