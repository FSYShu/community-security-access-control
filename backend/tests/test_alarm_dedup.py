import os
import sys

import numpy as np
import pytest
from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import db
from app.models import AlarmEvent
from app.video_monitor.dangerous_behavior_sse import (
    _active_alarm_states,
    _record_alarm,
    _tailgating_last_alarm_at,
    _record_tailgating_alarm,
)


@pytest.fixture
def alarm_app():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def reset_alarm_state():
    _active_alarm_states.clear()
    _tailgating_last_alarm_at.clear()
    yield
    _active_alarm_states.clear()
    _tailgating_last_alarm_at.clear()


def _frame():
    return np.zeros((80, 120, 3), dtype=np.uint8)


def _record_tamper(app, gate_id, alarm_type):
    _record_alarm(app, gate_id, alarm_type, _frame(), {}, cooldown=0)


def test_pending_alarm_is_written_once_per_gate_and_type(alarm_app):
    _record_tamper(alarm_app, 1, 'open_flame')
    _active_alarm_states.clear()
    _record_tamper(alarm_app, 1, 'open_flame')

    with alarm_app.app_context():
        alarms = AlarmEvent.query.filter_by(
            source_id=1, source_type='gate', alarm_type='open_flame'
        ).all()
        assert len(alarms) == 1
        assert alarms[0].handle_status == 'pending'


def test_fire_and_smoke_have_independent_pending_alarm_slots(alarm_app):
    _record_tamper(alarm_app, 1, 'open_flame')
    _active_alarm_states.clear()
    _record_tamper(alarm_app, 1, 'smoke')

    with alarm_app.app_context():
        alarms = AlarmEvent.query.filter_by(source_id=1).all()
        assert {alarm.alarm_type for alarm in alarms} == {'open_flame', 'smoke'}


def test_handled_alarm_allows_a_new_alarm_of_same_type(alarm_app):
    _record_tamper(alarm_app, 1, 'smoke')
    with alarm_app.app_context():
        alarm = AlarmEvent.query.filter_by(
            source_id=1, alarm_type='smoke'
        ).one()
        alarm.handle_status = 'handled'
        db.session.commit()

    _active_alarm_states.clear()
    _record_tamper(alarm_app, 1, 'smoke')

    with alarm_app.app_context():
        assert AlarmEvent.query.filter_by(
            source_id=1, alarm_type='smoke'
        ).count() == 2


def test_pending_tailgating_alarm_is_deduplicated(alarm_app):
    _record_tailgating_alarm(alarm_app, 1, _frame(), [1, 2], 2, cooldown=0)
    _tailgating_last_alarm_at.clear()
    _record_tailgating_alarm(alarm_app, 1, _frame(), [1, 2], 3, cooldown=0)

    with alarm_app.app_context():
        assert AlarmEvent.query.filter_by(
            source_id=1, alarm_type='tailgating'
        ).count() == 1


def test_pending_alarm_deduplication_is_scoped_to_gate(alarm_app):
    _record_tamper(alarm_app, 1, 'smoke')
    _active_alarm_states.clear()
    _record_tamper(alarm_app, 2, 'smoke')

    with alarm_app.app_context():
        assert AlarmEvent.query.filter_by(alarm_type='smoke').count() == 2
