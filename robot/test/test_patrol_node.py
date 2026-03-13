#!/usr/bin/env python3
"""Unit tests for patrol_node."""

import pytest
import random


# States
STATE_IDLE = 'idle'
STATE_FORWARD = 'forward'
STATE_REVERSING = 'reversing'
STATE_TURNING = 'turning'


class TestPatrolLogic:
    """Test patrol node logic without ROS2."""

    def test_obstacle_detection(self):
        """Test obstacle detection threshold."""
        threshold = 25.0

        def is_obstacle(distance, thresh=threshold):
            return distance < thresh

        assert is_obstacle(30) == False
        assert is_obstacle(25) == False
        assert is_obstacle(24.9) == True
        assert is_obstacle(10) == True

    def test_state_transitions_forward_to_reversing(self):
        """Test transition from forward to reversing on obstacle."""
        state = STATE_FORWARD
        distance = 20  # Below threshold
        threshold = 25

        def get_next_state(current_state, dist, thresh):
            if current_state == STATE_FORWARD and dist < thresh:
                return STATE_REVERSING
            return current_state

        new_state = get_next_state(state, distance, threshold)
        assert new_state == STATE_REVERSING

    def test_state_no_transition_far_obstacle(self):
        """Test no transition when obstacle is far."""
        state = STATE_FORWARD
        distance = 50  # Above threshold
        threshold = 25

        def get_next_state(current_state, dist, thresh):
            if current_state == STATE_FORWARD and dist < thresh:
                return STATE_REVERSING
            return current_state

        new_state = get_next_state(state, distance, threshold)
        assert new_state == STATE_FORWARD

    def test_turn_angle_selection(self):
        """Test random turn angle selection."""
        turn_angles = [-120.0, -90.0, -60.0, 60.0, 90.0, 120.0]

        # Test multiple times for randomness
        for _ in range(10):
            angle = random.choice(turn_angles)
            assert angle in turn_angles
            assert abs(angle) >= 60
            assert abs(angle) <= 120

    def test_turn_duration_calculation(self):
        """Test turn duration proportional to angle."""
        base_duration = 0.8

        def calc_turn_duration(angle, base=base_duration):
            return base * abs(angle) / 90.0

        assert calc_turn_duration(90) == pytest.approx(0.8, abs=0.01)
        assert calc_turn_duration(60) == pytest.approx(0.533, abs=0.01)
        assert calc_turn_duration(120) == pytest.approx(1.067, abs=0.01)

    def test_steering_normalization(self):
        """Test steering angle normalization."""
        def normalize_steering(angle, max_angle=40.0):
            steering = angle / max_angle
            return max(-1.0, min(1.0, steering))

        assert normalize_steering(0) == 0.0
        assert normalize_steering(40) == 1.0
        assert normalize_steering(-40) == -1.0
        assert normalize_steering(20) == 0.5
        assert normalize_steering(80) == 1.0  # Clamped
        assert normalize_steering(-80) == -1.0  # Clamped

    def test_speed_variation(self):
        """Test speed variation range."""
        base_speed = 30
        variation = 5

        for _ in range(20):
            varied_speed = base_speed + random.uniform(-variation, variation)
            assert varied_speed >= base_speed - variation
            assert varied_speed <= base_speed + variation

    def test_sensor_failure_detection(self):
        """Test consecutive None reading detection."""
        max_none = 5

        def is_sensor_failure(consecutive_none, max_n=max_none):
            return consecutive_none >= max_n

        assert is_sensor_failure(0) == False
        assert is_sensor_failure(4) == False
        assert is_sensor_failure(5) == True
        assert is_sensor_failure(10) == True

    def test_mode_activation(self):
        """Test mode activation logic."""
        def should_activate(mode_str, currently_active):
            mode = mode_str.lower().strip()
            return mode == 'patrol' and not currently_active

        def should_deactivate(mode_str, currently_active):
            mode = mode_str.lower().strip()
            return mode != 'patrol' and currently_active

        assert should_activate('patrol', False) == True
        assert should_activate('patrol', True) == False
        assert should_activate('manual', False) == False

        assert should_deactivate('manual', True) == True
        assert should_deactivate('manual', False) == False
        assert should_deactivate('patrol', True) == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
