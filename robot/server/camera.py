"""
Camera streaming module - captures frames from Pi camera and serves MJPEG over HTTP.

Provides:
- CameraStream: captures JPEG frames from picamera2
- MJPEG HTTP server on configurable port (default 8080)

When picamera2 is unavailable (not on Pi), runs in simulation mode.
"""

import io
import logging
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

log = logging.getLogger("btbg.camera")

try:
    from picamera2 import Picamera2
    from picamera2.encoders import MJPEGEncoder
    from picamera2.outputs import FileOutput
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
    log.warning("picamera2 not available - camera in simulation mode")


class CameraStream:
    """Captures JPEG frames from the Pi camera."""

    def __init__(self, config: dict):
        self.width = config.get("width", 320)
        self.height = config.get("height", 240)
        self.quality = config.get("quality", 50)
        self.fps = config.get("fps", 10)

        self._frame = None
        self._lock = threading.Lock()
        self._running = False
        self._camera = None

    def start(self):
        """Initialize camera and begin capturing."""
        if CAMERA_AVAILABLE:
            try:
                self._camera = Picamera2()
                config = self._camera.create_video_configuration(
                    main={"size": (self.width, self.height), "format": "RGB888"},
                )
                self._camera.configure(config)
                self._camera.start()
                self._running = True
                # Start capture thread
                self._thread = threading.Thread(target=self._capture_loop, daemon=True)
                self._thread.start()
                log.info("Camera started: %dx%d @ %dfps, quality=%d",
                         self.width, self.height, self.fps, self.quality)
            except Exception as e:
                log.error("Failed to start camera: %s", e)
                self._running = False
        else:
            self._running = True
            log.info("Camera in simulation mode (no frames)")

    def _capture_loop(self):
        """Continuously capture frames in a background thread."""
        interval = 1.0 / self.fps
        while self._running and self._camera:
            try:
                buf = io.BytesIO()
                self._camera.capture_file(buf, format="jpeg")
                with self._lock:
                    self._frame = buf.getvalue()
            except Exception as e:
                log.error("Frame capture error: %s", e)
            time.sleep(interval)

    def get_frame(self) -> bytes | None:
        """Return the latest JPEG frame, or None if unavailable."""
        with self._lock:
            return self._frame

    def is_available(self) -> bool:
        """True if camera hardware is present."""
        return CAMERA_AVAILABLE and self._camera is not None

    def is_streaming(self) -> bool:
        """True if actively capturing frames."""
        return self._running and (self._frame is not None or not CAMERA_AVAILABLE)

    def stop(self):
        """Stop capturing and release camera."""
        self._running = False
        if self._camera:
            try:
                self._camera.stop()
                self._camera.close()
            except Exception as e:
                log.error("Camera stop error: %s", e)
            self._camera = None
        log.info("Camera stopped")


class MJPEGHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves MJPEG stream and snapshots."""

    camera = None  # Set by start_stream_server

    def do_GET(self):
        if self.path == "/stream":
            self._handle_stream()
        elif self.path == "/snapshot":
            self._handle_snapshot()
        elif self.path == "/":
            self._handle_index()
        else:
            self.send_error(404)

    def _handle_stream(self):
        """Serve MJPEG multipart stream."""
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        while True:
            frame = self.camera.get_frame() if self.camera else None
            if frame is None:
                time.sleep(0.1)
                continue
            try:
                self.wfile.write(b"--frame\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode())
                self.wfile.write(frame)
                self.wfile.write(b"\r\n")
                time.sleep(1.0 / (self.camera.fps if self.camera else 10))
            except (BrokenPipeError, ConnectionResetError):
                break

    def _handle_snapshot(self):
        """Serve single JPEG frame."""
        frame = self.camera.get_frame() if self.camera else None
        if frame is None:
            self.send_error(503, "No frame available")
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(frame)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(frame)

    def _handle_index(self):
        """Serve simple test page."""
        html = f"""<!DOCTYPE html>
<html><head><title>BTBG Camera</title></head>
<body style="background:#1a1a2e;display:flex;justify-content:center;align-items:center;height:100vh;margin:0">
<img src="/stream" style="max-width:100%;border:2px solid #e94560;border-radius:8px">
</body></html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress default HTTP log spam."""
        pass


def start_stream_server(camera: CameraStream, port: int = 8080):
    """Start the MJPEG HTTP server in a background thread."""
    MJPEGHandler.camera = camera
    server = HTTPServer(("0.0.0.0", port), MJPEGHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log.info("MJPEG stream server listening on http://0.0.0.0:%d/stream", port)
    return server
