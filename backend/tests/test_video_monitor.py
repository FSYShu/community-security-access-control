"""
视频监控模块单元测试
测试RTMP配置读取、MJPEG转发、FFmpeg拉流等功能
"""
import sys
import os
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _create_test_app():
    app = pytest.importorskip('flask').Flask(__name__)
    app.config['TESTING'] = True
    app.config['RTMP_SERVER_HOST'] = '127.0.0.1'
    app.config['RTMP_SERVER_PORT'] = 9090
    app.config['VIDEO_MAX_WIDTH'] = 640
    app.config['VIDEO_FPS'] = 20

    from app.video_monitor import video_monitor_bp
    app.register_blueprint(video_monitor_bp, url_prefix='/api/v1/video-monitor')

    return app


class TestRTMPConfig:
    """测试RTMP配置项"""

    def test_default_rtmp_host(self):
        from config import BaseConfig
        assert isinstance(BaseConfig.RTMP_SERVER_HOST, str)
        assert len(BaseConfig.RTMP_SERVER_HOST) > 0

    def test_default_rtmp_port(self):
        from config import BaseConfig
        assert BaseConfig.RTMP_SERVER_PORT == 9090

    def test_config_attributes_exist(self):
        from config import BaseConfig
        assert hasattr(BaseConfig, 'RTMP_SERVER_HOST')
        assert hasattr(BaseConfig, 'RTMP_SERVER_PORT')
        assert hasattr(BaseConfig, 'VIDEO_MAX_WIDTH')
        assert hasattr(BaseConfig, 'VIDEO_FPS')


class TestGenerateFramesFFmpeg:
    """测试generate_frames_ffmpeg视频流生成函数"""

    def test_generate_frames_ffmpeg_no_entry(self):
        """测试FFmpeg拉流失败时返回空生成器"""
        app = _create_test_app()
        with app.app_context():
            with patch('app.video_monitor.start_rtmp_pull', return_value=None):
                from app.video_monitor import generate_frames_ffmpeg
                result = list(generate_frames_ffmpeg('rtmp://127.0.0.1:9090/live/test'))
                assert result == []

    def test_generate_frames_ffmpeg_yields_frames(self):
        """测试FFmpeg拉流成功时yield JPEG帧数据"""
        app = _create_test_app()
        with app.app_context():
            mock_entry = {'process': MagicMock(), 'url': 'rtmp://127.0.0.1:9090/live/test',
                          'started': 0, 'ref_count': 1}
            mock_entry['process'].poll.return_value = None

            fake_jpeg = b'\xff\xd8\xff\xe0fake_jpeg_data\xff\xd9'

            with patch('app.video_monitor.start_rtmp_pull', return_value=mock_entry):
                with patch('app.video_monitor.read_jpeg_frame_from_pull', return_value=fake_jpeg):
                    with patch('app.video_monitor.stop_rtmp_pull'):
                        from app.video_monitor import generate_frames_ffmpeg
                        gen = generate_frames_ffmpeg('rtmp://127.0.0.1:9090/live/test')
                        result = next(gen, None)
                        assert result is not None
                        assert b'--frame' in result
                        assert b'Content-Type: image/jpeg' in result


class TestVideoFeedRoute:
    """测试video_feed路由"""

    def test_video_feed_returns_mjpeg_response(self):
        """测试video_feed路由返回MJPEG格式响应"""
        app = _create_test_app()
        with app.test_client() as client:
            with patch('app.video_monitor.generate_frames_ffmpeg') as mock_gen:
                mock_gen.return_value = iter([
                    b'--frame\r\nContent-Type: image/jpeg\r\n\r\ntest\r\n'
                ])
                response = client.get('/api/v1/video-monitor/video_feed/test_stream')
                assert response.status_code == 200
                assert 'multipart/x-mixed-replace' in response.content_type

    def test_video_feed_exception_returns_500(self):
        """测试video_feed异常时返回500"""
        app = _create_test_app()
        with app.test_client() as client:
            with patch('app.video_monitor.generate_frames_ffmpeg') as mock_gen:
                mock_gen.side_effect = Exception('RTMP connection failed')
                response = client.get('/api/v1/video-monitor/video_feed/test_stream')
                assert response.status_code == 500
