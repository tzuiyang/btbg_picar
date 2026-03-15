"""
Hardware Bridge - Owns the PiCar-X instance and handles all hardware I/O.

This is the ONLY module that directly interfaces with the picarx library.
"""

import time
import logging

log = logging.getLogger("btbg.hardware")

try:
    from picarx import Picarx
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    log.warning("picarx not available - running in simulation mode")


class Hardware:
    """Single owner of the PiCar-X I2C bus."""

    def __init__(self, config: dict):
        self.min_motor_speed = config.get("min_motor_speed", 15)
        self.max_motor_speed = config.get("max_motor_speed", 100)
        self.max_steering_angle = config.get("max_steering_angle", 40.0)
        self.watchdog_timeout_s = config.get("watchdog_timeout_ms", 1500) / 1000.0

        self.px = None
        if HARDWARE_AVAILABLE:
            try:
                self.px = Picarx()
                log.info("Picarx initialized successfully")
            except Exception as e:
                log.error("Failed to initialize Picarx: %s", e)
        else:
            log.warning("Running in simulation mode (no hardware)")

        # State
        self.current_speed = 0.0
        self.current_steering = 0.0
        self.current_pan = 0.0
        self.current_tilt = 0.0
        self.is_stopped = True
        self.last_command_time = time.monotonic()

    def clamp_speed(self, speed: float) -> int:
        if abs(speed) < 0.01:
            return 0
        abs_speed = abs(speed)
        if abs_speed < self.min_motor_speed:
            abs_speed = self.min_motor_speed
        elif abs_speed > self.max_motor_speed:
            abs_speed = self.max_motor_speed
        return int(abs_speed) if speed > 0 else -int(abs_speed)

    def clamp_steering(self, angle: float) -> float:
        return max(-self.max_steering_angle, min(self.max_steering_angle, angle))

    def drive(self, speed: float, steering: float):
        """Apply drive command. speed: -100..100, steering: -40..40 degrees."""
        clamped_speed = self.clamp_speed(speed)
        clamped_steering = self.clamp_steering(steering)

        self.current_speed = clamped_speed
        self.current_steering = clamped_steering
        self.last_command_time = time.monotonic()

        if self.px:
            try:
                self.px.set_dir_servo_angle(clamped_steering)
                if clamped_speed > 0:
                    self.px.forward(clamped_speed)
                    self.is_stopped = False
                elif clamped_speed < 0:
                    self.px.backward(abs(clamped_speed))
                    self.is_stopped = False
                else:
                    self.px.stop()
                    self.is_stopped = True
            except Exception as e:
                log.error("Drive command failed: %s", e)
        else:
            log.debug("SIM: drive speed=%s, steering=%s", clamped_speed, clamped_steering)
            self.is_stopped = (clamped_speed == 0)

    def set_servo(self, pan: float, tilt: float):
        """Set camera pan/tilt. pan: -90..90, tilt: -35..35."""
        pan = max(-90, min(90, pan))
        tilt = max(-35, min(35, tilt))
        self.current_pan = pan
        self.current_tilt = tilt

        if self.px:
            try:
                self.px.set_cam_pan_angle(pan)
                self.px.set_cam_tilt_angle(tilt)
            except Exception as e:
                log.error("Servo command failed: %s", e)
        else:
            log.debug("SIM: servo pan=%s, tilt=%s", pan, tilt)

    def stop(self):
        """Emergency stop - stop all motors immediately."""
        self.current_speed = 0.0
        self.is_stopped = True
        if self.px:
            try:
                self.px.stop()
            except Exception as e:
                log.error("Emergency stop failed: %s", e)
        else:
            log.debug("SIM: emergency stop")

    def read_ultrasonic(self) -> float | None:
        """Read ultrasonic distance in cm, or None on failure."""
        if self.px:
            try:
                return self.px.ultrasonic.read()
            except Exception as e:
                log.error("Ultrasonic read failed: %s", e)
                return None
        else:
            import random
            if not hasattr(self, '_sim_dist'):
                self._sim_dist = 50.0
            self._sim_dist += random.uniform(-2, 2)
            self._sim_dist = max(10, min(100, self._sim_dist))
            return self._sim_dist

    def read_grayscale(self) -> list[float]:
        """Read grayscale sensors, normalized 0..1."""
        if self.px:
            try:
                values = self.px.get_grayscale_data()
                return [v / 4095.0 for v in values]
            except Exception as e:
                log.error("Grayscale read failed: %s", e)
                return [0.5, 0.5, 0.5]
        else:
            import random
            return [random.uniform(0.3, 0.7) for _ in range(3)]

    def read_battery(self) -> float:
        """Read battery voltage."""
        if self.px:
            # TODO: implement actual battery reading when robot-hat API is confirmed
            return 7.4
        else:
            if not hasattr(self, '_sim_batt'):
                self._sim_batt = 7.4
            self._sim_batt -= 0.001
            self._sim_batt = max(6.0, self._sim_batt)
            return self._sim_batt

    def check_watchdog(self):
        """Returns True if watchdog timed out (no commands received recently)."""
        if self.is_stopped:
            return False
        elapsed = time.monotonic() - self.last_command_time
        if elapsed > self.watchdog_timeout_s:
            log.warning("Watchdog timeout (%.0fms), stopping motors", elapsed * 1000)
            self.stop()
            return True
        return False

    def get_status(self) -> dict:
        return {
            "speed": self.current_speed,
            "steering": self.current_steering,
            "pan": self.current_pan,
            "tilt": self.current_tilt,
            "isStopped": self.is_stopped,
            "hardwareAvailable": HARDWARE_AVAILABLE and self.px is not None,
        }

    def shutdown(self):
        """Clean shutdown."""
        self.stop()
        log.info("Hardware shut down")
