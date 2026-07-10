"""
视频推流通道管理蓝图
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app import db
from app.models.stream_channel import StreamChannel
from utils.response import success_response, error_response
from utils.permissions import admin_required, guard_or_admin_required
from core.db_lock import with_write_lock
from core.audit_logger import log_audit

stream_bp = Blueprint('stream', __name__)


@stream_bp.route('/list', methods=['GET'])
@jwt_required()
def list_streams():
    """获取推流通道列表"""
    channels = StreamChannel.query.all()
    return success_response(data=[c.to_dict() for c in channels])


@stream_bp.route('/add', methods=['POST'])
@admin_required
@with_write_lock
def add_stream():
    """新增推流通道"""
    data = request.get_json()
    channel_id = data.get('channel_id', '')
    channel_name = data.get('channel_name', '')

    if not channel_id or not channel_name:
        return error_response(message='通道ID和名称不能为空', code=400)

    if StreamChannel.query.get(channel_id):
        return error_response(message='通道ID已存在', code=400)

    import secrets
    channel = StreamChannel(
        channel_id=channel_id,
        channel_name=channel_name,
        push_key=secrets.token_hex(16),
        camera_type=data.get('camera_type', 'fixed'),
        push_protocol=data.get('push_protocol', 'rtmp'),
        play_protocols=data.get('play_protocols', '["rtmp","hls","flv"]'),
        record_storage_path=data.get('record_storage_path', '')
    )
    db.session.add(channel)
    db.session.commit()
    log_audit(operation_type='add_stream', operation_content=f'新增推流通道: {channel_id}')
    return success_response(data=channel.to_dict(), message='新增成功')


@stream_bp.route('/<channel_id>/status', methods=['GET'])
@guard_or_admin_required
def get_stream_status(channel_id):
    """获取通道状态"""
    channel = StreamChannel.query.get(channel_id)
    if not channel:
        return error_response(message='通道不存在', code=404)
    return success_response(data={'channel_id': channel.channel_id, 'push_status': channel.push_status})


@stream_bp.route('/<channel_id>/record', methods=['POST'])
@guard_or_admin_required
def request_record(channel_id):
    """请求录制短视频"""
    channel = StreamChannel.query.get(channel_id)
    if not channel:
        return error_response(message='通道不存在', code=404)
    return success_response(message='录制请求已提交', data={'channel_id': channel_id})


@stream_bp.route('/<channel_id>/playback', methods=['GET'])
@guard_or_admin_required
def get_playback(channel_id):
    """获取回放地址"""
    channel = StreamChannel.query.get(channel_id)
    if not channel:
        return error_response(message='通道不存在', code=404)
    return success_response(data={'channel_id': channel_id, 'record_storage_path': channel.record_storage_path})