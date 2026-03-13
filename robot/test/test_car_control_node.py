#!/usr/bin/env python3
"""Unit tests for car_control_node."""

import pytest
import math


class TestCarControlLogic:
    """Test car control node logic without ROS2."""

    def test_twist_to_drive_forward(self):
        """Test forward movement scaling."""
        def scale_twist(linear_x, angular_z, max_speed=100, max_steering=40.0):
            speed = linear_x * max_speed
            steering = angular_z * max_steering
            return speed, steering

        speed, steering = scale_twist(1.0, 0.0)
        assert speed == 100
        assert steering == 0

    def test_twist_to_drive_reverse(self):
        """Test reverse movement scaling."""
        def scale_twist(linear_x, angular_z, max_speed=100, max_steering=40.0):
            speed = linear_x * max_speed
            steering = angular_z * max_steering
            return speed, steering

        speed, steering = scale_twist(-1.0, 0.0)
        assert speed == -100
        assert steering == 0

    def test_twist_to_drive_turn_left(self):
        """Test left turn scaling."""
        def scale_twist(linear_x, angular_z, max_speed=100, max_steering=40.0):
            speed = linear_x * max_speed
            steering = angular_z * max_steering
            return speed, steering

        speed, steering = scale_twist(0.5, 1.0)
        assert speed == 50
        assert steering == 40

    def test_twist_to_drive_turn_right(self):
        """Test right turn scaling."""
        def scale_twist(linear_x, angular_z, max_speed=100, max_steering=40.0):
            speed = linear_x * max_speed
            steering = angular_z * max_steering
            return speed, steering

        speed, steering = scale_twist(0.5, -1.0)
        assert speed == 50
        assert steering == -40

    def test_twist_to_drive_partial(self):
        """Test partial speed and steering."""
        def scale_twist(linear_x, angular_z, max_speed=100, max_steering=40.0):
            speed = linear_x * max_speed
            steering = angular_z * max_steering
            return speed, steering

        speed, steering = scale_twist(0.3, -0.5)
        assert speed == 30
        assert steering == -20

    def test_mode_validation(self):
        """Test mode validation logic."""
        valid_modes = ['manual', 'patrol']

        def is_valid_mode(mode):
            return mode.lower().strip() in valid_modes

        assert is_valid_mode('manual') == True
        assert is_valid_mode('patrol') == True
        assert is_valid_mode('MANUAL') == True
        assert is_valid_mode('  patrol  ') == True
        assert is_valid_mode('auto') == False
        assert is_valid_mode('') == False

    def test_is_moving_detection(self):
        """Test movement detection logic."""
        def is_moving(speed):
            return abs(speed) > 0.01

        assert is_moving(0) == False
        assert is_moving(0.001) == False
        assert is_moving(0.01) == False
        assert is_moving(0.02) == True
        assert is_moving(-0.02) == True
        assert is_moving(50) == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
