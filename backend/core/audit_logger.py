"""
审计日志写入工具
"""
import logging
from datetime import datetime
from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app import db
from app.models.audit_log import AuditLog
from core.db_lock import with_write_lock

logger = logging.getLogger(__name__)


def log_audit(operation_type, operation_content='', operator_id=None, ip_address=None):
    """写入审计日志"""
    try:
        if operator_id is None:
            try:
                verify_jwt_in_request()
                current_user = get_jwt_identity()
                operator_id = int(current_user)
            except Exception:
                operator_id = None

        if ip_address is None:
            ip_address = request.remote_addr if request else ''

        log = AuditLog(
            operator_id=operator_id,
            operation_type=operation_type,
            operation_content=operation_content,
            operation_time=datetime.utcnow().isoformat(),
            ip_address=ip_address or ''
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f'Failed to write audit log: {str(e)}')
        try:
            db.session.rollback()
        except Exception:
            pass