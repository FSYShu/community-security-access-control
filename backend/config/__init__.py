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

    # 视频流配置
    VIDEO_FPS = int(os.getenv('VIDEO_FPS', 30))
    VIDEO_MAX_WIDTH = int(os.getenv('VIDEO_MAX_WIDTH', 640))
    VIDEO_JPEG_QUALITY = int(os.getenv('VIDEO_JPEG_QUALITY', 50))
    VIDEO_DETECT_WIDTH = int(os.getenv('VIDEO_DETECT_WIDTH', 320))
    VIDEO_BUFFER_SIZE = int(os.getenv('VIDEO_BUFFER_SIZE', 30))

    # AI 服务配置
    AI_SERVICE_URL = os.getenv('AI_SERVICE_URL', 'http://localhost:8001')

    # 消息推送配置
    PUSH_SERVICE_URL = os.getenv('PUSH_SERVICE_URL', 'http://localhost:8002')

    VIDEO_FRAME_SKIP = int(os.getenv('VIDEO_FRAME_SKIP', '5'))
    VIDEO_MAX_WIDTH = int(os.getenv('VIDEO_MAX_WIDTH', '640'))
    VIDEO_DETECT_WIDTH = int(os.getenv('VIDEO_DETECT_WIDTH', '320'))
    DEVICE_TAMPER_CONFIRM_FRAMES = int(os.getenv('DEVICE_TAMPER_CONFIRM_FRAMES', '3'))
    DEVICE_BLOCKED_CONFIRM_FRAMES = int(os.getenv('DEVICE_BLOCKED_CONFIRM_FRAMES', '8'))
    DEVICE_TAMPER_RECOVERY_FRAMES = int(os.getenv('DEVICE_TAMPER_RECOVERY_FRAMES', '4'))
    DEVICE_OFFLINE_TIMEOUT = int(os.getenv('DEVICE_OFFLINE_TIMEOUT', '5'))
    DEVICE_STREAM_OPEN_TIMEOUT = int(os.getenv('DEVICE_STREAM_OPEN_TIMEOUT', '20'))
    DEVICE_TAMPER_BACKGROUND_ENABLED = os.getenv(
        'DEVICE_TAMPER_BACKGROUND_ENABLED', 'true'
    ).lower() in ('1', 'true', 'yes', 'on')
    DEVICE_TAMPER_GATE_REFRESH_INTERVAL = int(os.getenv('DEVICE_TAMPER_GATE_REFRESH_INTERVAL', '10'))
    DEVICE_TAMPER_RECONNECT_INTERVAL = int(os.getenv('DEVICE_TAMPER_RECONNECT_INTERVAL', '2'))
    DEVICE_TAMPER_CHECK_INTERVAL = float(os.getenv('DEVICE_TAMPER_CHECK_INTERVAL', '0.1'))
    DEVICE_IMPACT_CONFIRM_FRAMES = int(os.getenv('DEVICE_IMPACT_CONFIRM_FRAMES', '1'))
    DEVICE_IMPACT_MOTION_THRESHOLD = float(os.getenv('DEVICE_IMPACT_MOTION_THRESHOLD', '6.0'))
    DEVICE_IMPACT_COHERENCE_THRESHOLD = float(os.getenv('DEVICE_IMPACT_COHERENCE_THRESHOLD', '0.6'))
    DEVICE_IMPACT_REVERSAL_COSINE = float(os.getenv('DEVICE_IMPACT_REVERSAL_COSINE', '-0.35'))
    DEVICE_IMPACT_WINDOW_FRAMES = int(os.getenv('DEVICE_IMPACT_WINDOW_FRAMES', '6'))
    DEVICE_IMPACT_BLUR_DROP_THRESHOLD = float(os.getenv('DEVICE_IMPACT_BLUR_DROP_THRESHOLD', '0.45'))
    DEVICE_IMPACT_MIN_TRACKED_POINTS = int(os.getenv('DEVICE_IMPACT_MIN_TRACKED_POINTS', '20'))
    DEVICE_IMPACT_SCENE_CHANGE_LIMIT = float(os.getenv('DEVICE_IMPACT_SCENE_CHANGE_LIMIT', '0.60'))
    DEVICE_IMPACT_SUDDEN_MULTIPLIER = float(os.getenv('DEVICE_IMPACT_SUDDEN_MULTIPLIER', '1.25'))
    FIRE_SMOKE_CONFIRM_FRAMES = int(os.getenv('FIRE_SMOKE_CONFIRM_FRAMES', '5'))
    FIRE_SMOKE_RECOVERY_FRAMES = int(os.getenv('FIRE_SMOKE_RECOVERY_FRAMES', '20'))
    FIRE_RECOVERY_FRAMES = int(os.getenv('FIRE_RECOVERY_FRAMES', '10'))
    FIRE_RATIO_THRESHOLD = float(os.getenv('FIRE_RATIO_THRESHOLD', '0.006'))
    SMOKE_RATIO_THRESHOLD = float(os.getenv('SMOKE_RATIO_THRESHOLD', '0.10'))
    FIRE_SMOKE_WARMUP_FRAMES = int(os.getenv('FIRE_SMOKE_WARMUP_FRAMES', '10'))
    FIRE_SMOKE_SCENE_CHANGE_RATIO = float(os.getenv('FIRE_SMOKE_SCENE_CHANGE_RATIO', '0.35'))
    STATIC_FIRE_RATIO_THRESHOLD = float(os.getenv('STATIC_FIRE_RATIO_THRESHOLD', '0.02'))
    DEVICE_ALARM_COOLDOWN = int(os.getenv('DEVICE_ALARM_COOLDOWN', '60'))
    TAILGATING_PROTOTXT_PATH = os.getenv(
        'TAILGATING_PROTOTXT_PATH',
        os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..',
            'test_assets', 'models', 'deploy.prototxt',
        )),
    )
    TAILGATING_MODEL_PATH = os.getenv(
        'TAILGATING_MODEL_PATH',
        os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..',
            'test_assets', 'models', 'mobilenet_iter_73000.caffemodel',
        )),
    )
    TAILGATING_CONFIDENCE = float(os.getenv('TAILGATING_CONFIDENCE', '0.25'))
    TAILGATING_DETECTION_INTERVAL = float(os.getenv('TAILGATING_DETECTION_INTERVAL', '0.10'))
    TAILGATING_LINE_RATIO = float(os.getenv('TAILGATING_LINE_RATIO', '0.62'))
    TAILGATING_CROSSING_WINDOW = float(os.getenv('TAILGATING_CROSSING_WINDOW', '5'))
    TAILGATING_MAX_HORIZONTAL_GAP_RATIO = float(os.getenv(
        'TAILGATING_MAX_HORIZONTAL_GAP_RATIO', '0.28'
    ))
    TAILGATING_AUTHORIZED_ENTRIES = int(os.getenv('TAILGATING_AUTHORIZED_ENTRIES', '1'))
    TAILGATING_DIRECTION = os.getenv('TAILGATING_DIRECTION', 'both')
    TAILGATING_STATUS_HOLD_SECONDS = float(os.getenv('TAILGATING_STATUS_HOLD_SECONDS', '3'))
    TAILGATING_ALARM_COOLDOWN = int(os.getenv('TAILGATING_ALARM_COOLDOWN', '60'))


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
    DEVICE_TAMPER_BACKGROUND_ENABLED = False


class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DEBUG = False
    _db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(_db_dir, 'prod.db')
    )
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时
