#!/usr/bin/env python3
"""
Car Control Node - Mode arbiter between manual and patrol control.

This node receives commands from the UI (manual mode) and patrol_node (patrol mode).
It forwards only the active mode's commands to hardware_bridge_node.

Subscriptions:
    /btbg/cmd_vel (Twist): Manual drive commands from UI
    /btbg/patrol_cmd_vel (Twist): Autonomous commands from patrol_node
    /btbg/mode (String): "manual" or "patrol"
    /btbg/servo_cmd (Float32MultiArray): Camera servo commands [pan, tilt]

Publishers:
    /btbg/hw/drive (Float32MultiArray): [speed, steering] to hardware_bridge
    /btbg/hw/servo (Float32MultiArray): [pan, tilt] to hardware_bridge
    /btbg/hw/stop (Empty): Emergency stop
    /btbg/status (String): JSON status
"""

import json
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray, String, Empty


class CarControlNode(Node):
    """
    Central command arbiter for manual and autonomous control.

    Implements a watchdog that stops the car if no commands received in manual mode.
    In patrol mode, the patrol_node handles its own watchdog.
    """

    def __init__(self):
        super().__init__('car_control_node')

        # Declare parameters
        self.declare_parameter('max_speed', 100)
        self.declare_parameter('min_speed', 15)
        self.declare_parameter('max_steering_angle', 40.0)
        self.declare_parameter('watchdog_timeout_ms', 1000)
        self.declare_parameter('publish_rate_hz', 20.0)

        # Get parameters
        self.max_speed = self.get_parameter('max_speed').value
        self.min_speed = self.get_parameter('min_speed').value
        self.max_steering_angle = self.get_parameter('max_steering_angle').value
        self.watchdog_timeout_ms = self.get_parameter('watchdog_timeout_ms').value
        publish_rate = self.get_parameter('publish_rate_hz').value

        # State
        self.current_mode = 'manual'  # 'manual' or 'patrol'
        self.last_manual_cmd_time = self.get_clock().now()
        self.current_speed = 0.0
        self.current_steering = 0.0
        self.is_moving = False

        # QoS profile
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)

        # Subscribers
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/btbg/cmd_vel',
            self.manual_cmd_callback,
            qos
        )
        self.patrol_cmd_sub = self.create_subscription(
            Twist,
            '/btbg/patrol_cmd_vel',
            self.patrol_cmd_callback,
            qos
        )
        self.mode_sub = self.create_subscription(
            String,
            '/btbg/mode',
            self.mode_callback,
            qos
        )
        self.servo_sub = self.create_subscription(
            Float32MultiArray,
            '/btbg/servo_cmd',
            self.servo_callback,
            qos
        )

        # Publishers
        self.drive_pub = self.create_publisher(Float32MultiArray, '/btbg/hw/drive', qos)
        self.servo_pub = self.create_publisher(Float32MultiArray, '/btbg/hw/servo', qos)
        self.stop_pub = self.create_publisher(Empty, '/btbg/hw/stop', qos)
        self.status_pub = self.create_publisher(String, '/btbg/status', qos)

        # Timers
        watchdog_period = self.watchdog_timeout_ms / 1000.0 / 2
        self.watchdog_timer = self.create_timer(watchdog_period, self.watchdog_callback)
        self.status_timer = self.create_timer(1.0 / publish_rate, self.publish_status)

        self.get_logger().info(f'Car Control Node started (mode: {self.current_mode})')

    def scale_twist_to_drive(self, twist: Twist) -> tuple:
        """
        Convert Twist message to speed and steering values.

        Args:
            twist: geometry_msgs/Twist with linear.x (-1 to 1) and angular.z (-1 to 1)

        Returns:
            (speed, steering): speed in -100 to 100, steering in -40 to 40
        """
        # linear.x: -1.0 to 1.0 -> speed: -100 to 100
        speed = twist.linear.x * self.max_speed

        # angular.z: -1.0 to 1.0 -> steering: -40 to 40
        # Note: positive angular.z = left turn, negative = right turn
        steering = twist.angular.z * self.max_steering_angle

        return speed, steering

    def publish_drive(self, speed: float, steering: float):
        """Publish drive command to hardware bridge."""
        msg = Float32MultiArray()
        msg.data = [float(speed), float(steering)]
        self.drive_pub.publish(msg)

        self.current_speed = speed
        self.current_steering = steering
        self.is_moving = abs(speed) > 0.01

    def manual_cmd_callback(self, msg: Twist):
        """Handle manual drive commands from UI."""
        if self.current_mode != 'manual':
            return  # Ignore if not in manual mode

        speed, steering = self.scale_twist_to_drive(msg)
        self.publish_drive(speed, steering)
        self.last_manual_cmd_time = self.get_clock().now()

    def patrol_cmd_callback(self, msg: Twist):
        """Handle autonomous drive commands from patrol node."""
        if self.current_mode != 'patrol':
            return  # Ignore if not in patrol mode

        speed, steering = self.scale_twist_to_drive(msg)
        self.publish_drive(speed, steering)

    def mode_callback(self, msg: String):
        """Handle mode switch commands."""
        new_mode = msg.data.lower().strip()

        if new_mode not in ['manual', 'patrol']:
            self.get_logger().warn(f'Invalid mode: {new_mode}')
            return

        if new_mode != self.current_mode:
            self.get_logger().info(f'Mode changed: {self.current_mode} -> {new_mode}')

            # Stop the car on mode change
            self.publish_drive(0, 0)

            self.current_mode = new_mode
            self.last_manual_cmd_time = self.get_clock().now()

    def servo_callback(self, msg: Float32MultiArray):
        """Forward servo commands to hardware bridge."""
        if len(msg.data) >= 2:
            servo_msg = Float32MultiArray()
            servo_msg.data = [msg.data[0], msg.data[1]]
            self.servo_pub.publish(servo_msg)

    def watchdog_callback(self):
        """Stop car if no commands received in manual mode."""
        if self.current_mode != 'manual':
            return  # Patrol mode has its own watchdog

        if not self.is_moving:
            return  # Already stopped

        now = self.get_clock().now()
        elapsed_ms = (now - self.last_manual_cmd_time).nanoseconds / 1e6

        if elapsed_ms > self.watchdog_timeout_ms:
            self.get_logger().warn(f'Manual watchdog timeout ({elapsed_ms:.0f}ms)')
            self.publish_drive(0, 0)

    def publish_status(self):
        """Publish current status."""
        status = {
            'mode': self.current_mode,
            'speed': self.current_speed,
            'steering': self.current_steering,
            'is_moving': self.is_moving,
            'timestamp': self.get_clock().now().nanoseconds
        }

        msg = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = CarControlNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Stop the car on shutdown
        stop_msg = Float32MultiArray()
        stop_msg.data = [0.0, 0.0]
        node.drive_pub.publish(stop_msg)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
