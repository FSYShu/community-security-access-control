"""
社区安防门禁系统 - Flask 应用工厂
"""
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import inspect as sa_inspect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)



def create_app(config_name=None):
    """应用工厂函数"""
    app = Flask(__name__)

    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(get_config(config_name))

    data_dir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, supports_credentials=True)
    limiter.init_app(app)


    with app.app_context():
        from sqlalchemy import text
        try:
            db.engine.execute(text('PRAGMA journal_mode=WAL'))
        except Exception:
            pass

    register_blueprints(app)
    register_error_handlers(app)

    with app.app_context():
        init_database(app)

    if os.getenv('ENABLE_DANGER_ZONE_DETECTOR', '1') == '1':
        from app.danger_zone.danger_zone_background import start_danger_zone_detector
        start_danger_zone_detector(app)

    from app.device_tamper_monitor import start_device_tamper_monitor
    start_device_tamper_monitor(app)

    from core.cleanup_task import start_cleanup_task
    start_cleanup_task(app)

    return app


def get_config(config_name):
    """获取配置类"""
    config_map = {
        'development': 'config.DevelopmentConfig',
        'testing': 'config.TestingConfig',
        'production': 'config.ProductionConfig'
    }
    return config_map.get(config_name, 'config.DevelopmentConfig')


def register_blueprints(app):
    """注册所有蓝图"""
    from app.auth import auth_bp
    from app.face import face_bp
    from app.alarm import alarm_bp
    from app.danger_zone import danger_zone_bp
    from app.video_monitor import video_monitor_bp
    from app.gate import gate_bp
    from app.report import report_bp
    from app.property import property_bp
    from app.gate_level import gate_level_bp
    from app.stream import stream_bp
    from app.visitor_auth import visitor_auth_bp
    from app.audit import audit_bp
    from app.dashboard import dashboard_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(face_bp, url_prefix='/api/v1/face')
    app.register_blueprint(alarm_bp, url_prefix='/api/v1/alarm')
    app.register_blueprint(danger_zone_bp, url_prefix='/api/v1/danger-zone')
    app.register_blueprint(video_monitor_bp, url_prefix='/api/v1/video-monitor')
    app.register_blueprint(gate_bp, url_prefix='/api/v1/gate')
    app.register_blueprint(report_bp, url_prefix='/api/v1/report')
    app.register_blueprint(property_bp, url_prefix='/api/v1/property')
    app.register_blueprint(gate_level_bp, url_prefix='/api/v1/gate-level')
    app.register_blueprint(stream_bp, url_prefix='/api/v1/stream')
    app.register_blueprint(visitor_auth_bp, url_prefix='/api/v1/visitor-auth')
    app.register_blueprint(audit_bp, url_prefix='/api/v1/audit')
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1/dashboard')


def register_error_handlers(app):
    """注册全局错误处理"""
    from utils.response import error_response

    @app.errorhandler(400)
    def bad_request(e):
        return error_response(message='请求参数错误', code=400)

    @app.errorhandler(401)
    def unauthorized(e):
        return error_response(message='未授权，请重新登录', code=401)

    @app.errorhandler(403)
    def forbidden(e):
        return error_response(message='拒绝访问', code=403)

    @app.errorhandler(404)
    def not_found(e):
        return error_response(message='请求资源不存在', code=404)

    @app.errorhandler(409)
    def conflict(e):
        return error_response(message='资源冲突', code=409)

    @app.errorhandler(422)
    def unprocessable(e):
        return error_response(message='不可处理的实体', code=422)

    @app.errorhandler(500)
    def internal_error(e):
        return error_response(message='服务器内部错误', code=500)


def init_database(app):
    """初始化数据库：创建表、插入默认数据"""
    from app.models import User, GateLevel

    db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_path.startswith('sqlite:///'):
        db_file = db_path.replace('sqlite:///', '')
        if not os.path.exists(db_file):
            logger.info('Database not found, creating tables...')
            db.create_all()
            _seed_default_data()
        else:
            db.create_all()
            _migrate_schema(db)
            _migrate_danger_zone_columns()
            _migrate_daily_report_columns()
            _migrate_gate_columns()
    else:
        db.create_all()
        _migrate_schema(db)


def _migrate_schema(database):
    """自动迁移：为已有表添加缺失的列"""
    with database.engine.connect() as conn:
        try:
            conn.execute(db.text('ALTER TABLE gates ADD COLUMN bound INTEGER DEFAULT 0'))
            conn.commit()
            logger.info('Migrated: added bound column to gates')
        except Exception:
            pass
        try:
            conn.execute(db.text("ALTER TABLE gates ADD COLUMN last_heartbeat TEXT DEFAULT ''"))
            conn.commit()
            logger.info('Migrated: added last_heartbeat column to gates')
        except Exception:
            pass
        try:
            col_names = [col['name'] for col in sa_inspect(db.engine).get_columns('gates')]
            if 'location' in col_names:
                conn.execute(db.text('ALTER TABLE gates DROP COLUMN location'))
                conn.commit()
                logger.info('Migrated: dropped location column from gates')
        except Exception:
            pass
        try:
            conn.execute(db.text('ALTER TABLE gates ADD COLUMN calib_near_dist REAL'))
            conn.commit()
            logger.info('Migrated: added calib_near_dist column to gates')
        except Exception:
            pass
        try:
            conn.execute(db.text('ALTER TABLE gates ADD COLUMN calib_near_ratio REAL'))
            conn.commit()
            logger.info('Migrated: added calib_near_ratio column to gates')
        except Exception:
            pass
        try:
            conn.execute(db.text('ALTER TABLE gates ADD COLUMN calib_far_dist REAL'))
            conn.commit()
            logger.info('Migrated: added calib_far_dist column to gates')
        except Exception:
            pass
        try:
            conn.execute(db.text('ALTER TABLE gates ADD COLUMN calib_far_ratio REAL'))
            conn.commit()
            logger.info('Migrated: added calib_far_ratio column to gates')
        except Exception:
            pass
        try:
            conn.execute(db.text("ALTER TABLE visitor_auths ADD COLUMN visit_address TEXT DEFAULT ''"))
            conn.commit()
            logger.info('Migrated: added visit_address column to visitor_auths')
        except Exception:
            pass


def _migrate_danger_zone_columns():
    """为已存在的danger_zones表添加新列"""
    from sqlalchemy import text, inspect
    try:
        insp = inspect(db.engine)
        if 'danger_zones' in insp.get_table_names():
            existing = {col['name'] for col in insp.get_columns('danger_zones')}
            if 'zone_polygon' not in existing:
                db.session.execute(text('ALTER TABLE danger_zones ADD COLUMN zone_polygon TEXT'))
                db.session.commit()
                logger.info('Added zone_polygon column to danger_zones')
            if 'alarm_level' not in existing:
                db.session.execute(text("ALTER TABLE danger_zones ADD COLUMN alarm_level VARCHAR(20) DEFAULT 'high'"))
                db.session.commit()
                logger.info('Added alarm_level column to danger_zones')
    except Exception as e:
        logger.warning('Migration check failed (non-critical): {}'.format(str(e)))


def _migrate_daily_report_columns():
    """Add AI report fields to existing daily_reports tables."""
    from sqlalchemy import inspect, text

    columns = {
        'ai_summary': "TEXT DEFAULT ''",
        'risk_level': "TEXT DEFAULT 'low'",
        'risk_score': 'INTEGER DEFAULT 0',
        'recommendations': "TEXT DEFAULT '[]'",
        'workflow_source': "TEXT DEFAULT 'local_rules'",
    }
    try:
        inspector = inspect(db.engine)
        if 'daily_reports' not in inspector.get_table_names():
            return
        existing = {item['name'] for item in inspector.get_columns('daily_reports')}
        for name, definition in columns.items():
            if name in existing:
                continue
            db.session.execute(text(
                'ALTER TABLE daily_reports ADD COLUMN {} {}'.format(name, definition)
            ))
            db.session.commit()
            logger.info('Added daily_reports.%s', name)
    except Exception as exc:
        db.session.rollback()
        logger.warning('Daily report migration failed (non-critical): %s', exc)


def _migrate_gate_columns():
    """为已存在的gates表添加新列"""
    from sqlalchemy import text, inspect
    try:
        insp = inspect(db.engine)
        if 'gates' in insp.get_table_names():
            existing = {col['name'] for col in insp.get_columns('gates')}
            if 'parent_gate_id' not in existing:
                db.session.execute(text('ALTER TABLE gates ADD COLUMN parent_gate_id INTEGER REFERENCES gates(id)'))
                db.session.commit()
                logger.info('Added parent_gate_id column to gates')
    except Exception as e:
        logger.warning('Gate migration check failed (non-critical): {}'.format(str(e)))


def _seed_default_data():
    """插入默认数据"""
    from app.models import User, GateLevel

    if not User.query.filter_by(username='admin0').first():
        admin0 = User(username='admin0', real_name='管理员', role='admin')
        admin0.set_password('csac123456')
        db.session.add(admin0)

    default_levels = [
        GateLevel(level_code='community_gate', level_name='社区大门', security_level='较高',
                  default_pass_policy='{"allow_owner": true, "allow_visitor": true, "allow_stranger": false}'),
        GateLevel(level_code='unit_door', level_name='单元门', security_level='一般',
                  default_pass_policy='{"allow_owner": true, "allow_visitor": true, "allow_stranger": false}'),
        GateLevel(level_code='entrance_door', level_name='入户门', security_level='较高',
                  default_pass_policy='{"allow_owner": true, "allow_visitor": false, "allow_stranger": false}'),
        GateLevel(level_code='dangerous_area', level_name='危险防护区域', security_level='最高',
                  default_pass_policy='{"allow_owner": false, "allow_visitor": false, "allow_stranger": false}')
    ]
    for level in default_levels:
        if not GateLevel.query.get(level.level_code):
            db.session.add(level)

    db.session.commit()
    logger.info('Default data seeded.')
