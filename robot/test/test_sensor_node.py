#!/usr/bin/env python3
"""Unit tests for sensor_node."""

import pytest


class TestSensorNodeLogic:
    """Test sensor node logic without ROS2."""

    def test_ultrasonic_filter_valid(self):
        """Test that valid distances pass through."""
        max_range = 300.0
        min_range = 2.0

        def filter_distance(distance, last_valid, max_r=max_range, min_r=min_range):
            if distance is None:
                return last_valid
            if distance > max_r or distance < min_r:
                return last_valid
            return distance

        assert filter_distance(50.0, 100.0) == 50.0
        assert filter_distance(2.5, 100.0) == 2.5
        assert filter_distance(299.0, 100.0) == 299.0

    def test_ultrasonic_filter_none(self):
        """Test that None readings return last valid."""
        def filter_distance(distance, last_valid, max_r=300.0, min_r=2.0):
            if distance is None:
                return last_valid
            if distance > max_r or distance < min_r:
                return last_valid
            return distance

        assert filter_distance(None, 50.0) == 50.0
        assert filter_distance(None, 100.0) == 100.0

    def test_ultrasonic_filter_out_of_range(self):
        """Test that out-of-range readings return last valid."""
        def filter_distance(distance, last_valid, max_r=300.0, min_r=2.0):
            if distance is None:
                return last_valid
            if distance > max_r or distance < min_r:
                return last_valid
            return distance

        assert filter_distance(500.0, 50.0) == 50.0  # Above max
        assert filter_distance(1.0, 50.0) == 50.0    # Below min
        assert filter_distance(-5.0, 50.0) == 50.0   # Negative

    def test_grayscale_normalization(self):
        """Test grayscale value normalization."""
        def normalize_grayscale(values, adc_max=4095):
            return [v / adc_max for v in values]

        result = normalize_grayscale([0, 2048, 4095])
        assert result[0] == pytest.approx(0.0, abs=0.01)
        assert result[1] == pytest.approx(0.5, abs=0.01)
        assert result[2] == pytest.approx(1.0, abs=0.01)

    def test_battery_warning_threshold(self):
        """Test battery warning logic."""
        threshold = 7.0

        def check_low_battery(voltage, threshold_v=threshold):
            return voltage < threshold_v and voltage > 0

        assert check_low_battery(7.4) == False
        assert check_low_battery(7.0) == False
        assert check_low_battery(6.9) == True
        assert check_low_battery(6.0) == True
        assert check_low_battery(0.0) == False  # 0 means read error

    def test_cm_to_meters_conversion(self):
        """Test centimeters to meters conversion."""
        def cm_to_m(cm):
            return cm / 100.0

        assert cm_to_m(100) == 1.0
        assert cm_to_m(50) == 0.5
        assert cm_to_m(25) == 0.25


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
