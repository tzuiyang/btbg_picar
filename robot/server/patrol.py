"""
Patrol - Autonomous random patrol behavior (state machine).

States: IDLE -> FORWARD -> REVERSING -> TURNING -> FORWARD
"""

import random
import time
import logging

log = logging.getLogger("btbg.patrol")

STATE_IDLE = "idle"
STATE_FORWARD = "forward"
STATE_REVERSING = "reversing"
STATE_TURNING = "turning"


class Patrol:
    def __init__(self, config: dict):
        self.speed = config.get("speed", 30)
        self.obstacle_threshold = config.get("obstacle_threshold_cm", 25.0)
        self.reverse_speed = config.get("reverse_speed", 20)
        self.reverse_duration = config.get("reverse_duration_s", 0.5)
        self.turn_duration_base = config.get("turn_duration_base_s", 0.8)
        self.turn_angles = config.get("turn_angles", [-120, -90, -60, 60, 90, 120])
        self.max_none_readings = config.get("max_none_readings", 5)
        self.speed_variation = config.get("speed_variation", 5)

        self.state = STATE_IDLE
        self.is_active = False
        self.current_distance = 100.0
        self.consecutive_none = 0
        self.current_turn_angle = 0.0
        self._transition_deadline = None
        self._next_state = None

    def activate(self):
        if not self.is_active:
            log.info("Patrol mode activated")
            self.is_active = True
            self.state = STATE_FORWARD
            self.consecutive_none = 0

    def deactivate(self):
        if self.is_active:
            log.info("Patrol mode deactivated")
            self.is_active = False
            self.state = STATE_IDLE
            self._transition_deadline = None

    def update_distance(self, distance_cm: float | None):
        if distance_cm is None or distance_cm <= 0 or distance_cm > 300:
            self.consecutive_none += 1
        else:
            self.consecutive_none = 0
            self.current_distance = distance_cm

    def tick(self) -> tuple[float, float] | None:
        """
        Run one tick of the patrol loop.
        Returns (speed_normalized, steering_normalized) or None if idle/stopped.
        Speed and steering are -1..1 (same scale the UI uses).
        """
        if not self.is_active:
            return None

        # Check sensor failure
        if self.consecutive_none >= self.max_none_readings:
            log.warning("Ultrasonic sensor failure, stopping patrol")
            self.state = STATE_IDLE
            return (0.0, 0.0)

        # Check pending transitions
        if self._transition_deadline and time.monotonic() >= self._transition_deadline:
            self.state = self._next_state
            self._transition_deadline = None
            self._next_state = None
            log.debug("Transition to %s", self.state)

        if self.state == STATE_FORWARD:
            if self.current_distance < self.obstacle_threshold:
                log.info("Obstacle at %.1fcm, reversing", self.current_distance)
                self.state = STATE_REVERSING
                self._transition_deadline = time.monotonic() + self.reverse_duration
                self._next_state = STATE_TURNING
                return (-self.reverse_speed / 100.0, 0.0)
            else:
                variation = random.uniform(-self.speed_variation, self.speed_variation)
                return ((self.speed + variation) / 100.0, 0.0)

        elif self.state == STATE_REVERSING:
            return (-self.reverse_speed / 100.0, 0.0)

        elif self.state == STATE_TURNING:
            if self.current_turn_angle == 0:
                self.current_turn_angle = random.choice(self.turn_angles)
                turn_duration = self.turn_duration_base * abs(self.current_turn_angle) / 90.0
                log.info("Turning %.0f deg for %.2fs", self.current_turn_angle, turn_duration)
                self._transition_deadline = time.monotonic() + turn_duration
                self._next_state = STATE_FORWARD

            steering = self.current_turn_angle / 40.0
            steering = max(-1.0, min(1.0, steering))
            speed = self.speed / 100.0 * 0.5
            return (speed, steering)

        # IDLE or unknown
        return None

    def on_state_exit(self):
        """Called when transitioning away from TURNING."""
        if self.state != STATE_TURNING:
            self.current_turn_angle = 0.0

    def get_status(self) -> dict:
        return {
            "state": self.state,
            "isActive": self.is_active,
            "distance": self.current_distance,
            "turnAngle": self.current_turn_angle,
        }
