"""Tests for steering calibration system."""

import pytest
import tempfile
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Mock Picarx for tests
# ---------------------------------------------------------------------------

class MockPicarx:
    def __init__(self):
        self.steering = 0
        self.speed = 0
        self.pan = 0
        self.tilt = 0

    def set_dir_servo_angle(self, angle):
        self.steering = angle

    def set_cam_pan_angle(self, angle):
        self.pan = angle

    def set_cam_tilt_angle(self, angle):
        self.tilt = angle

    def forward(self, speed):
        self.speed = speed

    def backward(self, speed):
        self.speed = -speed

    def stop(self):
        self.speed = 0


# ---------------------------------------------------------------------------
# Hardware calibration tests
# ---------------------------------------------------------------------------

class TestHardwareCalibration:
    """Test that Hardware applies steering offset correctly."""

    def _make_hardware(self, offset=0):
        """Create a Hardware instance with a mock Picarx."""
        import robot.server.hardware as hw_mod
        # Temporarily enable hardware
        orig = hw_mod.HARDWARE_AVAILABLE
        hw_mod.HARDWARE_AVAILABLE = True

        config = {
            "min_motor_speed": 15,
            "max_motor_speed": 100,
            "max_steering_angle": 40.0,
            "watchdog_timeout_ms": 1500,
        }
        calibration = {"steering": {"offset": offset}}
        hardware = hw_mod.Hardware(config, calibration)
        hardware.px = MockPicarx()

        hw_mod.HARDWARE_AVAILABLE = orig
        return hardware

    def test_offset_zero_no_change(self):
        hw = self._make_hardware(offset=0)
        hw.drive(50, 10)
        assert hw.px.steering == 10  # No offset applied

    def test_offset_positive_shifts_angle(self):
        hw = self._make_hardware(offset=5)
        hw.drive(50, 0)
        assert hw.px.steering == 5  # 0 + 5 = 5

    def test_offset_negative_shifts_angle(self):
        hw = self._make_hardware(offset=-3)
        hw.drive(50, 10)
        assert hw.px.steering == 7  # 10 + (-3) = 7

    def test_offset_applied_with_steering(self):
        hw = self._make_hardware(offset=5)
        hw.drive(50, 20)
        assert hw.px.steering == 25  # 20 + 5 = 25

    def test_clamping_still_works(self):
        hw = self._make_hardware(offset=0)
        hw.drive(50, 100)  # Exceeds max
        # Clamped to 40, then + 0 offset = 40
        assert hw.px.steering == 40

    def test_set_raw_steering_no_offset(self):
        hw = self._make_hardware(offset=10)
        hw.set_raw_steering(5)
        assert hw.px.steering == 5  # Raw, no offset

    def test_set_raw_steering_clamped(self):
        hw = self._make_hardware(offset=0)
        hw.set_raw_steering(100)
        assert hw.px.steering == 60  # Clamped to ±60

    def test_set_raw_steering_negative_clamped(self):
        hw = self._make_hardware(offset=0)
        hw.set_raw_steering(-100)
        assert hw.px.steering == -60

    def test_set_steering_offset(self):
        hw = self._make_hardware(offset=0)
        hw.set_steering_offset(7)
        assert hw.steering_offset == 7

    def test_set_steering_offset_then_drive(self):
        hw = self._make_hardware(offset=0)
        hw.set_steering_offset(7)
        hw.drive(50, 0)
        assert hw.px.steering == 7  # 0 + 7 = 7


class TestCalibrationNoCalibrationArg:
    """Test that Hardware works when no calibration is provided."""

    def test_default_offset_is_zero(self):
        import robot.server.hardware as hw_mod
        config = {
            "min_motor_speed": 15,
            "max_motor_speed": 100,
            "max_steering_angle": 40.0,
            "watchdog_timeout_ms": 1500,
        }
        hardware = hw_mod.Hardware(config)  # No calibration arg
        assert hardware.steering_offset == 0


# ---------------------------------------------------------------------------
# Config loading tests
# ---------------------------------------------------------------------------

class TestCalibrationConfigLoading:
    """Test loading and saving calibration.yaml."""

    def test_load_calibration_defaults(self):
        import robot.server.main as main_mod
        orig_find = main_mod._find_calibration_path
        main_mod._find_calibration_path = lambda: Path("/nonexistent/no_such_file.yaml")
        try:
            cal = main_mod.load_calibration()
            assert cal["steering"]["offset"] == 0
        finally:
            main_mod._find_calibration_path = orig_find

    def test_save_and_load_calibration(self):
        import robot.server.main as main_mod
        # Temporarily override the calibration path
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "calibration.yaml"
            orig_find = main_mod._find_calibration_path
            main_mod._find_calibration_path = lambda: test_path

            try:
                cal = {"steering": {"offset": 7}, "camera_pan": {"offset": 0}, "camera_tilt": {"offset": 0}}
                main_mod.save_calibration(cal)
                assert test_path.exists()

                loaded = main_mod.load_calibration()
                assert loaded["steering"]["offset"] == 7
            finally:
                main_mod._find_calibration_path = orig_find

    def test_missing_file_returns_defaults(self):
        import robot.server.main as main_mod
        orig_find = main_mod._find_calibration_path
        main_mod._find_calibration_path = lambda: Path("/nonexistent/calibration.yaml")

        try:
            cal = main_mod.load_calibration()
            assert cal["steering"]["offset"] == 0
        finally:
            main_mod._find_calibration_path = orig_find


# ---------------------------------------------------------------------------
# Message dispatch tests
# ---------------------------------------------------------------------------

class TestCalibrationDispatch:
    """Test that calibration messages are dispatched correctly."""

    def _make_controller(self, offset=0):
        from robot.server.main import RobotController, DEFAULT_CONFIG
        config = DEFAULT_CONFIG.copy()
        config["calibration"] = {"steering": {"offset": offset}}
        controller = RobotController(config)
        controller.hw.px = MockPicarx()
        return controller

    def test_calibrate_steer_sets_raw_angle(self):
        ctrl = self._make_controller()
        ctrl.dispatch({"type": "calibrate_steer", "angle": 12})
        assert ctrl.hw.px.steering == 12

    def test_save_calibration_updates_offset(self):
        ctrl = self._make_controller()
        ctrl.dispatch({"type": "save_calibration", "steering_offset": 8})
        assert ctrl.hw.steering_offset == 8

    def test_drive_uses_offset_after_save(self):
        ctrl = self._make_controller(offset=0)
        ctrl.dispatch({"type": "save_calibration", "steering_offset": 5})
        ctrl.dispatch({"type": "drive", "speed": 0.5, "steering": 0.0})
        # steering = 0.0 * 40 = 0, + offset 5 = 5
        assert ctrl.hw.px.steering == 5
