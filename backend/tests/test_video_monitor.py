"""
视频监控模块单元测试
测试RTMP视频流拉取、MJPEG转发、配置读取等功能
"""
import sys
import os
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
from flask import Flask, Blueprint, Response, jsonify

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _create_test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['RTMP_SERVER_HOST'] = '127.0.0.1'
    app.config['RTMP_SERVER_PORT'] = 9090
    app.config['VIDEO_FRAME_SKIP'] = 5
    app.config['VIDEO_RESOLUTION'] = (480, 480)

    from app.video_monitor import video_monitor_bp
    app.register_blueprint(video_monitor_bp, url_prefix='/api/v1/video-monitor')

    return app


class TestRTMPConfig:
    """测试RTMP配置项"""

    def test_default_rtmp_host(self):
        from config import BaseConfig
        assert BaseConfig.RTMP_SERVER_HOST == '127.0.0.1'

    def test_default_rtmp_port(self):
        from config import BaseConfig
        assert BaseConfig.RTMP_SERVER_PORT == 9090

    def test_default_frame_skip(self):
        from config import BaseConfig
        assert BaseConfig.VIDEO_FRAME_SKIP == 5

    def test_default_resolution(self):
        from config import BaseConfig
        assert BaseConfig.VIDEO_RESOLUTION == (480, 480)

    def test_config_attributes_exist(self):
        from config import BaseConfig
        assert hasattr(BaseConfig, 'RTMP_SERVER_HOST')
        assert hasattr(BaseConfig, 'RTMP_SERVER_PORT')
        assert hasattr(BaseConfig, 'VIDEO_FRAME_SKIP')
        assert hasattr(BaseConfig, 'VIDEO_RESOLUTION')


class TestGenerateFrames:
    """测试generate_frames视频流生成函数"""

    def test_generate_frames_stream_url_format(self):
        """测试生成的RTMP流地址格式正确"""
        app = _create_test_app()
        with app.app_context():
            with patch('app.video_monitor.cv2.VideoCapture') as mock_vc_class:
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = False
                mock_vc_class.return_value = mock_cap

                from app.video_monitor import generate_frames
                list(generate_frames('test_stream'))

                expected_url = 'rtmp://127.0.0.1:9090/live/test_stream'
                mock_vc_class.assert_called_once_with(expected_url)

    def test_generate_frames_custom_host_and_port(self):
        """测试自定义RTMP主机和端口"""
        app = _create_test_app()
        app.config['RTMP_SERVER_HOST'] = '192.168.1.100'
        app.config['RTMP_SERVER_PORT'] = 1935
        with app.app_context():
            with patch('app.video_monitor.cv2.VideoCapture') as mock_vc_class:
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = False
                mock_vc_class.return_value = mock_cap

                from app.video_monitor import generate_frames
                list(generate_frames('cam01'))

                expected_url = 'rtmp://192.168.1.100:1935/live/cam01'
                mock_vc_class.assert_called_once_with(expected_url)

    def test_generate_frames_returns_empty_when_not_opened(self):
        """测试RTMP连接失败时返回空生成器"""
        app = _create_test_app()
        with app.app_context():
            with patch('app.video_monitor.cv2.VideoCapture') as mock_vc_class:
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = False
                mock_vc_class.return_value = mock_cap

                from app.video_monitor import generate_frames
                result = list(generate_frames('test_stream'))
                assert result == []

    def test_generate_frames_yields_jpeg_frames(self):
        """测试成功拉流时yield JPEG帧数据"""
        app = _create_test_app()
        with app.app_context():
            fake_frame = np.zeros((480, 480, 3), dtype=np.uint8)

            with patch('app.video_monitor.cv2.VideoCapture') as mock_vc_class:
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = True
                mock_cap.read.side_effect = [
                    (True, fake_frame),
                    (False, None)
                ]
                mock_vc_class.return_value = mock_cap

                with patch('app.video_monitor.cv2.imencode') as mock_encode:
                    fake_buffer = MagicMock()
                    fake_buffer.tobytes.return_value = b'\xff\xd8\xff\xe0fake_jpeg_data'
                    mock_encode.return_value = (True, fake_buffer)

                    from app.video_monitor import generate_frames
                    result = list(generate_frames('test_stream'))

                    assert len(result) == 1
                    assert result[0].startswith(b'--frame\r\n')
                    assert b'Content-Type: image/jpeg' in result[0]
                    assert b'fake_jpeg_data' in result[0]

    def test_generate_frames_frame_skip(self):
        """测试跳帧逻辑：frame_skip=5时每5帧输出1帧"""
        app = _create_test_app()
        with app.app_context():
            fake_frame = np.zeros((480, 480, 3), dtype=np.uint8)
            read_results = [(True, fake_frame) for _ in range(10)]
            read_results.append((False, None))

            with patch('app.video_monitor.cv2.VideoCapture') as mock_vc_class:
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = True
                mock_cap.read.side_effect = read_results
                mock_vc_class.return_value = mock_cap

                with patch('app.video_monitor.cv2.imencode') as mock_encode:
                    fake_buffer = MagicMock()
                    fake_buffer.tobytes.return_value = b'jpeg_data'
                    mock_encode.return_value = (True, fake_buffer)

                    from app.video_monitor import generate_frames
                    result = list(generate_frames('test_stream'))

                    assert len(result) == 2

    def test_generate_frames_releases_capture(self):
        """测试生成器退出时释放VideoCapture资源"""
        app = _create_test_app()
        with app.app_context():
            with patch('app.video_monitor.cv2.VideoCapture') as mock_vc_class:
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = True
                mock_cap.read.return_value = (False, None)
                mock_vc_class.return_value = mock_cap

                from app.video_monitor import generate_frames
                list(generate_frames('test_stream'))

                mock_cap.release.assert_called_once()

    def test_generate_frames_sets_resolution(self):
        """测试设置视频分辨率"""
        app = _create_test_app()
        with app.app_context():
            with patch('app.video_monitor.cv2.VideoCapture') as mock_vc_class:
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = True
                mock_cap.read.return_value = (False, None)
                mock_vc_class.return_value = mock_cap

                from app.video_monitor import generate_frames
                list(generate_frames('test_stream'))

                mock_cap.set.assert_any_call(3, 480)
                mock_cap.set.assert_any_call(4, 480)

    def test_generate_frames_skips_encode_failure(self):
        """测试编码失败时跳过当前帧"""
        app = _create_test_app()
        with app.app_context():
            fake_frame = np.zeros((480, 480, 3), dtype=np.uint8)

            with patch('app.video_monitor.cv2.VideoCapture') as mock_vc_class:
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = True
                mock_cap.read.side_effect = [
                    (True, fake_frame),
                    (False, None)
                ]
                mock_vc_class.return_value = mock_cap

                with patch('app.video_monitor.cv2.imencode') as mock_encode:
                    mock_encode.return_value = (False, None)

                    from app.video_monitor import generate_frames
                    result = list(generate_frames('test_stream'))

                    assert len(result) == 0


class TestVideoFeedRoute:
    """测试video_feed路由"""

    def test_video_feed_returns_mjpeg_response(self):
        """测试video_feed路由返回MJPEG格式响应"""
        app = _create_test_app()
        with app.test_client() as client:
            with patch('app.video_monitor.generate_frames') as mock_gen:
                mock_gen.return_value = iter([
                    b'--frame\r\nContent-Type: image/jpeg\r\n\r\ntest\r\n'
                ])
                response = client.get('/api/v1/video-monitor/video_feed/test_stream')
                assert response.status_code == 200
                assert 'multipart/x-mixed-replace' in response.content_type

    def test_video_feed_with_stream_id(self):
        """测试video_feed路由正确传递stream_id"""
        app = _create_test_app()
        with app.test_client() as client:
            with patch('app.video_monitor.generate_frames') as mock_gen:
                mock_gen.return_value = iter([])
                client.get('/api/v1/video-monitor/video_feed/my_camera_01')
                mock_gen.assert_called_once_with('my_camera_01')

    def test_video_feed_exception_returns_500(self):
        """测试video_feed异常时返回500"""
        app = _create_test_app()
        with app.test_client() as client:
            with patch('app.video_monitor.generate_frames') as mock_gen:
                mock_gen.side_effect = Exception('RTMP connection failed')
                response = client.get('/api/v1/video-monitor/video_feed/test_stream')
                assert response.status_code == 500
