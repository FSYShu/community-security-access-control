import sys
import os
import json
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db as _db
from app.models.user import User


@pytest.fixture(scope='module')
def app():
    os.environ['FLASK_ENV'] = 'testing'
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='module')
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        _db.session.query(User).delete()
        _db.session.commit()
        admin = User(username='admin', real_name='管理员', role='admin')
        admin.set_password('admin123')
        _db.session.add(admin)
        _db.session.commit()


def _login(client, username='admin', password='admin123'):
    resp = client.post('/api/v1/auth/login', json={'username': username, 'password': password})
    data = resp.get_json()
    return data.get('data', {}).get('token', '')


class TestLogin:
    def test_login_success(self, client, app):
        resp = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'admin123'})
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['code'] == 0
        assert 'token' in data.get('data', {})

    def test_login_wrong_password(self, client, app):
        resp = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'wrong'})
        data = resp.get_json()
        assert data['code'] == 401

    def test_login_disabled_account(self, client, app):
        with app.app_context():
            user = User(username='disabled_user', real_name='禁用用户', role='owner', status='disabled')
            user.set_password('pass123')
            _db.session.add(user)
            _db.session.commit()
        resp = client.post('/api/v1/auth/login', json={'username': 'disabled_user', 'password': 'pass123'})
        data = resp.get_json()
        assert data['code'] == 403

    def test_login_empty_fields(self, client, app):
        resp = client.post('/api/v1/auth/login', json={'username': '', 'password': ''})
        data = resp.get_json()
        assert data['code'] == 400


class TestLogout:
    def test_logout_success(self, client, app):
        token = _login(client)
        resp = client.post('/api/v1/auth/logout', headers={'Authorization': f'Bearer {token}'})
        data = resp.get_json()
        assert data['code'] == 0


class TestGetUserInfo:
    def test_get_user_info(self, client, app):
        token = _login(client)
        resp = client.get('/api/v1/auth/userinfo', headers={'Authorization': f'Bearer {token}'})
        data = resp.get_json()
        assert data['code'] == 0
        assert data['data']['username'] == 'admin'


class TestChangePassword:
    def test_change_password_success(self, client, app):
        token = _login(client)
        resp = client.post('/api/v1/auth/change-password',
                           json={'old_password': 'admin123', 'new_password': 'newpass456'},
                           headers={'Authorization': f'Bearer {token}'})
        data = resp.get_json()
        assert data['code'] == 0

    def test_change_password_wrong_old(self, client, app):
        token = _login(client)
        resp = client.post('/api/v1/auth/change-password',
                           json={'old_password': 'wrong', 'new_password': 'newpass456'},
                           headers={'Authorization': f'Bearer {token}'})
        data = resp.get_json()
        assert data['code'] == 400


class TestUserList:
    def test_list_users_admin(self, client, app):
        token = _login(client)
        resp = client.get('/api/v1/auth/users', headers={'Authorization': f'Bearer {token}'})
        data = resp.get_json()
        assert data['code'] == 0
        assert 'items' in data['data']