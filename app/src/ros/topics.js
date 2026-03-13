/**
 * ROS Topic Definitions
 *
 * Central definition of all ROS2 topics used by the UI.
 * Message types match ROS2 message definitions.
 */

export const TOPICS = {
  // Commands (UI -> Robot)
  CMD_VEL: {
    name: '/btbg/cmd_vel',
    messageType: 'geometry_msgs/Twist',
  },
  MODE: {
    name: '/btbg/mode',
    messageType: 'std_msgs/String',
  },
  SERVO_CMD: {
    name: '/btbg/servo_cmd',
    messageType: 'std_msgs/Float32MultiArray',
  },
  HW_STOP: {
    name: '/btbg/hw/stop',
    messageType: 'std_msgs/Empty',
  },

  // Telemetry (Robot -> UI)
  SENSOR_ULTRASONIC: {
    name: '/btbg/sensor/ultrasonic',
    messageType: 'sensor_msgs/Range',
  },
  SENSOR_GRAYSCALE: {
    name: '/btbg/sensor/grayscale',
    messageType: 'std_msgs/Float32MultiArray',
  },
  SENSOR_BATTERY: {
    name: '/btbg/sensor/battery',
    messageType: 'std_msgs/Float32',
  },
  SENSOR_BATTERY_WARNING: {
    name: '/btbg/sensor/battery_warning',
    messageType: 'std_msgs/Bool',
  },
  STATUS: {
    name: '/btbg/status',
    messageType: 'std_msgs/String',
  },
  PATROL_STATUS: {
    name: '/btbg/patrol_status',
    messageType: 'std_msgs/String',
  },
  HW_STATUS: {
    name: '/btbg/hw/status',
    messageType: 'std_msgs/String',
  },
};

export default TOPICS;
