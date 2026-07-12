"""
配置文件
支持开发、测试、生产三种环境
"""
import os


class BaseConfig:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    # JWT 配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 7200  # 2小时

    # 分页默认配置
    PER_PAGE = 20

    # 上传文件配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}

    # RTMP 服务器配置
    RTMP_SERVER_HOST = os.getenv('RTMP_SERVER_HOST', '20.214.147.223')
    RTMP_SERVER_PORT = int(os.getenv('RTMP_SERVER_PORT', 9090))

    # AI 服务配置
    AI_SERVICE_URL = os.getenv('AI_SERVICE_URL', 'http://localhost:8001')

    # 消息推送配置
    PUSH_SERVICE_URL = os.getenv('PUSH_SERVICE_URL', 'http://localhost:8002')


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True
    _db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(_db_dir, 'dev.db')
    )


class TestingConfig(BaseConfig):
    """测试环境配置"""
    TESTING = True
    _db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        'sqlite:///' + os.path.join(_db_dir, 'test.db')
    )
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DEBUG = False
    _db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(_db_dir, 'prod.db')
    )
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时