import sys
import os
import json
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db as _db
from app.models.user import User
from app.models.face import FaceInfo


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
        _db.session.query(FaceInfo).delete()
        _db.session.query(User).delete()
        admin = User(username='admin', real_name='管理员', role='admin')
        admin.set_password('admin123')
        owner = User(username='owner1', real_name='业主1', role='owner')
        owner.set_password('pass123')
        _db.session.add_all([admin, owner])
        _db.session.commit()


def _login_admin(client):
    resp = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'admin123'})
    return resp.get_json().get('data', {}).get('token', '')


def _login_owner(client):
    resp = client.post('/api/v1/auth/login', json={'username': 'owner1', 'password': 'pass123'})
    return resp.get_json().get('data', {}).get('token', '')


class TestFaceList:
    def test_face_list_admin(self, client, app):
        token = _login_admin(client)
        resp = client.get('/api/v1/face/list', headers={'Authorization': f'Bearer {token}'})
        data = resp.get_json()
        assert data['code'] == 0
        assert 'items' in data['data']

    def test_face_list_owner_only_self(self, client, app):
        token = _login_owner(client)
        resp = client.get('/api/v1/face/list', headers={'Authorization': f'Bearer {token}'})
        data = resp.get_json()
        assert data['code'] == 0


class TestFaceAdd:
    def test_add_face_limit_3(self, client, app):
        token = _login_admin(client)
        for i in range(4):
            resp = client.post('/api/v1/face/add',
                               json={'person_name': 'test_user', 'person_type': 'owner', 'face_image': ''},
                               headers={'Authorization': f'Bearer {token}'})
            data = resp.get_json()
            if i < 3:
                assert data['code'] == 0
            else:
                assert data['code'] == 400

    def test_add_face_visitor_requires_owner(self, client, app):
        token = _login_admin(client)
        resp = client.post('/api/v1/face/add',
                           json={'person_name': 'visitor1', 'person_type': 'visitor', 'face_image': ''},
                           headers={'Authorization': f'Bearer {token}'})
        data = resp.get_json()
        assert data['code'] == 400


class TestFaceUpdateDelete:
    def test_update_face(self, client, app):
        token = _login_admin(client)
        with app.app_context():
            face = FaceInfo(person_name='update_test', person_type='owner', status='active')
            _db.session.add(face)
            _db.session.commit()
            face_id = face.id
        resp = client.put(f'/api/v1/face/{face_id}',
                          json={'person_name': 'updated_name'},
                          headers={'Authorization': f'Bearer {token}'})
        data = resp.get_json()
        assert data['code'] == 0

    def test_delete_face(self, client, app):
        token = _login_admin(client)
        with app.app_context():
            face = FaceInfo(person_name='delete_test', person_type='owner', status='active')
            _db.session.add(face)
            _db.session.commit()
            face_id = face.id
        resp = client.delete(f'/api/v1/face/{face_id}',
                             headers={'Authorization': f'Bearer {token}'})
        data = resp.get_json()
        assert data['code'] == 0


class TestFaceRegister:
    def test_face_register_missing_fields(self, client, app):
        token = _login_admin(client)
        resp = client.post('/api/v1/face/face-register',
                           json={'person_name': ''},
                           headers={'Authorization': f'Bearer {token}'})
        data = resp.get_json()
        assert data['code'] == 400