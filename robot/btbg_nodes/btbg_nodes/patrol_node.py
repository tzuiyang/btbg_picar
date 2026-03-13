#!/usr/bin/env python3
"""
Patrol Node - Autonomous random patrol behavior.

State machine:
    IDLE -> FORWARD -> REVERSING -> TURNING -> FORWARD

Uses ROS2 timers for non-blocking state transitions.

Subscriptions:
    /btbg/mode (String): Activates when "patrol"
    /btbg/sensor/ultrasonic (Range): Distance readings

Publishers:
    /btbg/patrol_cmd_vel (Twist): Drive commands to car_control_node
    /btbg/patrol_status (String): JSON state information
"""

import json
import random
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Range
from std_msgs.msg import String

# Patrol states
STATE_IDLE = 'idle'
STATE_FORWARD = 'forward'
STATE_REVERSING = 'reversing'
STATE_TURNING = 'turning'


class PatrolNode(Node):
    """
    Autonomous patrol behavior using a state machine.

    Drives forward until obstacle detected, then reverses and turns randomly.
    Uses ROS2 timers instead of sleep() to avoid blocking.
    """

    def __init__(self):
        super().__init__('patrol_node')

        # Declare parameters
        self.declare_parameter('speed', 30)
        self.declare_parameter('obstacle_threshold_cm', 25.0)
        self.declare_parameter('reverse_speed', 20)
        self.declare_parameter('reverse_duration_s', 0.5)
        self.declare_parameter('turn_duration_base_s', 0.8)
        self.declare_parameter('scan_interval_ms', 100)
        self.declare_parameter('turn_angles', [-120.0, -90.0, -60.0, 60.0, 90.0, 120.0])
        self.declare_parameter('max_none_readings', 5)
        self.declare_parameter('speed_variation', 5)

        # Get parameters
        self.patrol_speed = self.get_parameter('speed').value
        self.obstacle_threshold = self.get_parameter('obstacle_threshold_cm').value
        self.reverse_speed = self.get_parameter('reverse_speed').value
        self.reverse_duration = self.get_parameter('reverse_duration_s').value
        self.turn_duration_base = self.get_parameter('turn_duration_base_s').value
        scan_interval_ms = self.get_parameter('scan_interval_ms').value
        self.turn_angles = self.get_parameter('turn_angles').value
        self.max_none_readings = self.get_parameter('max_none_readings').value
        self.speed_variation = self.get_parameter('speed_variation').value

        # State
        self.state = STATE_IDLE
        self.is_patrol_active = False
        self.current_distance = 100.0  # Default far distance
        self.consecutive_none_readings = 0
        self.current_turn_angle = 0.0

        # Timers for state transitions (created dynamically)
        self.transition_timer = None

        # QoS profile
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)

        # Subscribers
        self.mode_sub = self.create_subscription(
            String,
            '/btbg/mode',
            self.mode_callback,
            qos
        )
        self.ultrasonic_sub = self.create_subscription(
            Range,
            '/btbg/sensor/ultrasonic',
            self.ultrasonic_callback,
            qos
        )

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/btbg/patrol_cmd_vel', qos)
        self.status_pub = self.create_publisher(String, '/btbg/patrol_status', qos)

        # Main loop timer
        self.loop_timer = self.create_timer(scan_interval_ms / 1000.0, self.patrol_loop)

        # Status publish timer
        self.status_timer = self.create_timer(0.2, self.publish_status)

        self.get_logger().info('Patrol Node started (idle, waiting for patrol mode)')

    def mode_callback(self, msg: String):
        """Handle mode changes."""
        mode = msg.data.lower().strip()

        if mode == 'patrol' and not self.is_patrol_active:
            self.get_logger().info('Patrol mode activated')
            self.is_patrol_active = True
            self.state = STATE_FORWARD
            self.consecutive_none_readings = 0
        elif mode != 'patrol' and self.is_patrol_active:
            self.get_logger().info('Patrol mode deactivated')
            self.is_patrol_active = False
            self.state = STATE_IDLE
            self.stop_car()
            self.cancel_transition_timer()

    def ultrasonic_callback(self, msg: Range):
        """Handle ultrasonic sensor readings."""
        # Convert meters back to cm
        distance_cm = msg.range * 100.0

        if distance_cm <= 0 or distance_cm > 300:
            self.consecutive_none_readings += 1
        else:
            self.consecutive_none_readings = 0
            self.current_distance = distance_cm

    def publish_cmd_vel(self, linear_x: float, angular_z: float):
        """Publish velocity command."""
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.cmd_vel_pub.publish(msg)

    def stop_car(self):
        """Stop the car."""
        self.publish_cmd_vel(0.0, 0.0)

    def drive_forward(self):
        """Drive forward with slight speed variation."""
        variation = random.uniform(-self.speed_variation, self.speed_variation)
        speed = (self.patrol_speed + variation) / 100.0  # Normalize to -1 to 1
        self.publish_cmd_vel(speed, 0.0)

    def drive_reverse(self):
        """Drive in reverse."""
        speed = -self.reverse_speed / 100.0  # Normalize and negate
        self.publish_cmd_vel(speed, 0.0)

    def turn(self, angle: float):
        """Turn with given steering angle."""
        # Steering angle normalized: -1 to 1 maps to -40 to 40 degrees
        steering = angle / 40.0
        steering = max(-1.0, min(1.0, steering))

        # Move forward slowly while turning
        speed = self.patrol_speed / 100.0 * 0.5
        self.publish_cmd_vel(speed, steering)

    def cancel_transition_timer(self):
        """Cancel any pending transition timer."""
        if self.transition_timer is not None:
            self.transition_timer.cancel()
            self.transition_timer = None

    def schedule_transition(self, duration: float, next_state: str):
        """Schedule a state transition after duration seconds."""
        self.cancel_transition_timer()

        def transition_callback():
            self.cancel_transition_timer()
            if self.is_patrol_active:
                self.state = next_state
                self.get_logger().debug(f'Transition to {next_state}')

        self.transition_timer = self.create_timer(duration, transition_callback)

    def patrol_loop(self):
        """Main patrol state machine loop."""
        if not self.is_patrol_active:
            return

        # Check for sensor failure
        if self.consecutive_none_readings >= self.max_none_readings:
            self.get_logger().warn('Ultrasonic sensor failure, stopping')
            self.stop_car()
            self.state = STATE_IDLE
            return

        if self.state == STATE_FORWARD:
            # Check for obstacle
            if self.current_distance < self.obstacle_threshold:
                self.get_logger().info(f'Obstacle at {self.current_distance:.1f}cm, reversing')
                self.stop_car()
                self.state = STATE_REVERSING
                self.drive_reverse()
                self.schedule_transition(self.reverse_duration, STATE_TURNING)
            else:
                self.drive_forward()

        elif self.state == STATE_REVERSING:
            # Continue reversing (timer will transition to TURNING)
            self.drive_reverse()

        elif self.state == STATE_TURNING:
            # Start turn if not already turning
            if self.current_turn_angle == 0:
                self.current_turn_angle = random.choice(self.turn_angles)
                turn_duration = self.turn_duration_base * abs(self.current_turn_angle) / 90.0
                self.get_logger().info(f'Turning {self.current_turn_angle}° for {turn_duration:.2f}s')
                self.schedule_transition(turn_duration, STATE_FORWARD)

            self.turn(self.current_turn_angle)

        elif self.state == STATE_IDLE:
            self.stop_car()

    def publish_status(self):
        """Publish patrol status."""
        status = {
            'state': self.state,
            'is_active': self.is_patrol_active,
            'distance': self.current_distance,
            'turn_angle': self.current_turn_angle,
            'timestamp': self.get_clock().now().nanoseconds
        }

        msg = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)

        # Reset turn angle when we transition away from TURNING
        if self.state != STATE_TURNING:
            self.current_turn_angle = 0.0


def main(args=None):
    rclpy.init(args=args)
    node = PatrolNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_car()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
