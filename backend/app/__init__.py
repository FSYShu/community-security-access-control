"""
社区安防门禁系统 - Flask 应用工厂
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 初始化扩展
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

    # 加载配置
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(get_config(config_name))

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, supports_credentials=True)
    limiter.init_app(app)

    # 注册蓝图
    register_blueprints(app)

    # 注册错误处理
    register_error_handlers(app)

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

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(face_bp, url_prefix='/api/v1/face')
    app.register_blueprint(alarm_bp, url_prefix='/api/v1/alarm')
    app.register_blueprint(danger_zone_bp, url_prefix='/api/v1/danger-zone')
    app.register_blueprint(video_monitor_bp, url_prefix='/api/v1/video-monitor')
    app.register_blueprint(gate_bp, url_prefix='/api/v1/gate')
    app.register_blueprint(report_bp, url_prefix='/api/v1/report')
    app.register_blueprint(property_bp, url_prefix='/api/v1/property')


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

    @app.errorhandler(500)
    def internal_error(e):
        return error_response(message='服务器内部错误', code=500)