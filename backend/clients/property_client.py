"""
物业基础系统HTTP客户端
"""
import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)


class PropertyServiceClient:
    """封装物业基础系统HTTP接口调用"""

    def __init__(self):
        self._base_url = None
        self._timeout = 10

    @property
    def base_url(self):
        if self._base_url is None:
            try:
                self._base_url = current_app.config.get('PROPERTY_SERVICE_URL', '')
                self._timeout = current_app.config.get('PROPERTY_SERVICE_TIMEOUT', 10)
            except Exception:
                self._base_url = ''
        return self._base_url

    def get_owner_info(self, owner_id):
        """查询业主基础信息"""
        if not self.base_url:
            return None
        try:
            resp = requests.get(
                f'{self.base_url}/api/owners/{owner_id}',
                timeout=self._timeout
            )
            if resp.status_code == 200:
                return resp.json().get('data')
            return None
        except Exception as e:
            logger.error(f'PropertyServiceClient.get_owner_info failed: {str(e)}')
            return None

    def batch_import_owners(self, owner_data_list):
        """批量导入存量业主数据，创建User和FaceInfo记录"""
        from app import db
        from app.models.user import User
        from app.models.face import FaceInfo

        imported = 0
        for data in owner_data_list:
            username = data.get('username', '')
            if User.query.filter_by(username=username).first():
                continue

            user = User(
                username=username,
                real_name=data.get('real_name', ''),
                role='owner',
                phone=data.get('phone', '')
            )
            user.set_password(data.get('password', '123456'))
            db.session.add(user)
            imported += 1

        db.session.commit()
        return imported


property_client = PropertyServiceClient()