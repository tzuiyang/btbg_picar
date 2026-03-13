#!/usr/bin/env python3
"""
Sensor Node - Publishes sensor data from PiCar-X hardware.

Publishers:
    /btbg/sensor/ultrasonic (sensor_msgs/Range): Distance reading in cm
    /btbg/sensor/grayscale (Float32MultiArray): [left, center, right] values 0-1
    /btbg/sensor/battery (Float32): Battery voltage
    /btbg/sensor/battery_warning (Bool): True if battery low
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Range
from std_msgs.msg import Float32MultiArray, Float32, Bool

# Only import picarx on the actual Pi
try:
    from picarx import Picarx
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    print("WARNING: picarx not available - running in simulation mode")


class SensorNode(Node):
    """
    Publishes sensor data at configured rates.

    Filters out invalid ultrasonic readings (None or > max_range).
    Publishes battery warning when voltage drops below threshold.
    """

    def __init__(self):
        super().__init__('sensor_node')

        # Declare parameters
        self.declare_parameter('ultrasonic_rate_hz', 10.0)
        self.declare_parameter('grayscale_rate_hz', 10.0)
        self.declare_parameter('battery_rate_hz', 0.5)
        self.declare_parameter('ultrasonic_max_range_cm', 300.0)
        self.declare_parameter('ultrasonic_min_range_cm', 2.0)
        self.declare_parameter('battery_low_warning_v', 7.0)

        # Get parameters
        ultrasonic_rate = self.get_parameter('ultrasonic_rate_hz').value
        grayscale_rate = self.get_parameter('grayscale_rate_hz').value
        battery_rate = self.get_parameter('battery_rate_hz').value
        self.max_range = self.get_parameter('ultrasonic_max_range_cm').value
        self.min_range = self.get_parameter('ultrasonic_min_range_cm').value
        self.battery_warning_threshold = self.get_parameter('battery_low_warning_v').value

        # Initialize hardware
        self.px = None
        if HARDWARE_AVAILABLE:
            try:
                self.px = Picarx()
                self.get_logger().info('Picarx initialized for sensors')
            except Exception as e:
                self.get_logger().error(f'Failed to initialize Picarx: {e}')
        else:
            self.get_logger().warn('Running in simulation mode (no hardware)')

        # State tracking
        self.last_valid_distance = self.max_range
        self.consecutive_none_readings = 0
        self.battery_warning_sent = False

        # Simulation state
        self.sim_distance = 50.0
        self.sim_battery = 7.4

        # QoS profile
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)

        # Publishers
        self.ultrasonic_pub = self.create_publisher(Range, '/btbg/sensor/ultrasonic', qos)
        self.grayscale_pub = self.create_publisher(Float32MultiArray, '/btbg/sensor/grayscale', qos)
        self.battery_pub = self.create_publisher(Float32, '/btbg/sensor/battery', qos)
        self.battery_warning_pub = self.create_publisher(Bool, '/btbg/sensor/battery_warning', qos)

        # Timers
        self.ultrasonic_timer = self.create_timer(1.0 / ultrasonic_rate, self.publish_ultrasonic)
        self.grayscale_timer = self.create_timer(1.0 / grayscale_rate, self.publish_grayscale)
        self.battery_timer = self.create_timer(1.0 / battery_rate, self.publish_battery)

        self.get_logger().info(f'Sensor Node started (ultrasonic: {ultrasonic_rate}Hz)')

    def read_ultrasonic(self) -> float:
        """Read ultrasonic sensor, return distance in cm or None if invalid."""
        if self.px:
            try:
                distance = self.px.ultrasonic.read()
                return distance
            except Exception as e:
                self.get_logger().error(f'Ultrasonic read failed: {e}')
                return None
        else:
            # Simulation: return varying distance
            import random
            self.sim_distance += random.uniform(-2, 2)
            self.sim_distance = max(10, min(100, self.sim_distance))
            return self.sim_distance

    def publish_ultrasonic(self):
        """Read and publish ultrasonic distance."""
        distance = self.read_ultrasonic()

        # Filter invalid readings
        if distance is None:
            self.consecutive_none_readings += 1
            if self.consecutive_none_readings >= 5:
                self.get_logger().warn('Ultrasonic sensor returning None repeatedly')
            distance = self.last_valid_distance  # Use last valid reading
        elif distance > self.max_range or distance < self.min_range:
            distance = self.last_valid_distance  # Filter noise
        else:
            self.consecutive_none_readings = 0
            self.last_valid_distance = distance

        # Create Range message
        msg = Range()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'ultrasonic_sensor'
        msg.radiation_type = Range.ULTRASOUND
        msg.field_of_view = 0.26  # ~15 degrees in radians
        msg.min_range = self.min_range / 100.0  # Convert to meters
        msg.max_range = self.max_range / 100.0  # Convert to meters
        msg.range = distance / 100.0  # Convert cm to meters

        self.ultrasonic_pub.publish(msg)

    def publish_grayscale(self):
        """Read and publish grayscale sensor values."""
        if self.px:
            try:
                # Read grayscale sensors (returns list of 3 values)
                values = self.px.get_grayscale_data()
                # Normalize to 0-1 range (assuming 0-4095 ADC range)
                normalized = [v / 4095.0 for v in values]
            except Exception as e:
                self.get_logger().error(f'Grayscale read failed: {e}')
                normalized = [0.5, 0.5, 0.5]
        else:
            # Simulation
            import random
            normalized = [random.uniform(0.3, 0.7) for _ in range(3)]

        msg = Float32MultiArray()
        msg.data = normalized
        self.grayscale_pub.publish(msg)

    def publish_battery(self):
        """Read and publish battery voltage."""
        if self.px:
            try:
                # Note: Battery reading method depends on robot-hat version
                # This may need adjustment
                voltage = 7.4  # TODO: Implement actual battery reading
            except Exception as e:
                self.get_logger().error(f'Battery read failed: {e}')
                voltage = 0.0
        else:
            # Simulation: slowly decreasing battery
            self.sim_battery -= 0.001
            self.sim_battery = max(6.0, self.sim_battery)
            voltage = self.sim_battery

        # Publish voltage
        voltage_msg = Float32()
        voltage_msg.data = voltage
        self.battery_pub.publish(voltage_msg)

        # Check for low battery warning
        is_low = voltage < self.battery_warning_threshold and voltage > 0
        if is_low and not self.battery_warning_sent:
            self.get_logger().warn(f'Low battery warning: {voltage:.2f}V')
            self.battery_warning_sent = True
        elif not is_low:
            self.battery_warning_sent = False

        warning_msg = Bool()
        warning_msg.data = is_low
        self.battery_warning_pub.publish(warning_msg)


def main(args=None):
    rclpy.init(args=args)
    node = SensorNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
