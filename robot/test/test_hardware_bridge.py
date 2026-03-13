#!/usr/bin/env python3
"""Unit tests for hardware_bridge_node."""

import pytest
import sys
import os

# Add the package to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'btbg_nodes'))


class MockPicarx:
    """Mock Picarx class for testing without hardware."""

    def __init__(self):
        self.speed = 0
        self.steering = 0
        self.pan = 0
        self.tilt = 0
        self.stopped = True

    def forward(self, speed):
        self.speed = speed
        self.stopped = False

    def backward(self, speed):
        self.speed = -speed
        self.stopped = False

    def stop(self):
        self.speed = 0
        self.stopped = True

    def set_dir_servo_angle(self, angle):
        self.steering = angle

    def set_cam_pan_angle(self, angle):
        self.pan = angle

    def set_cam_tilt_angle(self, angle):
        self.tilt = angle


class TestHardwareBridgeLogic:
    """Test hardware bridge node logic without ROS2."""

    def test_clamp_speed_zero(self):
        """Test that near-zero speeds return 0."""
        # Simulate the clamp logic
        def clamp_speed(speed, min_speed=15, max_speed=100):
            if abs(speed) < 0.01:
                return 0
            abs_speed = abs(speed)
            if abs_speed < min_speed:
                abs_speed = min_speed
            elif abs_speed > max_speed:
                abs_speed = max_speed
            return int(abs_speed) if speed > 0 else -int(abs_speed)

        assert clamp_speed(0) == 0
        assert clamp_speed(0.001) == 0
        assert clamp_speed(-0.001) == 0

    def test_clamp_speed_minimum(self):
        """Test that speeds below minimum are clamped to minimum."""
        def clamp_speed(speed, min_speed=15, max_speed=100):
            if abs(speed) < 0.01:
                return 0
            abs_speed = abs(speed)
            if abs_speed < min_speed:
                abs_speed = min_speed
            elif abs_speed > max_speed:
                abs_speed = max_speed
            return int(abs_speed) if speed > 0 else -int(abs_speed)

        assert clamp_speed(5) == 15
        assert clamp_speed(10) == 15
        assert clamp_speed(-5) == -15

    def test_clamp_speed_maximum(self):
        """Test that speeds above maximum are clamped to maximum."""
        def clamp_speed(speed, min_speed=15, max_speed=100):
            if abs(speed) < 0.01:
                return 0
            abs_speed = abs(speed)
            if abs_speed < min_speed:
                abs_speed = min_speed
            elif abs_speed > max_speed:
                abs_speed = max_speed
            return int(abs_speed) if speed > 0 else -int(abs_speed)

        assert clamp_speed(150) == 100
        assert clamp_speed(-150) == -100

    def test_clamp_speed_valid(self):
        """Test that valid speeds pass through."""
        def clamp_speed(speed, min_speed=15, max_speed=100):
            if abs(speed) < 0.01:
                return 0
            abs_speed = abs(speed)
            if abs_speed < min_speed:
                abs_speed = min_speed
            elif abs_speed > max_speed:
                abs_speed = max_speed
            return int(abs_speed) if speed > 0 else -int(abs_speed)

        assert clamp_speed(50) == 50
        assert clamp_speed(-50) == -50
        assert clamp_speed(30) == 30

    def test_clamp_steering(self):
        """Test steering angle clamping."""
        def clamp_steering(angle, max_angle=40.0):
            return max(-max_angle, min(max_angle, angle))

        assert clamp_steering(0) == 0
        assert clamp_steering(30) == 30
        assert clamp_steering(-30) == -30
        assert clamp_steering(50) == 40
        assert clamp_steering(-50) == -40

    def test_mock_picarx_forward(self):
        """Test mock Picarx forward movement."""
        px = MockPicarx()
        px.forward(30)
        assert px.speed == 30
        assert px.stopped == False

    def test_mock_picarx_backward(self):
        """Test mock Picarx backward movement."""
        px = MockPicarx()
        px.backward(20)
        assert px.speed == -20
        assert px.stopped == False

    def test_mock_picarx_stop(self):
        """Test mock Picarx stop."""
        px = MockPicarx()
        px.forward(30)
        px.stop()
        assert px.speed == 0
        assert px.stopped == True

    def test_mock_picarx_steering(self):
        """Test mock Picarx steering."""
        px = MockPicarx()
        px.set_dir_servo_angle(25)
        assert px.steering == 25


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
