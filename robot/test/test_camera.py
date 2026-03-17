"""Tests for camera streaming module."""

import pytest
from unittest.mock import patch, MagicMock


class TestCameraStream:
    """Test CameraStream class."""

    def _make_camera(self, **overrides):
        from robot.server.camera import CameraStream
        config = {"width": 320, "height": 240, "quality": 50, "fps": 10}
        config.update(overrides)
        return CameraStream(config)

    def test_init_default_config(self):
        cam = self._make_camera()
        assert cam.width == 320
        assert cam.height == 240
        assert cam.quality == 50
        assert cam.fps == 10

    def test_init_custom_config(self):
        cam = self._make_camera(width=640, height=480, quality=80, fps=30)
        assert cam.width == 640
        assert cam.height == 480
        assert cam.quality == 80
        assert cam.fps == 30

    def test_is_available_false_without_picamera2(self):
        cam = self._make_camera()
        assert cam.is_available() is False

    def test_get_frame_returns_none_without_camera(self):
        cam = self._make_camera()
        assert cam.get_frame() is None

    def test_is_streaming_false_before_start(self):
        cam = self._make_camera()
        assert cam.is_streaming() is False

    def test_stop_without_start_no_error(self):
        cam = self._make_camera()
        cam.stop()  # Should not raise


class TestMJPEGHandler:
    """Test MJPEG HTTP handler."""

    def test_handler_has_do_GET(self):
        from robot.server.camera import MJPEGHandler
        assert hasattr(MJPEGHandler, 'do_GET')

    def test_handler_routes(self):
        from robot.server.camera import MJPEGHandler
        handler = MagicMock(spec=MJPEGHandler)
        handler.path = "/stream"
        MJPEGHandler.do_GET(handler)
        handler._handle_stream.assert_called_once()

    def test_handler_snapshot_route(self):
        from robot.server.camera import MJPEGHandler
        handler = MagicMock(spec=MJPEGHandler)
        handler.path = "/snapshot"
        MJPEGHandler.do_GET(handler)
        handler._handle_snapshot.assert_called_once()

    def test_handler_index_route(self):
        from robot.server.camera import MJPEGHandler
        handler = MagicMock(spec=MJPEGHandler)
        handler.path = "/"
        MJPEGHandler.do_GET(handler)
        handler._handle_index.assert_called_once()

    def test_handler_404_unknown_path(self):
        from robot.server.camera import MJPEGHandler
        handler = MagicMock(spec=MJPEGHandler)
        handler.path = "/unknown"
        MJPEGHandler.do_GET(handler)
        handler.send_error.assert_called_once_with(404)


class TestCameraConfig:
    """Test camera config in main server."""

    def test_default_config_has_camera_section(self):
        from robot.server.main import DEFAULT_CONFIG
        assert "camera" in DEFAULT_CONFIG

    def test_camera_config_defaults(self):
        from robot.server.main import DEFAULT_CONFIG
        cam = DEFAULT_CONFIG["camera"]
        assert cam["enabled"] is True
        assert cam["port"] == 8080
        assert cam["width"] == 320
        assert cam["height"] == 240
        assert cam["quality"] == 50
        assert cam["fps"] == 10
