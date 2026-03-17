# Camera Streaming TODO

> **Goal**: Stream live video from the Pi camera to the Electron UI.
> Low resolution (320x240) for smooth streaming over the Pi's WiFi hotspot.

---

## Architecture Decision

**Approach: Separate MJPEG HTTP server on port 8080**

```
┌─────────────────────────────────────┐
│  Pi (robot server)                  │
│                                     │
│  Port 9090: WebSocket (control)     │
│  Port 8080: HTTP MJPEG (video)      │
│                                     │
│  picamera2 → JPEG encode → MJPEG   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  PC (Electron app)                  │
│                                     │
│  WebSocket → control/telemetry      │
│  <img src="http://host:8080/stream">│
│    → live camera feed               │
└─────────────────────────────────────┘
```

**Why not WebSocket binary frames?**
- Couples video with control traffic on same connection
- Requires rewriting message parser to handle binary vs JSON
- MJPEG over HTTP is proven, standard, and browser-native

**Why not base64 over WebSocket?**
- 33% overhead on every frame
- Bloats telemetry messages
- Harder to manage frame rate independently

**MJPEG over HTTP is the simplest approach:**
- `<img>` tag handles it natively (no JS needed)
- Separate from control traffic
- Easy to throttle independently
- Works with any browser/viewer

---

## Phase 1: Camera Capture Module

### 1.1 Add dependencies to `robot/requirements.txt`
- [ ] Add `picamera2>=0.3.0,<1.0.0; platform_machine == "aarch64"`
- [ ] Note: picamera2 is pre-installed on Raspberry Pi OS, so pip install may not be needed

### 1.2 Create `robot/server/camera.py`
- [ ] Import `picamera2` with try/except fallback (like hardware.py pattern)
- [ ] `CameraStream` class with:
  - `__init__(self, config)` — resolution (320x240), quality (50), framerate (10fps)
  - `start()` — initialize picamera2, start capturing
  - `stop()` — release camera
  - `get_frame()` — return latest JPEG bytes (thread-safe)
  - `is_available()` — True if camera hardware is present
- [ ] Simulation mode: when picamera2 unavailable, `get_frame()` returns a
      simple generated test image (gray frame with "NO CAMERA" text) or None
- [ ] Use a background thread for continuous capture into a shared buffer
- [ ] Thread-safe frame access using `threading.Lock` or `threading.Event`

### 1.3 Create MJPEG HTTP server in `robot/server/camera.py`
- [ ] `MJPEGHandler` class extending `http.server.BaseHTTPRequestHandler`
- [ ] `GET /stream` — serves `multipart/x-mixed-replace` MJPEG stream
- [ ] `GET /snapshot` — serves single JPEG frame
- [ ] `GET /` — serves simple HTML page with `<img>` for testing
- [ ] `start_stream_server(camera, port=8080)` — starts threaded HTTP server
- [ ] Configurable port via config dict

### Tests after Phase 1: `robot/test/test_camera.py`
- [ ] Test: CameraStream initializes with default config (320x240, quality 50)
- [ ] Test: CameraStream in simulation mode returns None or placeholder bytes
- [ ] Test: CameraStream.is_available() returns False when picamera2 missing
- [ ] Test: MJPEGHandler responds to GET /snapshot with image/jpeg content-type
- [ ] Test: MJPEGHandler responds to GET /stream with multipart content-type
- [ ] Test: MJPEGHandler responds to GET / with text/html
- [ ] Test: start_stream_server starts without error in sim mode

---

## Phase 2: Integrate Camera with Main Server

### 2.1 Add camera config to `main.py` DEFAULT_CONFIG
- [ ] Add `"camera"` section:
      ```python
      "camera": {
          "enabled": True,
          "port": 8080,
          "width": 320,
          "height": 240,
          "quality": 50,
          "fps": 10,
      }
      ```

### 2.2 Start camera server alongside WebSocket in `main.py`
- [ ] Import `CameraStream` and `start_stream_server` from camera module
- [ ] Create `CameraStream` instance in `main()` after controller init
- [ ] Call `start_stream_server(camera, port)` before WebSocket serve
- [ ] Stop camera on shutdown
- [ ] Log camera server URL on startup: `http://0.0.0.0:8080/stream`

### 2.3 Add camera status to telemetry
- [ ] Add `"camera"` field to telemetry broadcast:
      ```python
      "camera": {
          "available": camera.is_available(),
          "streaming": camera.is_streaming(),
          "port": 8080,
      }
      ```
- [ ] Frontend can use this to know the stream URL dynamically

### Tests after Phase 2: `robot/test/test_camera_integration.py`
- [ ] Test: DEFAULT_CONFIG contains camera section with all keys
- [ ] Test: camera config has sensible defaults (320x240, quality 50, fps 10)
- [ ] Test: telemetry message includes camera status fields
- [ ] Test: camera port is configurable

---

## Phase 3: Frontend — Camera Feed Component

### 3.1 Create `app/src/components/CameraFeed.jsx`
- [ ] Accepts `host` and `port` props (or constructs from env)
- [ ] Renders `<img>` tag with `src="http://{host}:{port}/stream"`
- [ ] Shows placeholder/message when not connected or camera unavailable
- [ ] Shows "Camera unavailable" if telemetry reports `camera.available = false`
- [ ] Error handling: `onError` shows fallback message
- [ ] Aspect ratio: 4:3 (320x240), scales to fit container

### 3.2 Update CSP in `app/index.html`
- [ ] Add `img-src 'self' http://*:8080;` to Content-Security-Policy
- [ ] This allows loading images from any host on port 8080

### 3.3 Integrate into `App.jsx`
- [ ] Add CameraFeed to the right panel (above telemetry)
- [ ] Pass camera info from telemetry data (port, availability)
- [ ] Construct stream URL from `VITE_PI_HOST` env var + camera port
- [ ] Layout: camera feed takes top of right panel, telemetry below

### 3.4 Updated layout:
```
┌─────────────────────────────────────────────────────┐
│ Header: BTBG Control | Calibrate | Connection       │
├─────────────────────────────────────────────────────┤
│ Mode Toggle: MANUAL ←→ PATROL                       │
├──────────────────────┬──────────────────────────────┤
│  Left Panel (1/2)    │  Right Panel (1/2)           │
│  ─────────────────   │  ────────────────────        │
│  Drive Controls      │  ┌──────────────────┐        │
│  - Speed Slider      │  │  CAMERA FEED     │        │
│  - WASD/Arrow Pad    │  │  (320x240 MJPEG) │        │
│  - Emergency Stop    │  └──────────────────┘        │
│                      │  Telemetry                   │
│  Camera Servo        │  - Ultrasonic                │
│  - Pan/Tilt sliders  │  - Battery                   │
│                      │  - Status Bar                │
└──────────────────────┴──────────────────────────────┘
```

### Tests after Phase 3: `app/src/components/__tests__/CameraFeed.test.jsx`
- [ ] Test: renders img element with correct stream URL
- [ ] Test: constructs URL from host and port props
- [ ] Test: shows "Camera unavailable" when `available=false`
- [ ] Test: shows fallback on img error
- [ ] Test: has correct aspect ratio class (4:3)

---

## Phase 4: Install Dependencies on Pi

### 4.1 Install picamera2 on the Pi
- [ ] SSH to Pi: `ssh yze@10.42.0.1` (or via WiFi)
- [ ] Check if already installed: `python3 -c "import picamera2; print('OK')"`
- [ ] If not: `sudo apt install python3-picamera2`
- [ ] Verify camera hardware: `libcamera-hello --list-cameras`

### 4.2 Deploy code to Pi
- [ ] Commit and push from PC
- [ ] Switch Pi to WiFi, pull code, switch back to hotspot
- [ ] Or: edit directly on Pi via SSH

---

## Phase 5: End-to-End Testing

### 5.1 Test on Pi with real camera
- [ ] Start server: `npm run btbg:start` — should show both ports (9090 + 8080)
- [ ] Open browser: `http://10.42.0.1:8080/` — should show test page with video
- [ ] Open browser: `http://10.42.0.1:8080/snapshot` — should show single JPEG
- [ ] Run app: `npm run app` — camera feed should appear in right panel
- [ ] Move camera servos with pan/tilt sliders — video should show new angle
- [ ] Drive the car — video should show real-time view

### 5.2 Test simulation mode (no camera)
- [ ] Run server on PC (sim mode) — camera reports unavailable
- [ ] App shows "Camera unavailable" placeholder
- [ ] No crashes, all other features still work

---

## File Change Summary

| File | Action | What Changes |
|------|--------|-------------|
| `robot/server/camera.py` | Create | Camera capture + MJPEG HTTP server |
| `robot/server/main.py` | Edit | Start camera server, add camera telemetry |
| `robot/requirements.txt` | Edit | Add picamera2 dependency |
| `app/src/components/CameraFeed.jsx` | Create | Camera feed display component |
| `app/src/App.jsx` | Edit | Add CameraFeed to right panel |
| `app/index.html` | Edit | Update CSP for img-src |
| `robot/test/test_camera.py` | Create | Camera module tests |
| `robot/test/test_camera_integration.py` | Create | Integration tests |
| `app/src/components/__tests__/CameraFeed.test.jsx` | Create | Frontend camera tests |

---

## Configuration Reference

```python
# In DEFAULT_CONFIG (main.py)
"camera": {
    "enabled": True,       # Enable/disable camera
    "port": 8080,          # HTTP stream port
    "width": 320,          # Frame width
    "height": 240,         # Frame height
    "quality": 50,         # JPEG quality (1-100, lower = smaller/faster)
    "fps": 10,             # Target framerate
}
```

## Bandwidth Estimate

| Resolution | Quality | Frame Size | FPS | Bandwidth |
|-----------|---------|------------|-----|-----------|
| 320x240 | 50 | ~10KB | 10 | ~100KB/s |
| 320x240 | 50 | ~10KB | 15 | ~150KB/s |
| 640x480 | 50 | ~30KB | 10 | ~300KB/s |

320x240 at 10fps is very comfortable over the Pi's WiFi hotspot.
