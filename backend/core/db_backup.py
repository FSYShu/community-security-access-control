"""
SQLite数据库备份工具
"""
import os
import shutil
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def backup_database(db_path, backup_dir=None, keep_days=7):
    """备份SQLite数据库文件"""
    if backup_dir is None:
        backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f'security_access_{timestamp}.db'
    backup_path = os.path.join(backup_dir, filename)

    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f'Database backed up to {backup_path}')
    except Exception as e:
        logger.error(f'Database backup failed: {str(e)}')
        return None

    _cleanup_old_backups(backup_dir, keep_days)
    return backup_path


def _cleanup_old_backups(backup_dir, keep_days):
    """清理过期备份文件"""
    cutoff = datetime.utcnow() - timedelta(days=keep_days)
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if not os.path.isfile(filepath):
            continue
        mtime = datetime.utcfromtimestamp(os.path.getmtime(filepath))
        if mtime < cutoff:
            try:
                os.remove(filepath)
                logger.info(f'Removed old backup: {filename}')
            except Exception as e:
                logger.error(f'Failed to remove backup {filename}: {str(e)}')