#!/usr/bin/env python3
"""
Hardware Bridge Node - Owns the Picarx instance and handles all hardware I/O.

This is the ONLY node that directly interfaces with the picarx library.
All other nodes must publish to /btbg/hw/* topics to control hardware.

Subscriptions:
    /btbg/hw/drive (Float32MultiArray): [speed, steering_angle]
    /btbg/hw/servo (Float32MultiArray): [pan, tilt]
    /btbg/hw/stop (Empty): Emergency stop
    /btbg/hw/buzzer (Bool): Buzzer on/off

Publishers:
    /btbg/hw/status (String): JSON status of hardware state
"""

import signal
import sys
import json
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import Float32MultiArray, Empty, Bool, String

# Only import picarx on the actual Pi
try:
    from picarx import Picarx
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    print("WARNING: picarx not available - running in simulation mode")


class HardwareBridgeNode(Node):
    """
    Hardware abstraction node that owns the Picarx instance.

    All motor/servo commands go through this node to prevent I2C conflicts.
    Implements a hardware watchdog that stops motors if no commands received.
    """

    def __init__(self):
        super().__init__('hardware_bridge_node')

        # Declare parameters
        self.declare_parameter('watchdog_timeout_ms', 1500)
        self.declare_parameter('min_motor_speed', 15)
        self.declare_parameter('max_motor_speed', 100)
        self.declare_parameter('max_steering_angle', 40.0)
        self.declare_parameter('publish_rate_hz', 10.0)

        # Get parameters
        self.watchdog_timeout_ms = self.get_parameter('watchdog_timeout_ms').value
        self.min_motor_speed = self.get_parameter('min_motor_speed').value
        self.max_motor_speed = self.get_parameter('max_motor_speed').value
        self.max_steering_angle = self.get_parameter('max_steering_angle').value
        publish_rate = self.get_parameter('publish_rate_hz').value

        # Initialize hardware
        self.px = None
        if HARDWARE_AVAILABLE:
            try:
                self.px = Picarx()
                self.get_logger().info('Picarx initialized successfully')
            except Exception as e:
                self.get_logger().error(f'Failed to initialize Picarx: {e}')
        else:
            self.get_logger().warn('Running in simulation mode (no hardware)')

        # State tracking
        self.current_speed = 0.0
        self.current_steering = 0.0
        self.current_pan = 0.0
        self.current_tilt = 0.0
        self.last_command_time = self.get_clock().now()
        self.is_stopped = True

        # QoS profile for reliable delivery
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)

        # Subscribers
        self.drive_sub = self.create_subscription(
            Float32MultiArray,
            '/btbg/hw/drive',
            self.drive_callback,
            qos
        )
        self.servo_sub = self.create_subscription(
            Float32MultiArray,
            '/btbg/hw/servo',
            self.servo_callback,
            qos
        )
        self.stop_sub = self.create_subscription(
            Empty,
            '/btbg/hw/stop',
            self.stop_callback,
            qos
        )
        self.buzzer_sub = self.create_subscription(
            Bool,
            '/btbg/hw/buzzer',
            self.buzzer_callback,
            qos
        )

        # Publishers
        self.status_pub = self.create_publisher(String, '/btbg/hw/status', qos)

        # Watchdog timer
        watchdog_period = self.watchdog_timeout_ms / 1000.0 / 2  # Check twice per timeout
        self.watchdog_timer = self.create_timer(watchdog_period, self.watchdog_callback)

        # Status publish timer
        self.status_timer = self.create_timer(1.0 / publish_rate, self.publish_status)

        # Register shutdown handler
        self._setup_signal_handlers()

        self.get_logger().info(f'Hardware Bridge Node started (watchdog: {self.watchdog_timeout_ms}ms)')

    def _setup_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        def shutdown_handler(signum, frame):
            self.get_logger().info('Shutdown signal received, stopping motors')
            self.emergency_stop()
            sys.exit(0)

        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)

    def clamp_speed(self, speed: float) -> int:
        """Clamp speed to valid range, respecting motor stall threshold."""
        if abs(speed) < 0.01:  # Treat very small speeds as stop
            return 0

        # Clamp absolute value to min/max range
        abs_speed = abs(speed)
        if abs_speed < self.min_motor_speed:
            abs_speed = self.min_motor_speed
        elif abs_speed > self.max_motor_speed:
            abs_speed = self.max_motor_speed

        return int(abs_speed) if speed > 0 else -int(abs_speed)

    def clamp_steering(self, angle: float) -> float:
        """Clamp steering angle to valid range."""
        return max(-self.max_steering_angle, min(self.max_steering_angle, angle))

    def drive_callback(self, msg: Float32MultiArray):
        """
        Handle drive commands.

        Args:
            msg.data[0]: speed (-100 to 100, negative = reverse)
            msg.data[1]: steering angle (-40 to 40 degrees)
        """
        if len(msg.data) < 2:
            self.get_logger().warn('Invalid drive message: expected [speed, steering]')
            return

        speed = msg.data[0]
        steering = msg.data[1]

        # Clamp values
        clamped_speed = self.clamp_speed(speed)
        clamped_steering = self.clamp_steering(steering)

        # Update state
        self.current_speed = clamped_speed
        self.current_steering = clamped_steering
        self.last_command_time = self.get_clock().now()

        # Apply to hardware
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
                self.get_logger().error(f'Drive command failed: {e}')
        else:
            self.get_logger().debug(f'SIM: drive speed={clamped_speed}, steering={clamped_steering}')
            self.is_stopped = (clamped_speed == 0)

    def servo_callback(self, msg: Float32MultiArray):
        """
        Handle camera servo commands.

        Args:
            msg.data[0]: pan angle (-90 to 90 degrees)
            msg.data[1]: tilt angle (-35 to 35 degrees)
        """
        if len(msg.data) < 2:
            self.get_logger().warn('Invalid servo message: expected [pan, tilt]')
            return

        pan = max(-90, min(90, msg.data[0]))
        tilt = max(-35, min(35, msg.data[1]))

        self.current_pan = pan
        self.current_tilt = tilt

        if self.px:
            try:
                self.px.set_cam_pan_angle(pan)
                self.px.set_cam_tilt_angle(tilt)
            except Exception as e:
                self.get_logger().error(f'Servo command failed: {e}')
        else:
            self.get_logger().debug(f'SIM: servo pan={pan}, tilt={tilt}')

    def stop_callback(self, msg: Empty):
        """Handle emergency stop command."""
        self.get_logger().info('Emergency stop received')
        self.emergency_stop()

    def emergency_stop(self):
        """Stop all motors immediately."""
        self.current_speed = 0.0
        self.is_stopped = True

        if self.px:
            try:
                self.px.stop()
            except Exception as e:
                self.get_logger().error(f'Emergency stop failed: {e}')
        else:
            self.get_logger().debug('SIM: emergency stop')

    def buzzer_callback(self, msg: Bool):
        """Handle buzzer on/off command."""
        if self.px:
            try:
                # Note: buzzer control depends on robot-hat library version
                # This may need adjustment based on actual API
                pass  # TODO: Implement buzzer control
            except Exception as e:
                self.get_logger().error(f'Buzzer command failed: {e}')
        else:
            self.get_logger().debug(f'SIM: buzzer {"on" if msg.data else "off"}')

    def watchdog_callback(self):
        """Check if we've received commands recently, stop if not."""
        if self.is_stopped:
            return

        now = self.get_clock().now()
        elapsed_ms = (now - self.last_command_time).nanoseconds / 1e6

        if elapsed_ms > self.watchdog_timeout_ms:
            self.get_logger().warn(f'Watchdog timeout ({elapsed_ms:.0f}ms), stopping motors')
            self.emergency_stop()

    def publish_status(self):
        """Publish current hardware status."""
        status = {
            'speed': self.current_speed,
            'steering': self.current_steering,
            'pan': self.current_pan,
            'tilt': self.current_tilt,
            'is_stopped': self.is_stopped,
            'hardware_available': HARDWARE_AVAILABLE and self.px is not None,
            'timestamp': self.get_clock().now().nanoseconds
        }

        msg = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = HardwareBridgeNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.emergency_stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
