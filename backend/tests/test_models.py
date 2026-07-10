import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db as _db
from app.models import (User, FaceInfo, AlarmEvent, Gate, DangerZone,
                        PassRecord, DailyReport, GateLevel, StreamChannel,
                        VisitorAuth, AuditLog)


@pytest.fixture(scope='module')
def app():
    os.environ['FLASK_ENV'] = 'testing'
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


class TestUserModel:
    def test_create_user(self, app):
        with app.app_context():
            user = User(username='testuser', real_name='测试', role='owner')
            user.set_password('pass123')
            _db.session.add(user)
            _db.session.commit()
            assert user.id is not None

    def test_to_dict(self, app):
        with app.app_context():
            user = User(username='dictuser', real_name='字典测试', role='guard')
            user.set_password('pass123')
            _db.session.add(user)
            _db.session.commit()
            d = user.to_dict()
            assert 'id' in d
            assert 'username' in d
            assert 'real_name' in d
            assert 'role' in d
            assert 'phone' in d
            assert 'status' in d
            assert 'created_at' in d

    def test_password_hashing(self, app):
        with app.app_context():
            user = User(username='pwduser', real_name='密码测试', role='owner')
            user.set_password('mypassword')
            assert user.check_password('mypassword')
            assert not user.check_password('wrongpassword')


class TestGateLevelModel:
    def test_create_gate_level(self, app):
        with app.app_context():
            level = GateLevel(level_code='test_level', level_name='测试层级',
                              security_level='一般', default_pass_policy='{}')
            _db.session.add(level)
            _db.session.commit()
            assert level.level_code == 'test_level'

    def test_to_dict(self, app):
        with app.app_context():
            level = GateLevel(level_code='dict_level', level_name='字典层级',
                              security_level='较高', default_pass_policy='{}')
            _db.session.add(level)
            _db.session.commit()
            d = level.to_dict()
            assert 'level_code' in d
            assert 'level_name' in d


class TestAuditLogModel:
    def test_create_audit_log(self, app):
        with app.app_context():
            log = AuditLog(operator_id=1, operation_type='TEST_OP',
                           operation_content='test content', ip_address='127.0.0.1')
            _db.session.add(log)
            _db.session.commit()
            assert log.id is not None

    def test_to_dict(self, app):
        with app.app_context():
            log = AuditLog(operator_id=1, operation_type='DICT_OP',
                           operation_content='dict test', ip_address='127.0.0.1')
            _db.session.add(log)
            _db.session.commit()
            d = log.to_dict()
            assert 'id' in d
            assert 'operation_type' in d