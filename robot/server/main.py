#!/usr/bin/env python3
"""
BTBG Robot Server - Pure Python + WebSocket replacement for the ROS2 stack.

Single asyncio process that handles:
- WebSocket server (replaces rosbridge)
- Hardware control (motors, servos)
- Sensor polling (ultrasonic, grayscale, battery)
- Mode arbitration (manual vs patrol)
- Patrol state machine
- Hardware watchdog

Usage:
    python3 -m server.main
    python3 robot/server/main.py
    python3 robot/server/main.py --port 9090 --config robot/config/btbg_params.yaml
"""

import asyncio
import json
import signal
import sys
import time
import logging
import argparse
from pathlib import Path

try:
    import websockets
except ImportError:
    print("ERROR: websockets not installed. Run: pip3 install websockets")
    sys.exit(1)

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from .hardware import Hardware
from .patrol import Patrol
from .camera import CameraStream, start_stream_server

log = logging.getLogger("btbg")

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "hardware": {
        "watchdog_timeout_ms": 1500,
        "min_motor_speed": 15,
        "max_motor_speed": 100,
        "max_steering_angle": 40.0,
    },
    "sensors": {
        "ultrasonic_rate_hz": 10.0,
        "battery_rate_hz": 0.5,
        "ultrasonic_max_range_cm": 300.0,
        "ultrasonic_min_range_cm": 2.0,
        "battery_low_warning_v": 7.0,
    },
    "control": {
        "max_speed": 100,
        "max_steering_angle": 40.0,
        "watchdog_timeout_ms": 1000,
    },
    "patrol": {
        "speed": 30,
        "obstacle_threshold_cm": 25.0,
        "reverse_speed": 20,
        "reverse_duration_s": 0.5,
        "turn_duration_base_s": 0.8,
        "turn_angles": [-120, -90, -60, 60, 90, 120],
        "max_none_readings": 5,
        "speed_variation": 5,
    },
    "server": {
        "port": 9090,
        "telemetry_rate_hz": 10.0,
    },
    "camera": {
        "enabled": True,
        "port": 8080,
        "width": 320,
        "height": 240,
        "quality": 50,
        "fps": 10,
    },
}


def load_config(path: str | None) -> dict:
    config = DEFAULT_CONFIG.copy()
    if path and HAS_YAML:
        p = Path(path)
        if p.exists():
            with open(p) as f:
                raw = yaml.safe_load(f)
            # Map the ROS-style param file into our flat config
            if raw:
                for section_key, section in raw.items():
                    params = section.get("ros__parameters", section)
                    if "hardware_bridge" in section_key:
                        config["hardware"].update(params)
                    elif "sensor" in section_key:
                        config["sensors"].update(params)
                    elif "car_control" in section_key:
                        config["control"].update(params)
                    elif "patrol" in section_key:
                        config["patrol"].update(params)
            log.info("Loaded config from %s", path)

    # Load calibration
    config["calibration"] = load_calibration()
    return config


def _find_calibration_path() -> Path:
    """Locate calibration.yaml relative to this file or the repo root."""
    # Try relative to robot/server/ -> robot/config/
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "config" / "calibration.yaml",     # robot/config/
        here.parents[1] / "robot" / "config" / "calibration.yaml",  # repo root
    ]
    for p in candidates:
        if p.exists():
            return p
    # Default to first candidate (will be created on save)
    return candidates[0]


def load_calibration() -> dict:
    """Load calibration offsets from calibration.yaml."""
    defaults = {"steering": {"offset": 0}, "camera_pan": {"offset": 0}, "camera_tilt": {"offset": 0}}
    if not HAS_YAML:
        return defaults
    p = _find_calibration_path()
    if p.exists():
        try:
            with open(p) as f:
                raw = yaml.safe_load(f)
            if raw:
                for key in defaults:
                    if key in raw:
                        defaults[key].update(raw[key])
            log.info("Loaded calibration from %s", p)
        except Exception as e:
            log.error("Failed to load calibration: %s", e)
    return defaults


def save_calibration(calibration: dict):
    """Write calibration offsets to calibration.yaml."""
    if not HAS_YAML:
        log.warning("Cannot save calibration: PyYAML not installed")
        return
    p = _find_calibration_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        yaml.dump(calibration, f, default_flow_style=False, sort_keys=False)
    log.info("Saved calibration to %s", p)


# ---------------------------------------------------------------------------
# Robot controller (mode arbiter + sensor loop)
# ---------------------------------------------------------------------------

class RobotController:
    def __init__(self, config: dict, camera: CameraStream = None):
        self.config = config
        self.hw = Hardware(config["hardware"], config.get("calibration"))
        self.patrol = Patrol(config["patrol"])
        self.camera = camera

        ctrl = config["control"]
        self.max_speed = ctrl.get("max_speed", 100)
        self.max_steering = ctrl.get("max_steering_angle", 40.0)
        self.manual_watchdog_s = ctrl.get("watchdog_timeout_ms", 1000) / 1000.0

        sens = config["sensors"]
        self.ultrasonic_interval = 1.0 / sens.get("ultrasonic_rate_hz", 10.0)
        self.battery_interval = 1.0 / sens.get("battery_rate_hz", 0.5)
        self.max_range = sens.get("ultrasonic_max_range_cm", 300.0)
        self.min_range = sens.get("ultrasonic_min_range_cm", 2.0)
        self.battery_warning_v = sens.get("battery_low_warning_v", 7.0)

        self.mode = "manual"  # "manual" or "patrol"
        self.last_manual_cmd = time.monotonic()
        self.is_moving = False

        # Sensor state
        self.last_valid_distance = self.max_range
        self.consecutive_none = 0
        self.last_battery = 7.4
        self.battery_warning = False
        self.last_grayscale = [0.5, 0.5, 0.5]

        # Connected clients
        self.clients: set = set()

        self._running = False

    # -- Command handlers (called from WebSocket messages) --

    def handle_drive(self, data: dict):
        """Handle manual drive from UI. speed/steering are -1..1."""
        if self.mode != "manual":
            return
        linear_x = data.get("speed", 0.0)
        angular_z = data.get("steering", 0.0)
        speed = linear_x * self.max_speed
        steering = angular_z * self.max_steering
        self.hw.drive(speed, steering)
        self.last_manual_cmd = time.monotonic()
        self.is_moving = abs(speed) > 0.01

    def handle_mode(self, data: dict):
        new_mode = data.get("mode", "manual").lower().strip()
        if new_mode not in ("manual", "patrol"):
            return
        if new_mode != self.mode:
            log.info("Mode changed: %s -> %s", self.mode, new_mode)
            self.hw.drive(0, 0)
            self.is_moving = False
            self.mode = new_mode
            if new_mode == "patrol":
                self.patrol.activate()
            else:
                self.patrol.deactivate()

    def handle_servo(self, data: dict):
        pan = data.get("pan", 0.0)
        tilt = data.get("tilt", 0.0)
        self.hw.set_servo(pan, tilt)

    def handle_stop(self, _data: dict):
        log.info("Emergency stop received")
        self.hw.stop()
        self.is_moving = False
        if self.mode == "patrol":
            self.handle_mode({"mode": "manual"})

    # -- Calibration handlers --

    def handle_calibrate_steer(self, data: dict):
        """Set steering servo to raw angle for live calibration preview."""
        angle = data.get("angle", 0.0)
        self.hw.set_raw_steering(angle)

    def handle_save_calibration(self, data: dict):
        """Save steering offset and persist to disk."""
        offset = data.get("steering_offset", 0)
        self.hw.set_steering_offset(offset)
        # Update in-memory config and save to disk
        cal = self.config.get("calibration", {})
        cal.setdefault("steering", {})["offset"] = offset
        self.config["calibration"] = cal
        save_calibration(cal)

    def handle_get_calibration(self, _data: dict):
        """Return current calibration values (dispatched via broadcast)."""
        # This is handled specially in dispatch to send to requesting client
        pass

    # -- Message dispatch --

    MSG_HANDLERS = {
        "drive": "handle_drive",
        "mode": "handle_mode",
        "servo": "handle_servo",
        "stop": "handle_stop",
        "calibrate_steer": "handle_calibrate_steer",
        "save_calibration": "handle_save_calibration",
        "get_calibration": "handle_get_calibration",
    }

    def dispatch(self, msg: dict):
        msg_type = msg.get("type")
        handler_name = self.MSG_HANDLERS.get(msg_type)
        if handler_name:
            getattr(self, handler_name)(msg)
        else:
            log.warning("Unknown message type: %s", msg_type)

    # -- Broadcast to all connected clients --

    async def broadcast(self, msg: dict):
        if not self.clients:
            return
        data = json.dumps(msg)
        dead = set()
        for ws in self.clients:
            try:
                await ws.send(data)
            except websockets.ConnectionClosed:
                dead.add(ws)
        self.clients -= dead

    # -- Async loops --

    async def sensor_loop(self):
        """Poll sensors and update state."""
        last_ultra = 0.0
        last_batt = 0.0

        while self._running:
            now = time.monotonic()

            # Ultrasonic
            if now - last_ultra >= self.ultrasonic_interval:
                last_ultra = now
                raw = self.hw.read_ultrasonic()
                if raw is None:
                    self.consecutive_none += 1
                    dist = self.last_valid_distance
                elif raw > self.max_range or raw < self.min_range:
                    dist = self.last_valid_distance
                else:
                    self.consecutive_none = 0
                    self.last_valid_distance = raw
                    dist = raw

                # Feed patrol
                self.patrol.update_distance(dist)

            # Battery
            if now - last_batt >= self.battery_interval:
                last_batt = now
                self.last_battery = self.hw.read_battery()
                self.battery_warning = (
                    0 < self.last_battery < self.battery_warning_v
                )

            # Grayscale (same rate as ultrasonic)
            self.last_grayscale = self.hw.read_grayscale()

            await asyncio.sleep(self.ultrasonic_interval)

    async def control_loop(self):
        """Run patrol tick + watchdogs at ~20Hz."""
        interval = 0.05  # 20Hz

        while self._running:
            # Hardware watchdog
            self.hw.check_watchdog()

            # Manual watchdog
            if self.mode == "manual" and self.is_moving:
                elapsed = time.monotonic() - self.last_manual_cmd
                if elapsed > self.manual_watchdog_s:
                    log.warning("Manual watchdog timeout (%.0fms)", elapsed * 1000)
                    self.hw.drive(0, 0)
                    self.is_moving = False

            # Patrol tick
            if self.mode == "patrol":
                result = self.patrol.tick()
                if result is not None:
                    speed_norm, steer_norm = result
                    self.hw.drive(
                        speed_norm * self.max_speed,
                        steer_norm * self.max_steering,
                    )
                    self.is_moving = abs(speed_norm) > 0.01
                else:
                    self.hw.drive(0, 0)
                    self.is_moving = False
                self.patrol.on_state_exit()

            await asyncio.sleep(interval)

    async def telemetry_loop(self):
        """Broadcast telemetry to all clients."""
        rate = self.config["server"].get("telemetry_rate_hz", 10.0)
        interval = 1.0 / rate

        while self._running:
            msg = {
                "type": "telemetry",
                "sensors": {
                    "ultrasonic": round(self.last_valid_distance, 1),
                    "battery": round(self.last_battery, 2),
                    "batteryWarning": self.battery_warning,
                    "grayscale": [round(v, 3) for v in self.last_grayscale],
                },
                "status": {
                    "mode": self.mode,
                    "speed": self.hw.current_speed,
                    "steering": self.hw.current_steering,
                    "isMoving": self.is_moving,
                },
                "patrol": self.patrol.get_status(),
                "hardware": self.hw.get_status(),
                "camera": {
                    "available": self.camera.is_available() if self.camera else False,
                    "streaming": self.camera.is_streaming() if self.camera else False,
                    "port": self.config["camera"].get("port", 8080),
                },
            }
            await self.broadcast(msg)
            await asyncio.sleep(interval)

    # -- Lifecycle --

    async def start(self):
        self._running = True
        log.info("Robot controller started (mode: %s)", self.mode)

    async def stop(self):
        self._running = False
        self.hw.shutdown()
        log.info("Robot controller stopped")


# ---------------------------------------------------------------------------
# WebSocket server
# ---------------------------------------------------------------------------

async def ws_handler(ws, controller: RobotController):
    controller.clients.add(ws)
    remote = ws.remote_address
    log.info("Client connected: %s", remote)

    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
                # get_calibration needs to reply to the requesting client
                if msg.get("type") == "get_calibration":
                    cal = controller.config.get("calibration", {})
                    await ws.send(json.dumps({
                        "type": "calibration",
                        "steering_offset": cal.get("steering", {}).get("offset", 0),
                    }))
                else:
                    controller.dispatch(msg)
            except json.JSONDecodeError:
                log.warning("Invalid JSON from %s", remote)
    except websockets.ConnectionClosed:
        pass
    finally:
        controller.clients.discard(ws)
        log.info("Client disconnected: %s", remote)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(args):
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    config = load_config(args.config)
    config["server"]["port"] = args.port or config["server"].get("port", 9090)

    # Start camera
    camera = None
    cam_config = config.get("camera", {})
    if cam_config.get("enabled", True):
        camera = CameraStream(cam_config)
        camera.start()
        cam_port = cam_config.get("port", 8080)
        start_stream_server(camera, cam_port)

    controller = RobotController(config, camera)
    await controller.start()

    port = config["server"]["port"]

    # Graceful shutdown
    loop = asyncio.get_event_loop()
    shutdown_event = asyncio.Event()

    def _signal_handler():
        log.info("Shutdown signal received")
        shutdown_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _signal_handler)

    async with websockets.serve(
        lambda ws: ws_handler(ws, controller),
        "0.0.0.0",
        port,
    ):
        log.info("WebSocket server listening on 0.0.0.0:%d", port)

        # Start background tasks
        tasks = [
            asyncio.create_task(controller.sensor_loop()),
            asyncio.create_task(controller.control_loop()),
            asyncio.create_task(controller.telemetry_loop()),
        ]

        # Wait for shutdown
        await shutdown_event.wait()

        # Cleanup
        for t in tasks:
            t.cancel()
        if camera:
            camera.stop()
        await controller.stop()

    log.info("Server shut down cleanly")


def cli():
    parser = argparse.ArgumentParser(description="BTBG Robot Server")
    parser.add_argument("--port", type=int, default=None, help="WebSocket port (default: 9090)")
    parser.add_argument("--config", type=str, default=None, help="Path to btbg_params.yaml")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args()
    asyncio.run(main(args))


if __name__ == "__main__":
    cli()
