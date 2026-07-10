"""
配置文件
支持开发、测试、生产三种环境
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')


class BaseConfig:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ENGINE_OPTIONS = {'connect_args': {'timeout': 10}}

    DB_FILE_PATH = os.path.join(DATA_DIR, 'security_access.db')

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 7200

    PER_PAGE = 20

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}

    AI_SERVICE_URL = os.getenv('AI_SERVICE_URL', 'http://localhost:8001')

    PUSH_SERVICE_URL = os.getenv('PUSH_SERVICE_URL', 'http://localhost:8002')

    RTMP_SERVER_HOST = os.getenv('RTMP_SERVER_HOST', '20.214.147.223')
    RTMP_SERVER_PORT = int(os.getenv('RTMP_SERVER_PORT', 9090))
    VIDEO_FRAME_SKIP = int(os.getenv('VIDEO_FRAME_SKIP', 5))
    VIDEO_MAX_WIDTH = int(os.getenv('VIDEO_MAX_WIDTH', 640))
    VIDEO_DETECT_WIDTH = int(os.getenv('VIDEO_DETECT_WIDTH', 320))
    VIDEO_JPEG_QUALITY = int(os.getenv('VIDEO_JPEG_QUALITY', 45))
    VIDEO_TARGET_FPS = int(os.getenv('VIDEO_TARGET_FPS', 25))
    RECORDINGS_BASE_URL = os.getenv('RECORDINGS_BASE_URL', 'http://20.214.147.223:9092')

    PROPERTY_SERVICE_URL = os.getenv('PROPERTY_SERVICE_URL', '')
    PROPERTY_SERVICE_TIMEOUT = int(os.getenv('PROPERTY_SERVICE_TIMEOUT', 10))

    REGISTERED_FACES_FILE = os.path.join(BASE_DIR, 'registered_faces.json')


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(DATA_DIR, 'security_access_dev.db')
    )


class TestingConfig(BaseConfig):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        'sqlite:///' + os.path.join(DATA_DIR, 'security_access_test.db')
    )
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(DATA_DIR, 'security_access.db')
    )
    JWT_ACCESS_TOKEN_EXPIRES = 3600
