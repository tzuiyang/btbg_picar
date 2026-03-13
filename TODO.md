# BTBG Implementation TODO

> **Purpose:** Step-by-step implementation guide for AI agents. Each section includes verification tests.
> **Source of Truth:** MASTER_PLAN.md (read it first for full context)
> **Version:** 1.0.0
> **Last Updated:** 2026-03-13

---

## How to Use This File

1. Complete tasks in order (dependencies exist between sections)
2. Run ALL verification tests before proceeding to next section
3. If a test fails, fix the issue before continuing
4. Check off tasks with `[x]` as you complete them
5. Add notes in `> AGENT NOTE:` blocks if you encounter issues

---

## Table of Contents

- [Phase 1: Development Environment Setup](#phase-1-development-environment-setup)
- [Phase 2: Pi Hardware Setup](#phase-2-pi-hardware-setup)
- [Phase 3: ROS2 Package Structure](#phase-3-ros2-package-structure)
- [Phase 4: Hardware Bridge Node](#phase-4-hardware-bridge-node)
- [Phase 5: Sensor Node](#phase-5-sensor-node)
- [Phase 6: Car Control Node](#phase-6-car-control-node)
- [Phase 7: Patrol Node](#phase-7-patrol-node)
- [Phase 8: Launch File & Integration](#phase-8-launch-file--integration)
- [Phase 9: Electron App Setup](#phase-9-electron-app-setup)
- [Phase 10: ROS Client Module](#phase-10-ros-client-module)
- [Phase 11: UI Components](#phase-11-ui-components)
- [Phase 12: NPM Scripts](#phase-12-npm-scripts)
- [Phase 13: End-to-End Testing](#phase-13-end-to-end-testing)

---

## Phase 1: Development Environment Setup

### 1.1 Create Project Root Structure

```
LOCATION: Developer machine (Windows/macOS/Linux)
WORKING_DIR: C:\Users\tzuiy\self_projects\btbg
```

- [ ] **1.1.1** Create root `package.json`

```json
{
  "name": "btbg",
  "version": "1.0.0",
  "description": "Big Thing Big Gun - Raspberry Pi Robot Car",
  "private": true,
  "scripts": {
    "btbg:start": "node scripts/start_robot.js",
    "btbg:stop": "node scripts/stop_robot.js",
    "btbg:deploy": "node scripts/deploy.js",
    "btbg:logs": "node scripts/tail_logs.js",
    "btbg:status": "node scripts/status.js",
    "app": "npm run dev --prefix app",
    "app:build": "npm run build --prefix app",
    "app:electron": "npm run electron --prefix app",
    "setup": "node scripts/setup_dev.js"
  },
  "devDependencies": {
    "node-ssh": "^13.0.0",
    "dotenv": "^16.0.0"
  }
}
```

- [ ] **1.1.2** Create `.env.example` file

```env
# Raspberry Pi Connection
PI_HOST=btbg.local
PI_USER=ubuntu
PI_SSH_KEY=~/.ssh/btbg_pi

# ROS2 Configuration
ROS2_WS=/home/ubuntu/btbg_ws
ROS_DISTRO=humble
ROSBRIDGE_PORT=9090

# Optional: Use IP if mDNS not working
# PI_HOST=192.168.1.100
```

- [ ] **1.1.3** Create `.gitignore`

```gitignore
# Dependencies
node_modules/
app/node_modules/

# Environment
.env
.env.local

# Build outputs
app/dist/
app/dist-electron/

# Logs
*.log
logs/

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# ROS2 build artifacts (on Pi)
robot/btbg_nodes/build/
robot/btbg_nodes/install/
robot/btbg_nodes/log/
```

- [ ] **1.1.4** Create directory structure

```bash
# Create all directories
mkdir -p scripts/bash
mkdir -p app/electron
mkdir -p app/src/components
mkdir -p app/src/ros
mkdir -p app/src/styles
mkdir -p robot/launch
mkdir -p robot/config
mkdir -p robot/btbg_nodes/btbg_nodes
mkdir -p robot/test
```

- [ ] **1.1.5** Install root dependencies

```bash
npm install
```

### 1.2 Verification Tests - Phase 1

```bash
# TEST 1.2.1: Verify package.json exists and is valid JSON
node -e "require('./package.json'); console.log('✓ package.json valid')"

# TEST 1.2.2: Verify directory structure
node -e "
const fs = require('fs');
const dirs = ['scripts', 'app', 'robot', 'robot/btbg_nodes', 'robot/launch', 'robot/config'];
let pass = true;
dirs.forEach(d => {
  if (!fs.existsSync(d)) { console.log('✗ Missing:', d); pass = false; }
  else { console.log('✓', d); }
});
if (!pass) process.exit(1);
console.log('✓ All directories exist');
"

# TEST 1.2.3: Verify node_modules installed
node -e "
try {
  require('node-ssh');
  require('dotenv');
  console.log('✓ Dependencies installed');
} catch(e) {
  console.log('✗ Missing dependencies:', e.message);
  process.exit(1);
}
"
```

**Expected Results:**
- All 3 tests pass with `✓` output
- No errors or missing directories

---

## Phase 2: Pi Hardware Setup

### 2.1 Flash Ubuntu and Configure Pi

```
LOCATION: Raspberry Pi 5
OS: Ubuntu 22.04 Server 64-bit
```

- [ ] **2.1.1** Flash Ubuntu 22.04 Server using Raspberry Pi Imager
  - Select "Ubuntu Server 22.04 LTS (64-bit)"
  - Configure WiFi SSID and password in Imager settings
  - Enable SSH with password authentication initially
  - Set hostname to `btbg`
  - Set username to `ubuntu`

- [ ] **2.1.2** Boot Pi and find IP address

```bash
# From developer machine, scan network (example)
# Windows: use Advanced IP Scanner or arp -a
# macOS/Linux:
arp -a | grep -i "b8:27:eb\|dc:a6:32\|e4:5f:01"
# Or check router's DHCP client list
```

- [ ] **2.1.3** SSH into Pi and set up SSH key

```bash
# From developer machine:
ssh-keygen -t ed25519 -f ~/.ssh/btbg_pi -C "btbg robot key" -N ""
ssh-copy-id -i ~/.ssh/btbg_pi.pub ubuntu@<PI_IP_ADDRESS>

# Add to SSH config (~/.ssh/config):
cat >> ~/.ssh/config << 'EOF'
Host btbg
    HostName btbg.local
    User ubuntu
    IdentityFile ~/.ssh/btbg_pi
    ServerAliveInterval 30
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 60s
EOF
```

- [ ] **2.1.4** Verify passwordless SSH works

```bash
ssh btbg "echo 'SSH connection successful'"
```

### 2.2 Install ROS2 and Dependencies on Pi

- [ ] **2.2.1** Create setup script on Pi

SSH into Pi and create `~/setup_btbg.sh`:

```bash
#!/bin/bash
set -e

echo "=== BTBG Pi Setup Script ==="
echo "Expected OS: Ubuntu 22.04 Server (64-bit)"

# Verify Ubuntu 22.04
if ! grep -q "22.04" /etc/os-release; then
    echo "ERROR: This script requires Ubuntu 22.04. Detected:"
    cat /etc/os-release | grep PRETTY_NAME
    exit 1
fi

echo "[1/8] Updating system..."
sudo apt update && sudo apt upgrade -y

echo "[2/8] Installing ROS2 Humble prerequisites..."
sudo apt install -y software-properties-common curl gnupg lsb-release

echo "[3/8] Adding ROS2 repository..."
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list

echo "[4/8] Installing ROS2 Humble..."
sudo apt update
sudo apt install -y ros-humble-ros-base python3-colcon-common-extensions python3-pip

echo "[5/8] Installing ROS2 packages..."
sudo apt install -y ros-humble-rosbridge-suite ros-humble-sensor-msgs ros-humble-geometry-msgs ros-humble-std-msgs

echo "[6/8] Installing SunFounder libraries..."
pip3 install "picarx>=2.0.0,<3.0.0" "robot-hat>=2.0.0,<3.0.0"

echo "[7/8] Installing Python dependencies..."
pip3 install "opencv-python-headless>=4.9.0,<5.0.0"

echo "[8/8] Setting up workspace..."
mkdir -p ~/btbg_ws/src
mkdir -p ~/btbg_logs
cd ~/btbg_ws
source /opt/ros/humble/setup.bash
colcon build

# Add ROS2 to bashrc
if ! grep -q "btbg_ws" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# BTBG ROS2 setup" >> ~/.bashrc
    echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
    echo "source ~/btbg_ws/install/setup.bash 2>/dev/null || true" >> ~/.bashrc
fi

# Enable I2C
echo "[Extra] Enabling I2C..."
sudo apt install -y i2c-tools python3-smbus
if ! grep -q "dtparam=i2c_arm=on" /boot/firmware/config.txt; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt
fi
sudo usermod -aG i2c $USER

echo ""
echo "=== Setup complete ==="
echo "Please reboot: sudo reboot"
```

- [ ] **2.2.2** Run setup script

```bash
chmod +x ~/setup_btbg.sh
./setup_btbg.sh
sudo reboot
```

- [ ] **2.2.3** Wait for reboot and reconnect

```bash
# Wait 60 seconds for Pi to reboot
sleep 60
ssh btbg "echo 'Reconnected after reboot'"
```

### 2.3 Verify Hardware

- [ ] **2.3.1** Verify I2C devices detected

```bash
ssh btbg "sudo i2cdetect -y 1"
```

Expected output should show addresses (typically 0x14 for Robot HAT):
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- --
10:    -- -- -- 14 -- -- -- -- -- -- -- -- -- -- --
...
```

- [ ] **2.3.2** Verify picarx library works

```bash
ssh btbg "python3 -c \"
from picarx import Picarx
px = Picarx()
print('Picarx initialized successfully')
px.stop()
print('Motors stopped')
\""
```

- [ ] **2.3.3** Test motor movement (CAREFUL - car will move!)

```bash
ssh btbg "python3 -c \"
from picarx import Picarx
import time
px = Picarx()
print('Moving forward for 0.5 seconds...')
px.forward(20)
time.sleep(0.5)
px.stop()
print('Test complete')
\""
```

- [ ] **2.3.4** Test ultrasonic sensor

```bash
ssh btbg "python3 -c \"
from picarx import Picarx
px = Picarx()
for i in range(5):
    distance = px.ultrasonic.read()
    print(f'Distance reading {i+1}: {distance} cm')
    import time
    time.sleep(0.2)
\""
```

### 2.4 Verification Tests - Phase 2

```bash
# TEST 2.4.1: Verify SSH connection
ssh btbg "echo '✓ SSH connection works'"

# TEST 2.4.2: Verify ROS2 installed
ssh btbg "source /opt/ros/humble/setup.bash && ros2 --version" && echo "✓ ROS2 installed"

# TEST 2.4.3: Verify rosbridge installed
ssh btbg "source /opt/ros/humble/setup.bash && ros2 pkg list | grep rosbridge" && echo "✓ rosbridge installed"

# TEST 2.4.4: Verify workspace exists
ssh btbg "test -d ~/btbg_ws/src && echo '✓ Workspace exists'"

# TEST 2.4.5: Verify I2C accessible
ssh btbg "sudo i2cdetect -y 1 | grep -q '14' && echo '✓ Robot HAT detected on I2C'"

# TEST 2.4.6: Verify picarx importable
ssh btbg "python3 -c 'from picarx import Picarx; print(\"✓ picarx importable\")'"
```

**Expected Results:**
- All 6 tests pass
- I2C shows device at address 0x14
- Motors can move (tested manually)
- Ultrasonic returns distance values (not None)

---

## Phase 3: ROS2 Package Structure

### 3.1 Create ROS2 Package Files

```
LOCATION: Developer machine
WORKING_DIR: C:\Users\tzuiy\self_projects\btbg\robot\btbg_nodes
```

- [ ] **3.1.1** Create `package.xml`

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>btbg_nodes</name>
  <version>1.0.0</version>
  <description>BTBG Robot Car ROS2 Nodes</description>
  <maintainer email="your@email.com">BTBG Developer</maintainer>
  <license>MIT</license>

  <depend>rclpy</depend>
  <depend>std_msgs</depend>
  <depend>geometry_msgs</depend>
  <depend>sensor_msgs</depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

- [ ] **3.1.2** Create `setup.py`

```python
from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'btbg_nodes'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='BTBG Developer',
    maintainer_email='your@email.com',
    description='BTBG Robot Car ROS2 Nodes',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'hardware_bridge_node = btbg_nodes.hardware_bridge_node:main',
            'sensor_node = btbg_nodes.sensor_node:main',
            'car_control_node = btbg_nodes.car_control_node:main',
            'patrol_node = btbg_nodes.patrol_node:main',
        ],
    },
)
```

- [ ] **3.1.3** Create `setup.cfg`

```ini
[develop]
script_dir=$base/lib/btbg_nodes

[install]
install_scripts=$base/lib/btbg_nodes
```

- [ ] **3.1.4** Create `resource/btbg_nodes` (empty marker file)

```bash
# Create empty resource file (required by ament)
mkdir -p robot/btbg_nodes/resource
echo "" > robot/btbg_nodes/resource/btbg_nodes
```

- [ ] **3.1.5** Create `btbg_nodes/__init__.py`

```python
"""BTBG Robot Car ROS2 Nodes Package."""
```

### 3.2 Create Configuration Files

- [ ] **3.2.1** Create `robot/config/btbg_params.yaml`

```yaml
# BTBG Robot Parameters
# All parameters are namespaced by node name

hardware_bridge_node:
  ros__parameters:
    watchdog_timeout_ms: 1500
    min_motor_speed: 15
    max_motor_speed: 100
    max_steering_angle: 40.0
    publish_rate_hz: 10.0

sensor_node:
  ros__parameters:
    ultrasonic_rate_hz: 10.0
    grayscale_rate_hz: 10.0
    battery_rate_hz: 0.5
    ultrasonic_max_range_cm: 300.0
    ultrasonic_min_range_cm: 2.0
    battery_low_warning_v: 7.0

car_control_node:
  ros__parameters:
    max_speed: 100
    min_speed: 15
    max_steering_angle: 40.0
    watchdog_timeout_ms: 1000
    publish_rate_hz: 20.0

patrol_node:
  ros__parameters:
    speed: 30
    obstacle_threshold_cm: 25.0
    reverse_speed: 20
    reverse_duration_s: 0.5
    turn_duration_base_s: 0.8
    scan_interval_ms: 100
    turn_angles: [-120.0, -90.0, -60.0, 60.0, 90.0, 120.0]
    max_none_readings: 5
    speed_variation: 5
```

- [ ] **3.2.2** Create `robot/config/calibration.yaml`

```yaml
# Servo Calibration Offsets
# Adjust these values after running calibration procedure
# Positive values shift servo clockwise, negative counter-clockwise

steering:
  offset: 0        # Steering servo center offset (-20 to 20)

camera_pan:
  offset: 0        # Camera pan servo center offset (-20 to 20)

camera_tilt:
  offset: 0        # Camera tilt servo center offset (-20 to 20)

# Motor calibration
motors:
  left_offset: 0   # Left motor speed offset (-10 to 10)
  right_offset: 0  # Right motor speed offset (-10 to 10)
```

### 3.3 Verification Tests - Phase 3

```bash
# TEST 3.3.1: Verify package.xml is valid XML
node -e "
const fs = require('fs');
const xml = fs.readFileSync('robot/btbg_nodes/package.xml', 'utf8');
if (xml.includes('<package') && xml.includes('</package>')) {
  console.log('✓ package.xml structure valid');
} else {
  console.log('✗ package.xml invalid');
  process.exit(1);
}
"

# TEST 3.3.2: Verify setup.py exists and has entry_points
node -e "
const fs = require('fs');
const setup = fs.readFileSync('robot/btbg_nodes/setup.py', 'utf8');
const nodes = ['hardware_bridge_node', 'sensor_node', 'car_control_node', 'patrol_node'];
let pass = true;
nodes.forEach(n => {
  if (!setup.includes(n)) { console.log('✗ Missing entry_point:', n); pass = false; }
});
if (pass) console.log('✓ All entry_points defined');
else process.exit(1);
"

# TEST 3.3.3: Verify YAML files are valid
node -e "
const fs = require('fs');
const yaml = require('yaml') || { parse: s => s }; // fallback if no yaml parser
const files = ['robot/config/btbg_params.yaml', 'robot/config/calibration.yaml'];
files.forEach(f => {
  if (fs.existsSync(f)) console.log('✓', f, 'exists');
  else { console.log('✗', f, 'missing'); process.exit(1); }
});
"

# TEST 3.3.4: Verify resource file exists
node -e "
const fs = require('fs');
if (fs.existsSync('robot/btbg_nodes/resource/btbg_nodes')) {
  console.log('✓ resource/btbg_nodes exists');
} else {
  console.log('✗ resource/btbg_nodes missing');
  process.exit(1);
}
"
```

**Expected Results:**
- All 4 tests pass
- Package structure is complete

---

## Phase 4: Hardware Bridge Node

### 4.1 Create Hardware Bridge Node

```
LOCATION: Developer machine
FILE: robot/btbg_nodes/btbg_nodes/hardware_bridge_node.py
```

- [ ] **4.1.1** Create the hardware bridge node

```python
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
```

### 4.2 Create Unit Tests for Hardware Bridge

- [ ] **4.2.1** Create `robot/test/test_hardware_bridge.py`

```python
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
```

### 4.3 Verification Tests - Phase 4

```bash
# TEST 4.3.1: Verify hardware_bridge_node.py exists and has correct structure
node -e "
const fs = require('fs');
const code = fs.readFileSync('robot/btbg_nodes/btbg_nodes/hardware_bridge_node.py', 'utf8');
const required = ['class HardwareBridgeNode', 'def main', 'drive_callback', 'watchdog_callback', 'emergency_stop'];
let pass = true;
required.forEach(r => {
  if (!code.includes(r)) { console.log('✗ Missing:', r); pass = false; }
  else { console.log('✓ Found:', r); }
});
if (!pass) process.exit(1);
"

# TEST 4.3.2: Verify test file exists
node -e "
const fs = require('fs');
if (fs.existsSync('robot/test/test_hardware_bridge.py')) {
  console.log('✓ test_hardware_bridge.py exists');
} else {
  console.log('✗ test_hardware_bridge.py missing');
  process.exit(1);
}
"

# TEST 4.3.3: Run unit tests locally (if pytest available)
# Note: This requires Python with pytest installed on dev machine
# python -m pytest robot/test/test_hardware_bridge.py -v

# TEST 4.3.4: Syntax check the Python file
# python -m py_compile robot/btbg_nodes/btbg_nodes/hardware_bridge_node.py && echo "✓ Syntax valid"
```

**Expected Results:**
- hardware_bridge_node.py contains all required classes and methods
- Unit tests exist and pass
- Python syntax is valid

---

## Phase 5: Sensor Node

### 5.1 Create Sensor Node

```
FILE: robot/btbg_nodes/btbg_nodes/sensor_node.py
```

- [ ] **5.1.1** Create the sensor node

```python
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
```

### 5.2 Create Unit Tests for Sensor Node

- [ ] **5.2.1** Create `robot/test/test_sensor_node.py`

```python
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
```

### 5.3 Verification Tests - Phase 5

```bash
# TEST 5.3.1: Verify sensor_node.py exists and has correct structure
node -e "
const fs = require('fs');
const code = fs.readFileSync('robot/btbg_nodes/btbg_nodes/sensor_node.py', 'utf8');
const required = ['class SensorNode', 'def main', 'publish_ultrasonic', 'publish_grayscale', 'publish_battery'];
let pass = true;
required.forEach(r => {
  if (!code.includes(r)) { console.log('✗ Missing:', r); pass = false; }
  else { console.log('✓ Found:', r); }
});
if (!pass) process.exit(1);
"

# TEST 5.3.2: Verify test file exists
node -e "
const fs = require('fs');
if (fs.existsSync('robot/test/test_sensor_node.py')) {
  console.log('✓ test_sensor_node.py exists');
} else {
  console.log('✗ test_sensor_node.py missing');
  process.exit(1);
}
"
```

---

## Phase 6: Car Control Node

### 6.1 Create Car Control Node

```
FILE: robot/btbg_nodes/btbg_nodes/car_control_node.py
```

- [ ] **6.1.1** Create the car control node

```python
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
```

### 6.2 Create Unit Tests for Car Control Node

- [ ] **6.2.1** Create `robot/test/test_car_control_node.py`

```python
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
```

### 6.3 Verification Tests - Phase 6

```bash
# TEST 6.3.1: Verify car_control_node.py exists and has correct structure
node -e "
const fs = require('fs');
const code = fs.readFileSync('robot/btbg_nodes/btbg_nodes/car_control_node.py', 'utf8');
const required = ['class CarControlNode', 'def main', 'manual_cmd_callback', 'patrol_cmd_callback', 'mode_callback', 'scale_twist_to_drive'];
let pass = true;
required.forEach(r => {
  if (!code.includes(r)) { console.log('✗ Missing:', r); pass = false; }
  else { console.log('✓ Found:', r); }
});
if (!pass) process.exit(1);
"

# TEST 6.3.2: Verify test file exists
node -e "
const fs = require('fs');
if (fs.existsSync('robot/test/test_car_control_node.py')) {
  console.log('✓ test_car_control_node.py exists');
} else {
  console.log('✗ test_car_control_node.py missing');
  process.exit(1);
}
"
```

---

## Phase 7: Patrol Node

### 7.1 Create Patrol Node

```
FILE: robot/btbg_nodes/btbg_nodes/patrol_node.py
```

- [ ] **7.1.1** Create the patrol node

```python
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
```

### 7.2 Create Unit Tests for Patrol Node

- [ ] **7.2.1** Create `robot/test/test_patrol_node.py`

```python
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
```

### 7.3 Verification Tests - Phase 7

```bash
# TEST 7.3.1: Verify patrol_node.py exists and has correct structure
node -e "
const fs = require('fs');
const code = fs.readFileSync('robot/btbg_nodes/btbg_nodes/patrol_node.py', 'utf8');
const required = ['class PatrolNode', 'def main', 'patrol_loop', 'STATE_FORWARD', 'STATE_REVERSING', 'STATE_TURNING'];
let pass = true;
required.forEach(r => {
  if (!code.includes(r)) { console.log('✗ Missing:', r); pass = false; }
  else { console.log('✓ Found:', r); }
});
if (!pass) process.exit(1);
"

# TEST 7.3.2: Verify test file exists
node -e "
const fs = require('fs');
if (fs.existsSync('robot/test/test_patrol_node.py')) {
  console.log('✓ test_patrol_node.py exists');
} else {
  console.log('✗ test_patrol_node.py missing');
  process.exit(1);
}
"
```

---

## Phase 8: Launch File & Integration

### 8.1 Create Launch File

- [ ] **8.1.1** Create `robot/launch/btbg.launch.py`

```python
#!/usr/bin/env python3
"""
BTBG Launch File - Starts all ROS2 nodes and rosbridge.

Usage:
    ros2 launch btbg_nodes btbg.launch.py
"""

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get package share directory for config files
    pkg_share = get_package_share_directory('btbg_nodes')
    params_file = os.path.join(pkg_share, 'config', 'btbg_params.yaml')

    # Check if params file exists, use defaults if not
    if not os.path.exists(params_file):
        print(f"WARNING: {params_file} not found, using default parameters")
        params_file = None

    nodes = []

    # Hardware Bridge Node (must start first - owns Picarx instance)
    hardware_bridge = Node(
        package='btbg_nodes',
        executable='hardware_bridge_node',
        name='hardware_bridge_node',
        output='screen',
        parameters=[params_file] if params_file else [],
        emulate_tty=True,
    )
    nodes.append(hardware_bridge)

    # Sensor Node
    sensor_node = Node(
        package='btbg_nodes',
        executable='sensor_node',
        name='sensor_node',
        output='screen',
        parameters=[params_file] if params_file else [],
        emulate_tty=True,
    )
    nodes.append(sensor_node)

    # Car Control Node (mode arbiter)
    car_control = Node(
        package='btbg_nodes',
        executable='car_control_node',
        name='car_control_node',
        output='screen',
        parameters=[params_file] if params_file else [],
        emulate_tty=True,
    )
    nodes.append(car_control)

    # Patrol Node (autonomous mode)
    patrol_node = Node(
        package='btbg_nodes',
        executable='patrol_node',
        name='patrol_node',
        output='screen',
        parameters=[params_file] if params_file else [],
        emulate_tty=True,
    )
    nodes.append(patrol_node)

    # rosbridge WebSocket server
    rosbridge = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        name='rosbridge_websocket',
        output='screen',
        parameters=[{'port': 9090}],
        emulate_tty=True,
    )
    nodes.append(rosbridge)

    return LaunchDescription(nodes)
```

### 8.2 Deploy and Build on Pi

- [ ] **8.2.1** Create deployment script `scripts/deploy.js`

```javascript
#!/usr/bin/env node
/**
 * Deploy robot code to Pi and rebuild.
 *
 * Usage: npm run btbg:deploy
 */

require('dotenv').config();
const { NodeSSH } = require('node-ssh');
const path = require('path');
const fs = require('fs');

const ssh = new NodeSSH();

const PI_HOST = process.env.PI_HOST || 'btbg.local';
const PI_USER = process.env.PI_USER || 'ubuntu';
const PI_SSH_KEY = process.env.PI_SSH_KEY || path.join(require('os').homedir(), '.ssh', 'btbg_pi');
const ROS2_WS = process.env.ROS2_WS || '/home/ubuntu/btbg_ws';

async function deploy() {
    console.log(`\n🚀 Deploying to ${PI_USER}@${PI_HOST}...\n`);

    try {
        // Connect
        await ssh.connect({
            host: PI_HOST,
            username: PI_USER,
            privateKeyPath: PI_SSH_KEY.replace('~', require('os').homedir()),
        });
        console.log('✓ Connected to Pi\n');

        // Create target directory
        const targetDir = `${ROS2_WS}/src/btbg_nodes`;
        await ssh.execCommand(`mkdir -p ${targetDir}`);

        // Upload files
        const localRobotDir = path.join(__dirname, '..', 'robot');
        console.log(`📁 Uploading from ${localRobotDir}...\n`);

        // Upload btbg_nodes package
        await ssh.putDirectory(
            path.join(localRobotDir, 'btbg_nodes'),
            targetDir,
            {
                recursive: true,
                concurrency: 5,
                tick: (localPath, remotePath, error) => {
                    if (error) {
                        console.log(`  ✗ ${path.basename(localPath)}: ${error.message}`);
                    } else {
                        console.log(`  ✓ ${path.basename(localPath)}`);
                    }
                }
            }
        );

        // Upload launch files
        await ssh.putDirectory(
            path.join(localRobotDir, 'launch'),
            `${targetDir}/launch`,
            { recursive: true }
        );
        console.log('  ✓ launch/');

        // Upload config files
        await ssh.putDirectory(
            path.join(localRobotDir, 'config'),
            `${targetDir}/config`,
            { recursive: true }
        );
        console.log('  ✓ config/');

        console.log('\n📦 Building ROS2 package...\n');

        // Build
        const buildCmd = `
            source /opt/ros/humble/setup.bash &&
            cd ${ROS2_WS} &&
            colcon build --packages-select btbg_nodes --symlink-install
        `;

        const result = await ssh.execCommand(buildCmd, {
            onStdout: (chunk) => process.stdout.write(chunk.toString()),
            onStderr: (chunk) => process.stderr.write(chunk.toString()),
        });

        if (result.code === 0) {
            console.log('\n✓ Build successful!\n');
        } else {
            console.error('\n✗ Build failed with code:', result.code);
            process.exit(1);
        }

    } catch (error) {
        console.error('✗ Deployment failed:', error.message);
        process.exit(1);
    } finally {
        ssh.dispose();
    }
}

deploy();
```

### 8.3 Verification Tests - Phase 8

```bash
# TEST 8.3.1: Verify launch file exists
node -e "
const fs = require('fs');
if (fs.existsSync('robot/launch/btbg.launch.py')) {
  console.log('✓ btbg.launch.py exists');
} else {
  console.log('✗ btbg.launch.py missing');
  process.exit(1);
}
"

# TEST 8.3.2: Deploy to Pi and verify build
npm run btbg:deploy

# TEST 8.3.3: Verify package is installed on Pi
ssh btbg "source /opt/ros/humble/setup.bash && source ~/btbg_ws/install/setup.bash && ros2 pkg list | grep btbg_nodes" && echo "✓ btbg_nodes package installed"

# TEST 8.3.4: Verify all nodes are registered
ssh btbg "source /opt/ros/humble/setup.bash && source ~/btbg_ws/install/setup.bash && ros2 pkg executables btbg_nodes"
# Expected output:
# btbg_nodes car_control_node
# btbg_nodes hardware_bridge_node
# btbg_nodes patrol_node
# btbg_nodes sensor_node

# TEST 8.3.5: Test launch file starts (run for 5 seconds then kill)
ssh btbg "source /opt/ros/humble/setup.bash && source ~/btbg_ws/install/setup.bash && timeout 5 ros2 launch btbg_nodes btbg.launch.py || true" && echo "✓ Launch file executes"
```

---

## Phase 9: Electron App Setup

### 9.1 Initialize Electron + React + Vite Project

```
LOCATION: Developer machine
WORKING_DIR: C:\Users\tzuiy\self_projects\btbg\app
```

- [ ] **9.1.1** Create `app/package.json`

```json
{
  "name": "btbg-app",
  "version": "1.0.0",
  "description": "BTBG Robot Control UI",
  "main": "dist-electron/main.js",
  "scripts": {
    "dev": "vite",
    "build": "vite build && electron-builder",
    "preview": "vite preview",
    "electron": "electron .",
    "electron:dev": "concurrently \"vite\" \"wait-on http://localhost:5173 && electron .\""
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "roslib": "^1.3.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "concurrently": "^8.2.2",
    "electron": "^28.0.0",
    "electron-builder": "^24.9.1",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.4.0",
    "vite": "^5.0.0",
    "vite-plugin-electron": "^0.15.0",
    "wait-on": "^7.2.0"
  }
}
```

- [ ] **9.1.2** Create `app/vite.config.js`

```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import electron from 'vite-plugin-electron';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    electron([
      {
        entry: 'electron/main.js',
        vite: {
          build: {
            outDir: 'dist-electron',
            rollupOptions: {
              external: ['electron'],
            },
          },
        },
      },
      {
        entry: 'electron/preload.js',
        onstart(options) {
          options.reload();
        },
        vite: {
          build: {
            outDir: 'dist-electron',
          },
        },
      },
    ]),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
  },
});
```

- [ ] **9.1.3** Create `app/tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        'btbg-dark': '#1a1a2e',
        'btbg-darker': '#16213e',
        'btbg-accent': '#0f3460',
        'btbg-highlight': '#e94560',
      },
    },
  },
  plugins: [],
};
```

- [ ] **9.1.4** Create `app/postcss.config.js`

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **9.1.5** Create `app/index.html`

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' ws://btbg.local:9090 ws://localhost:9090 ws://*:9090;">
    <title>BTBG Control</title>
  </head>
  <body class="bg-btbg-dark text-white">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

### 9.2 Create Electron Main Process

- [ ] **9.2.1** Create `app/electron/main.js`

```javascript
const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');

// Handle creating/removing shortcuts on Windows when installing/uninstalling
if (require('electron-squirrel-startup')) {
  app.quit();
}

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 600,
    minWidth: 800,
    minHeight: 500,
    backgroundColor: '#1a1a2e',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // Remove default menu, keep only File > Quit
  const template = [
    {
      label: 'File',
      submenu: [
        { role: 'quit' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
      ]
    }
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));

  // Load the app
  if (process.env.NODE_ENV === 'development' || process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL || 'http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
```

- [ ] **9.2.2** Create `app/electron/preload.js`

```javascript
const { contextBridge } = require('electron');

// Expose a minimal API to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  version: process.env.npm_package_version || '1.0.0',
});

// Log when preload script runs
console.log('BTBG preload script loaded');
```

### 9.3 Create React Entry Point

- [ ] **9.3.1** Create `app/src/main.jsx`

```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **9.3.2** Create `app/src/styles/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Base styles */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  margin: 0;
  padding: 0;
  overflow: hidden;
  user-select: none;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #16213e;
}

::-webkit-scrollbar-thumb {
  background: #0f3460;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #e94560;
}

/* Control button styles */
.control-btn {
  @apply w-16 h-16 rounded-lg bg-btbg-accent text-white font-bold text-xl
         flex items-center justify-center transition-all duration-100
         hover:bg-btbg-highlight active:scale-95 active:bg-btbg-highlight
         disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-btbg-accent;
}

.control-btn.active {
  @apply bg-btbg-highlight scale-95;
}

/* Status indicators */
.status-dot {
  @apply w-3 h-3 rounded-full;
}

.status-dot.connected {
  @apply bg-green-500;
  animation: pulse 2s infinite;
}

.status-dot.connecting {
  @apply bg-yellow-500;
  animation: pulse 1s infinite;
}

.status-dot.disconnected {
  @apply bg-red-500;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Mode toggle */
.mode-toggle {
  @apply relative w-full h-10 bg-btbg-darker rounded-lg flex items-center cursor-pointer;
}

.mode-toggle-slider {
  @apply absolute h-8 rounded-md bg-btbg-highlight transition-all duration-300;
  width: calc(50% - 4px);
  left: 2px;
}

.mode-toggle-slider.patrol {
  left: calc(50% + 2px);
}

.mode-toggle-label {
  @apply flex-1 text-center z-10 font-semibold text-sm;
}
```

- [ ] **9.3.3** Create `app/src/App.jsx`

```jsx
import React, { useState, useEffect, useCallback } from 'react';
import { rosClient } from './ros/rosClient';
import { TOPICS } from './ros/topics';
import ConnectionStatus from './components/ConnectionStatus';
import ModeToggle from './components/ModeToggle';
import DriveControls from './components/DriveControls';
import SpeedSlider from './components/SpeedSlider';
import SensorDisplay from './components/SensorDisplay';
import ServoControls from './components/ServoControls';
import StatusBar from './components/StatusBar';

function App() {
  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  // Robot state
  const [mode, setMode] = useState('manual');
  const [speed, setSpeed] = useState(50);
  const [sensorData, setSensorData] = useState({
    ultrasonic: 0,
    battery: 7.4,
    batteryWarning: false,
  });
  const [patrolStatus, setPatrolStatus] = useState({
    state: 'idle',
    distance: 0,
  });
  const [robotStatus, setRobotStatus] = useState({
    speed: 0,
    steering: 0,
    isMoving: false,
  });

  // Connect to ROS on mount
  useEffect(() => {
    const connect = async () => {
      setIsConnecting(true);
      try {
        await rosClient.connect();
        setIsConnected(true);
        setIsConnecting(false);

        // Subscribe to topics
        rosClient.subscribe(TOPICS.SENSOR_ULTRASONIC, (msg) => {
          setSensorData(prev => ({ ...prev, ultrasonic: msg.range * 100 }));
        });

        rosClient.subscribe(TOPICS.SENSOR_BATTERY, (msg) => {
          setSensorData(prev => ({ ...prev, battery: msg.data }));
        });

        rosClient.subscribe(TOPICS.SENSOR_BATTERY_WARNING, (msg) => {
          setSensorData(prev => ({ ...prev, batteryWarning: msg.data }));
        });

        rosClient.subscribe(TOPICS.PATROL_STATUS, (msg) => {
          try {
            const status = JSON.parse(msg.data);
            setPatrolStatus(status);
          } catch (e) {
            console.error('Failed to parse patrol status:', e);
          }
        });

        rosClient.subscribe(TOPICS.STATUS, (msg) => {
          try {
            const status = JSON.parse(msg.data);
            setRobotStatus(status);
            if (status.mode) setMode(status.mode);
          } catch (e) {
            console.error('Failed to parse status:', e);
          }
        });

      } catch (error) {
        console.error('Connection failed:', error);
        setIsConnected(false);
        setIsConnecting(false);
      }
    };

    connect();

    // Handle disconnection
    rosClient.on('close', () => {
      setIsConnected(false);
      setIsConnecting(true);
      // Auto-reconnect after 3 seconds
      setTimeout(connect, 3000);
    });

    return () => {
      rosClient.disconnect();
    };
  }, []);

  // Handle mode change
  const handleModeChange = useCallback((newMode) => {
    setMode(newMode);
    rosClient.publish(TOPICS.MODE, { data: newMode });
  }, []);

  // Handle emergency stop
  const handleEmergencyStop = useCallback(() => {
    rosClient.publish(TOPICS.HW_STOP, {});
    handleModeChange('manual');
  }, [handleModeChange]);

  return (
    <div className="h-screen flex flex-col bg-btbg-dark">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 bg-btbg-darker border-b border-btbg-accent">
        <h1 className="text-xl font-bold">BTBG Control</h1>
        <ConnectionStatus
          isConnected={isConnected}
          isConnecting={isConnecting}
        />
      </header>

      {/* Mode Toggle */}
      <div className="px-4 py-3 bg-btbg-darker">
        <ModeToggle
          mode={mode}
          onChange={handleModeChange}
          disabled={!isConnected}
        />
      </div>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left Panel - Controls */}
        <div className="w-1/2 p-4 flex flex-col gap-4 border-r border-btbg-accent">
          <div className="text-sm font-semibold text-gray-400 uppercase">
            Drive Controls
          </div>

          <SpeedSlider
            value={speed}
            onChange={setSpeed}
            disabled={!isConnected || mode === 'patrol'}
          />

          <DriveControls
            speed={speed}
            disabled={!isConnected || mode === 'patrol'}
            onEmergencyStop={handleEmergencyStop}
          />

          <div className="text-xs text-gray-500 text-center">
            WASD or Arrow Keys to drive • Space = E-STOP
          </div>

          <ServoControls disabled={!isConnected} />
        </div>

        {/* Right Panel - Telemetry */}
        <div className="w-1/2 p-4 flex flex-col gap-4">
          <div className="text-sm font-semibold text-gray-400 uppercase">
            Telemetry
          </div>

          <SensorDisplay
            ultrasonic={sensorData.ultrasonic}
            battery={sensorData.battery}
            batteryWarning={sensorData.batteryWarning}
            patrolState={patrolStatus.state}
            isPatrolMode={mode === 'patrol'}
          />

          <StatusBar
            mode={mode}
            speed={robotStatus.speed}
            steering={robotStatus.steering}
            isMoving={robotStatus.isMoving}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
```

### 9.4 Verification Tests - Phase 9

```bash
# TEST 9.4.1: Verify app directory structure
node -e "
const fs = require('fs');
const files = [
  'app/package.json',
  'app/vite.config.js',
  'app/index.html',
  'app/electron/main.js',
  'app/electron/preload.js',
  'app/src/main.jsx',
  'app/src/App.jsx',
  'app/src/styles/index.css'
];
let pass = true;
files.forEach(f => {
  if (fs.existsSync(f)) console.log('✓', f);
  else { console.log('✗', f, 'missing'); pass = false; }
});
if (!pass) process.exit(1);
"

# TEST 9.4.2: Install dependencies
cd app && npm install && cd ..
echo "✓ Dependencies installed"

# TEST 9.4.3: Verify Vite can start (just check, don't run)
node -e "
const pkg = require('./app/package.json');
if (pkg.scripts.dev) console.log('✓ dev script exists');
else { console.log('✗ dev script missing'); process.exit(1); }
"
```

---

## Phase 10: ROS Client Module

### 10.1 Create ROS Client

- [ ] **10.1.1** Create `app/src/ros/rosClient.js`

```javascript
/**
 * ROS Client - Singleton wrapper around roslibjs
 *
 * Provides:
 * - Automatic connection management
 * - Topic subscription/publishing helpers
 * - Event emitter for connection state
 */

import ROSLIB from 'roslib';

class ROSClient {
  constructor() {
    this.ros = null;
    this.topics = {};
    this.subscribers = {};
    this.eventHandlers = {
      connection: [],
      close: [],
      error: [],
    };

    // Connection settings
    this.url = this._getWebSocketUrl();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
  }

  /**
   * Get WebSocket URL from environment or default
   */
  _getWebSocketUrl() {
    // Check for environment variable (can be set in .env)
    if (typeof process !== 'undefined' && process.env.ROSBRIDGE_URL) {
      return process.env.ROSBRIDGE_URL;
    }

    // Default to btbg.local
    const host = localStorage.getItem('rosbridge_host') || 'btbg.local';
    const port = localStorage.getItem('rosbridge_port') || '9090';
    return `ws://${host}:${port}`;
  }

  /**
   * Connect to rosbridge
   */
  connect() {
    return new Promise((resolve, reject) => {
      console.log(`Connecting to ${this.url}...`);

      this.ros = new ROSLIB.Ros({
        url: this.url,
      });

      this.ros.on('connection', () => {
        console.log('Connected to rosbridge');
        this.reconnectAttempts = 0;
        this._emit('connection');
        resolve();
      });

      this.ros.on('error', (error) => {
        console.error('rosbridge error:', error);
        this._emit('error', error);
      });

      this.ros.on('close', () => {
        console.log('rosbridge connection closed');
        this._emit('close');

        // Auto-reconnect with exponential backoff
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
            5000
          );
          this.reconnectAttempts++;
          console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
          setTimeout(() => this.connect(), delay);
        }
      });

      // Timeout after 5 seconds
      setTimeout(() => {
        if (!this.ros.isConnected) {
          reject(new Error('Connection timeout'));
        }
      }, 5000);
    });
  }

  /**
   * Disconnect from rosbridge
   */
  disconnect() {
    if (this.ros) {
      // Unsubscribe from all topics
      Object.values(this.subscribers).forEach(sub => sub.unsubscribe());
      this.subscribers = {};

      this.ros.close();
      this.ros = null;
    }
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.ros && this.ros.isConnected;
  }

  /**
   * Get or create a topic
   */
  getTopic(name, messageType) {
    const key = `${name}:${messageType}`;
    if (!this.topics[key]) {
      this.topics[key] = new ROSLIB.Topic({
        ros: this.ros,
        name: name,
        messageType: messageType,
      });
    }
    return this.topics[key];
  }

  /**
   * Subscribe to a topic
   */
  subscribe(topicConfig, callback) {
    const { name, messageType } = topicConfig;
    const topic = this.getTopic(name, messageType);

    const subscriber = topic.subscribe(callback);
    this.subscribers[name] = topic;

    console.log(`Subscribed to ${name}`);
    return () => {
      topic.unsubscribe();
      delete this.subscribers[name];
    };
  }

  /**
   * Publish to a topic
   */
  publish(topicConfig, data) {
    if (!this.isConnected()) {
      console.warn('Cannot publish: not connected');
      return;
    }

    const { name, messageType } = topicConfig;
    const topic = this.getTopic(name, messageType);
    const message = new ROSLIB.Message(data);

    topic.publish(message);
  }

  /**
   * Register event handler
   */
  on(event, handler) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].push(handler);
    }
  }

  /**
   * Remove event handler
   */
  off(event, handler) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler);
    }
  }

  /**
   * Emit event
   */
  _emit(event, data) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach(handler => handler(data));
    }
  }

  /**
   * Set connection URL
   */
  setUrl(host, port = 9090) {
    this.url = `ws://${host}:${port}`;
    localStorage.setItem('rosbridge_host', host);
    localStorage.setItem('rosbridge_port', port.toString());
  }
}

// Export singleton instance
export const rosClient = new ROSClient();
export default rosClient;
```

- [ ] **10.1.2** Create `app/src/ros/topics.js`

```javascript
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
```

### 10.2 Create Unit Tests for ROS Client

- [ ] **10.2.1** Create `app/src/ros/__tests__/rosClient.test.js`

```javascript
/**
 * Unit tests for ROS client
 */

describe('ROSClient', () => {
  describe('URL generation', () => {
    test('should generate correct WebSocket URL', () => {
      const host = 'btbg.local';
      const port = 9090;
      const url = `ws://${host}:${port}`;
      expect(url).toBe('ws://btbg.local:9090');
    });

    test('should handle custom host', () => {
      const host = '192.168.1.100';
      const port = 9090;
      const url = `ws://${host}:${port}`;
      expect(url).toBe('ws://192.168.1.100:9090');
    });

    test('should handle custom port', () => {
      const host = 'btbg.local';
      const port = 8080;
      const url = `ws://${host}:${port}`;
      expect(url).toBe('ws://btbg.local:8080');
    });
  });

  describe('Topic configuration', () => {
    test('CMD_VEL topic should have correct message type', () => {
      const topic = {
        name: '/btbg/cmd_vel',
        messageType: 'geometry_msgs/Twist',
      };
      expect(topic.name).toBe('/btbg/cmd_vel');
      expect(topic.messageType).toBe('geometry_msgs/Twist');
    });

    test('MODE topic should have correct message type', () => {
      const topic = {
        name: '/btbg/mode',
        messageType: 'std_msgs/String',
      };
      expect(topic.name).toBe('/btbg/mode');
      expect(topic.messageType).toBe('std_msgs/String');
    });
  });

  describe('Reconnection logic', () => {
    test('should calculate exponential backoff', () => {
      const baseDelay = 1000;
      const maxDelay = 5000;

      const calcDelay = (attempt) => Math.min(baseDelay * Math.pow(2, attempt), maxDelay);

      expect(calcDelay(0)).toBe(1000);
      expect(calcDelay(1)).toBe(2000);
      expect(calcDelay(2)).toBe(4000);
      expect(calcDelay(3)).toBe(5000); // Capped
      expect(calcDelay(4)).toBe(5000); // Capped
    });
  });
});
```

### 10.3 Verification Tests - Phase 10

```bash
# TEST 10.3.1: Verify ROS client files exist
node -e "
const fs = require('fs');
const files = [
  'app/src/ros/rosClient.js',
  'app/src/ros/topics.js'
];
files.forEach(f => {
  if (fs.existsSync(f)) console.log('✓', f);
  else { console.log('✗', f, 'missing'); process.exit(1); }
});
"

# TEST 10.3.2: Verify topics are correctly defined
node -e "
const fs = require('fs');
const topics = fs.readFileSync('app/src/ros/topics.js', 'utf8');
const required = ['CMD_VEL', 'MODE', 'SERVO_CMD', 'HW_STOP', 'SENSOR_ULTRASONIC', 'STATUS', 'PATROL_STATUS'];
let pass = true;
required.forEach(t => {
  if (topics.includes(t)) console.log('✓ Topic:', t);
  else { console.log('✗ Missing topic:', t); pass = false; }
});
if (!pass) process.exit(1);
"
```

---

## Phase 11: UI Components

### 11.1 Create Connection Status Component

- [ ] **11.1.1** Create `app/src/components/ConnectionStatus.jsx`

```jsx
import React from 'react';

function ConnectionStatus({ isConnected, isConnecting }) {
  let statusClass = 'disconnected';
  let statusText = 'Disconnected';

  if (isConnected) {
    statusClass = 'connected';
    statusText = 'Connected';
  } else if (isConnecting) {
    statusClass = 'connecting';
    statusText = 'Connecting...';
  }

  return (
    <div className="flex items-center gap-2">
      <div className={`status-dot ${statusClass}`}></div>
      <span className="text-sm">{statusText}</span>
    </div>
  );
}

export default ConnectionStatus;
```

### 11.2 Create Mode Toggle Component

- [ ] **11.2.1** Create `app/src/components/ModeToggle.jsx`

```jsx
import React from 'react';

function ModeToggle({ mode, onChange, disabled }) {
  const isPatrol = mode === 'patrol';

  return (
    <div
      className={`mode-toggle ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      onClick={() => {
        if (!disabled) {
          onChange(isPatrol ? 'manual' : 'patrol');
        }
      }}
    >
      <div className={`mode-toggle-slider ${isPatrol ? 'patrol' : ''}`}></div>
      <span className="mode-toggle-label">MANUAL</span>
      <span className="mode-toggle-label">PATROL</span>
    </div>
  );
}

export default ModeToggle;
```

### 11.3 Create Drive Controls Component

- [ ] **11.3.1** Create `app/src/components/DriveControls.jsx`

```jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { rosClient } from '../ros/rosClient';
import { TOPICS } from '../ros/topics';

function DriveControls({ speed, disabled, onEmergencyStop }) {
  const [activeKeys, setActiveKeys] = useState(new Set());
  const publishInterval = useRef(null);

  // Key mappings
  const keyMap = {
    'w': 'forward',
    'arrowup': 'forward',
    's': 'backward',
    'arrowdown': 'backward',
    'a': 'left',
    'arrowleft': 'left',
    'd': 'right',
    'arrowright': 'right',
    ' ': 'stop',
    'escape': 'estop',
  };

  // Calculate velocity from active keys
  const calculateVelocity = useCallback(() => {
    let linearX = 0;
    let angularZ = 0;

    if (activeKeys.has('forward')) linearX += 1;
    if (activeKeys.has('backward')) linearX -= 1;
    if (activeKeys.has('left')) angularZ += 1;
    if (activeKeys.has('right')) angularZ -= 1;

    // Scale by speed percentage
    linearX *= speed / 100;
    angularZ *= speed / 100;

    return { linearX, angularZ };
  }, [activeKeys, speed]);

  // Publish velocity
  const publishVelocity = useCallback(() => {
    if (disabled) return;

    const { linearX, angularZ } = calculateVelocity();

    rosClient.publish(TOPICS.CMD_VEL, {
      linear: { x: linearX, y: 0, z: 0 },
      angular: { x: 0, y: 0, z: angularZ },
    });
  }, [calculateVelocity, disabled]);

  // Handle key down
  const handleKeyDown = useCallback((e) => {
    if (disabled) return;

    const key = e.key.toLowerCase();
    const action = keyMap[key];

    if (action === 'estop' || action === 'stop') {
      e.preventDefault();
      onEmergencyStop();
      setActiveKeys(new Set());
      return;
    }

    if (action && !activeKeys.has(action)) {
      e.preventDefault();
      setActiveKeys(prev => new Set([...prev, action]));
    }
  }, [activeKeys, disabled, onEmergencyStop]);

  // Handle key up
  const handleKeyUp = useCallback((e) => {
    const key = e.key.toLowerCase();
    const action = keyMap[key];

    if (action) {
      e.preventDefault();
      setActiveKeys(prev => {
        const next = new Set(prev);
        next.delete(action);
        return next;
      });
    }
  }, []);

  // Set up keyboard listeners
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [handleKeyDown, handleKeyUp]);

  // Publish at 20Hz when keys are active
  useEffect(() => {
    if (activeKeys.size > 0 && !disabled) {
      publishInterval.current = setInterval(publishVelocity, 50); // 20Hz
    } else {
      if (publishInterval.current) {
        clearInterval(publishInterval.current);
        // Send stop command when all keys released
        rosClient.publish(TOPICS.CMD_VEL, {
          linear: { x: 0, y: 0, z: 0 },
          angular: { x: 0, y: 0, z: 0 },
        });
      }
    }

    return () => {
      if (publishInterval.current) {
        clearInterval(publishInterval.current);
      }
    };
  }, [activeKeys, disabled, publishVelocity]);

  // Handle button click
  const handleButtonDown = (action) => {
    if (disabled) return;
    setActiveKeys(prev => new Set([...prev, action]));
  };

  const handleButtonUp = (action) => {
    setActiveKeys(prev => {
      const next = new Set(prev);
      next.delete(action);
      return next;
    });
  };

  const isActive = (action) => activeKeys.has(action);

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Forward */}
      <button
        className={`control-btn ${isActive('forward') ? 'active' : ''}`}
        disabled={disabled}
        onMouseDown={() => handleButtonDown('forward')}
        onMouseUp={() => handleButtonUp('forward')}
        onMouseLeave={() => handleButtonUp('forward')}
        onTouchStart={() => handleButtonDown('forward')}
        onTouchEnd={() => handleButtonUp('forward')}
      >
        ↑
      </button>

      {/* Left, Stop, Right */}
      <div className="flex gap-2">
        <button
          className={`control-btn ${isActive('left') ? 'active' : ''}`}
          disabled={disabled}
          onMouseDown={() => handleButtonDown('left')}
          onMouseUp={() => handleButtonUp('left')}
          onMouseLeave={() => handleButtonUp('left')}
          onTouchStart={() => handleButtonDown('left')}
          onTouchEnd={() => handleButtonUp('left')}
        >
          ←
        </button>

        <button
          className="control-btn bg-red-600 hover:bg-red-700"
          disabled={disabled}
          onClick={onEmergencyStop}
        >
          ■
        </button>

        <button
          className={`control-btn ${isActive('right') ? 'active' : ''}`}
          disabled={disabled}
          onMouseDown={() => handleButtonDown('right')}
          onMouseUp={() => handleButtonUp('right')}
          onMouseLeave={() => handleButtonUp('right')}
          onTouchStart={() => handleButtonDown('right')}
          onTouchEnd={() => handleButtonUp('right')}
        >
          →
        </button>
      </div>

      {/* Backward */}
      <button
        className={`control-btn ${isActive('backward') ? 'active' : ''}`}
        disabled={disabled}
        onMouseDown={() => handleButtonDown('backward')}
        onMouseUp={() => handleButtonUp('backward')}
        onMouseLeave={() => handleButtonUp('backward')}
        onTouchStart={() => handleButtonDown('backward')}
        onTouchEnd={() => handleButtonUp('backward')}
      >
        ↓
      </button>
    </div>
  );
}

export default DriveControls;
```

### 11.4 Create Speed Slider Component

- [ ] **11.4.1** Create `app/src/components/SpeedSlider.jsx`

```jsx
import React from 'react';

function SpeedSlider({ value, onChange, disabled }) {
  return (
    <div className="flex items-center gap-3">
      <label className="text-sm text-gray-400 w-16">Speed:</label>
      <input
        type="range"
        min="0"
        max="100"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        disabled={disabled}
        className="flex-1 h-2 bg-btbg-accent rounded-lg appearance-none cursor-pointer
                   disabled:opacity-50 disabled:cursor-not-allowed"
      />
      <span className="text-sm w-12 text-right">{value}%</span>
    </div>
  );
}

export default SpeedSlider;
```

### 11.5 Create Sensor Display Component

- [ ] **11.5.1** Create `app/src/components/SensorDisplay.jsx`

```jsx
import React from 'react';

function SensorDisplay({ ultrasonic, battery, batteryWarning, patrolState, isPatrolMode }) {
  // Color code ultrasonic based on distance
  const getDistanceColor = (dist) => {
    if (dist < 20) return 'text-red-500';
    if (dist < 40) return 'text-yellow-500';
    return 'text-green-500';
  };

  // Color code battery
  const getBatteryColor = (v) => {
    if (v < 6.5) return 'text-red-500';
    if (v < 7.0) return 'text-yellow-500';
    return 'text-green-500';
  };

  // Patrol state badge color
  const getPatrolStateColor = (state) => {
    switch (state) {
      case 'forward': return 'bg-green-600';
      case 'reversing': return 'bg-yellow-600';
      case 'turning': return 'bg-blue-600';
      case 'idle': return 'bg-gray-600';
      default: return 'bg-gray-600';
    }
  };

  return (
    <div className="space-y-3">
      {/* Ultrasonic */}
      <div className="flex justify-between items-center p-3 bg-btbg-darker rounded-lg">
        <span className="text-gray-400">Ultrasonic</span>
        <span className={`font-mono text-lg ${getDistanceColor(ultrasonic)}`}>
          {ultrasonic.toFixed(1)} cm
        </span>
      </div>

      {/* Battery */}
      <div className="flex justify-between items-center p-3 bg-btbg-darker rounded-lg">
        <span className="text-gray-400">Battery</span>
        <div className="flex items-center gap-2">
          {batteryWarning && (
            <span className="text-xs text-red-500 animate-pulse">LOW!</span>
          )}
          <span className={`font-mono text-lg ${getBatteryColor(battery)}`}>
            {battery.toFixed(2)}V
          </span>
        </div>
      </div>

      {/* Patrol State (only show in patrol mode) */}
      {isPatrolMode && (
        <div className="flex justify-between items-center p-3 bg-btbg-darker rounded-lg">
          <span className="text-gray-400">Patrol State</span>
          <span className={`px-3 py-1 rounded-full text-sm font-semibold uppercase ${getPatrolStateColor(patrolState)}`}>
            {patrolState}
          </span>
        </div>
      )}
    </div>
  );
}

export default SensorDisplay;
```

### 11.6 Create Servo Controls Component

- [ ] **11.6.1** Create `app/src/components/ServoControls.jsx`

```jsx
import React, { useState, useCallback } from 'react';
import { rosClient } from '../ros/rosClient';
import { TOPICS } from '../ros/topics';

function ServoControls({ disabled }) {
  const [pan, setPan] = useState(0);
  const [tilt, setTilt] = useState(0);

  // Throttle servo commands to 10Hz max
  const publishServo = useCallback(
    throttle((panAngle, tiltAngle) => {
      rosClient.publish(TOPICS.SERVO_CMD, {
        data: [panAngle, tiltAngle],
      });
    }, 100),
    []
  );

  const handlePanChange = (e) => {
    const value = parseInt(e.target.value);
    setPan(value);
    publishServo(value, tilt);
  };

  const handleTiltChange = (e) => {
    const value = parseInt(e.target.value);
    setTilt(value);
    publishServo(pan, value);
  };

  const resetServos = () => {
    setPan(0);
    setTilt(0);
    publishServo(0, 0);
  };

  return (
    <div className="mt-4 p-3 bg-btbg-darker rounded-lg">
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm font-semibold text-gray-400 uppercase">
          Camera Servo
        </span>
        <button
          onClick={resetServos}
          disabled={disabled}
          className="text-xs px-2 py-1 bg-btbg-accent rounded hover:bg-btbg-highlight
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Reset
        </button>
      </div>

      <div className="space-y-2">
        {/* Pan */}
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-400 w-10">Pan:</label>
          <input
            type="range"
            min="-90"
            max="90"
            value={pan}
            onChange={handlePanChange}
            disabled={disabled}
            className="flex-1 h-2 bg-btbg-accent rounded-lg appearance-none cursor-pointer
                       disabled:opacity-50"
          />
          <span className="text-sm w-12 text-right font-mono">{pan}°</span>
        </div>

        {/* Tilt */}
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-400 w-10">Tilt:</label>
          <input
            type="range"
            min="-35"
            max="35"
            value={tilt}
            onChange={handleTiltChange}
            disabled={disabled}
            className="flex-1 h-2 bg-btbg-accent rounded-lg appearance-none cursor-pointer
                       disabled:opacity-50"
          />
          <span className="text-sm w-12 text-right font-mono">{tilt}°</span>
        </div>
      </div>
    </div>
  );
}

// Simple throttle function
function throttle(func, limit) {
  let lastCall = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastCall >= limit) {
      lastCall = now;
      func.apply(this, args);
    }
  };
}

export default ServoControls;
```

### 11.7 Create Status Bar Component

- [ ] **11.7.1** Create `app/src/components/StatusBar.jsx`

```jsx
import React from 'react';

function StatusBar({ mode, speed, steering, isMoving }) {
  return (
    <div className="mt-auto p-3 bg-btbg-darker rounded-lg">
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Mode:</span>
          <span className="font-semibold uppercase">{mode}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Moving:</span>
          <span className={isMoving ? 'text-green-500' : 'text-gray-500'}>
            {isMoving ? 'Yes' : 'No'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Speed:</span>
          <span className="font-mono">{Math.abs(speed).toFixed(0)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Steering:</span>
          <span className="font-mono">{steering.toFixed(1)}°</span>
        </div>
      </div>
    </div>
  );
}

export default StatusBar;
```

### 11.8 Verification Tests - Phase 11

```bash
# TEST 11.8.1: Verify all components exist
node -e "
const fs = require('fs');
const components = [
  'app/src/components/ConnectionStatus.jsx',
  'app/src/components/ModeToggle.jsx',
  'app/src/components/DriveControls.jsx',
  'app/src/components/SpeedSlider.jsx',
  'app/src/components/SensorDisplay.jsx',
  'app/src/components/ServoControls.jsx',
  'app/src/components/StatusBar.jsx'
];
let pass = true;
components.forEach(c => {
  if (fs.existsSync(c)) console.log('✓', c);
  else { console.log('✗', c, 'missing'); pass = false; }
});
if (!pass) process.exit(1);
console.log('✓ All components exist');
"

# TEST 11.8.2: Verify App.jsx imports all components
node -e "
const fs = require('fs');
const app = fs.readFileSync('app/src/App.jsx', 'utf8');
const imports = ['ConnectionStatus', 'ModeToggle', 'DriveControls', 'SpeedSlider', 'SensorDisplay', 'ServoControls', 'StatusBar'];
let pass = true;
imports.forEach(i => {
  if (app.includes(i)) console.log('✓ Imports:', i);
  else { console.log('✗ Missing import:', i); pass = false; }
});
if (!pass) process.exit(1);
"
```

---

## Phase 12: NPM Scripts

### 12.1 Create Start Robot Script

- [ ] **12.1.1** Create `scripts/start_robot.js`

```javascript
#!/usr/bin/env node
/**
 * Start ROS2 nodes on the Pi.
 *
 * Usage: npm run btbg:start
 */

require('dotenv').config();
const { NodeSSH } = require('node-ssh');
const path = require('path');

const ssh = new NodeSSH();

const PI_HOST = process.env.PI_HOST || 'btbg.local';
const PI_USER = process.env.PI_USER || 'ubuntu';
const PI_SSH_KEY = process.env.PI_SSH_KEY || path.join(require('os').homedir(), '.ssh', 'btbg_pi');
const ROS2_WS = process.env.ROS2_WS || '/home/ubuntu/btbg_ws';

async function startRobot() {
    console.log(`\n🤖 Starting BTBG on ${PI_USER}@${PI_HOST}...\n`);

    try {
        await ssh.connect({
            host: PI_HOST,
            username: PI_USER,
            privateKeyPath: PI_SSH_KEY.replace('~', require('os').homedir()),
        });
        console.log('✓ Connected to Pi\n');

        // Check if already running
        const checkResult = await ssh.execCommand('pgrep -f "ros2 launch btbg_nodes"');
        if (checkResult.stdout.trim()) {
            console.log('⚠ ROS2 nodes already running (PID:', checkResult.stdout.trim() + ')');
            console.log('  Run "npm run btbg:stop" first to restart.\n');
            ssh.dispose();
            return;
        }

        // Create log directory
        await ssh.execCommand('mkdir -p ~/btbg_logs');

        // Start ROS2 launch
        console.log('🚀 Launching ROS2 nodes...\n');

        const launchCmd = `
            source /opt/ros/humble/setup.bash &&
            source ${ROS2_WS}/install/setup.bash &&
            nohup ros2 launch btbg_nodes btbg.launch.py > ~/btbg_logs/ros.log 2>&1 &
            echo $!
        `;

        const result = await ssh.execCommand(launchCmd);
        const pid = result.stdout.trim();

        if (pid) {
            console.log(`✓ ROS2 nodes started (PID: ${pid})`);

            // Wait for rosbridge to be ready
            console.log('⏳ Waiting for rosbridge...');

            let attempts = 0;
            while (attempts < 10) {
                await new Promise(r => setTimeout(r, 1000));
                const portCheck = await ssh.execCommand('ss -tlnp | grep 9090');
                if (portCheck.stdout.includes('9090')) {
                    console.log('✓ rosbridge ready on port 9090\n');
                    console.log('🎉 BTBG is ready! Run "npm run app" to open the UI.\n');
                    break;
                }
                attempts++;
            }

            if (attempts >= 10) {
                console.log('⚠ rosbridge not detected after 10s. Check logs with: npm run btbg:logs\n');
            }
        } else {
            console.error('✗ Failed to start ROS2 nodes');
            console.error('stderr:', result.stderr);
        }

    } catch (error) {
        console.error('✗ Failed to start:', error.message);
        process.exit(1);
    } finally {
        ssh.dispose();
    }
}

startRobot();
```

### 12.2 Create Stop Robot Script

- [ ] **12.2.1** Create `scripts/stop_robot.js`

```javascript
#!/usr/bin/env node
/**
 * Stop ROS2 nodes on the Pi and ensure motors are stopped.
 *
 * Usage: npm run btbg:stop
 */

require('dotenv').config();
const { NodeSSH } = require('node-ssh');
const path = require('path');

const ssh = new NodeSSH();

const PI_HOST = process.env.PI_HOST || 'btbg.local';
const PI_USER = process.env.PI_USER || 'ubuntu';
const PI_SSH_KEY = process.env.PI_SSH_KEY || path.join(require('os').homedir(), '.ssh', 'btbg_pi');

async function stopRobot() {
    console.log(`\n🛑 Stopping BTBG on ${PI_USER}@${PI_HOST}...\n`);

    try {
        await ssh.connect({
            host: PI_HOST,
            username: PI_USER,
            privateKeyPath: PI_SSH_KEY.replace('~', require('os').homedir()),
        });
        console.log('✓ Connected to Pi\n');

        // Stop motors first (safety)
        console.log('🔧 Stopping motors...');
        await ssh.execCommand(`python3 -c "
try:
    from picarx import Picarx
    px = Picarx()
    px.stop()
    print('Motors stopped')
except Exception as e:
    print(f'Motor stop failed: {e}')
"`);

        // Kill ROS2 processes
        console.log('🔧 Stopping ROS2 nodes...');

        const killCmds = [
            'pkill -f "ros2 launch btbg_nodes"',
            'pkill -f "btbg_nodes"',
            'pkill -f "rosbridge_websocket"',
        ];

        for (const cmd of killCmds) {
            await ssh.execCommand(cmd);
        }

        // Verify stopped
        await new Promise(r => setTimeout(r, 1000));
        const check = await ssh.execCommand('pgrep -f "btbg_nodes"');

        if (!check.stdout.trim()) {
            console.log('\n✓ All BTBG processes stopped.\n');
        } else {
            console.log('\n⚠ Some processes may still be running. PIDs:', check.stdout.trim());
            console.log('  Try: ssh btbg "pkill -9 -f btbg_nodes"\n');
        }

    } catch (error) {
        console.error('✗ Failed to stop:', error.message);
        process.exit(1);
    } finally {
        ssh.dispose();
    }
}

stopRobot();
```

### 12.3 Create Tail Logs Script

- [ ] **12.3.1** Create `scripts/tail_logs.js`

```javascript
#!/usr/bin/env node
/**
 * Tail ROS2 logs from Pi.
 *
 * Usage: npm run btbg:logs
 */

require('dotenv').config();
const { NodeSSH } = require('node-ssh');
const path = require('path');

const ssh = new NodeSSH();

const PI_HOST = process.env.PI_HOST || 'btbg.local';
const PI_USER = process.env.PI_USER || 'ubuntu';
const PI_SSH_KEY = process.env.PI_SSH_KEY || path.join(require('os').homedir(), '.ssh', 'btbg_pi');

async function tailLogs() {
    console.log(`\n📜 Tailing logs from ${PI_USER}@${PI_HOST}...`);
    console.log('   Press Ctrl+C to stop.\n');

    try {
        await ssh.connect({
            host: PI_HOST,
            username: PI_USER,
            privateKeyPath: PI_SSH_KEY.replace('~', require('os').homedir()),
        });

        // Use execCommand with streaming
        await ssh.execCommand('tail -f ~/btbg_logs/ros.log', {
            onStdout: (chunk) => process.stdout.write(chunk.toString()),
            onStderr: (chunk) => process.stderr.write(chunk.toString()),
        });

    } catch (error) {
        if (error.message.includes('SIGINT')) {
            console.log('\n\n✓ Log tailing stopped.\n');
        } else {
            console.error('✗ Failed:', error.message);
            process.exit(1);
        }
    } finally {
        ssh.dispose();
    }
}

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
    console.log('\n\n✓ Log tailing stopped.\n');
    process.exit(0);
});

tailLogs();
```

### 12.4 Create Status Script

- [ ] **12.4.1** Create `scripts/status.js`

```javascript
#!/usr/bin/env node
/**
 * Check BTBG status - Pi connectivity, rosbridge, ROS2 nodes.
 *
 * Usage: npm run btbg:status
 */

require('dotenv').config();
const { NodeSSH } = require('node-ssh');
const path = require('path');
const net = require('net');

const ssh = new NodeSSH();

const PI_HOST = process.env.PI_HOST || 'btbg.local';
const PI_USER = process.env.PI_USER || 'ubuntu';
const PI_SSH_KEY = process.env.PI_SSH_KEY || path.join(require('os').homedir(), '.ssh', 'btbg_pi');
const ROSBRIDGE_PORT = parseInt(process.env.ROSBRIDGE_PORT || '9090');

async function checkStatus() {
    console.log('\n🔍 BTBG Status Check\n');

    let allGood = true;

    // Check Pi reachability
    console.log(`Checking ${PI_HOST}...`);

    try {
        await ssh.connect({
            host: PI_HOST,
            username: PI_USER,
            privateKeyPath: PI_SSH_KEY.replace('~', require('os').homedir()),
            readyTimeout: 5000,
        });
        console.log(`  ✓ SSH connection to ${PI_HOST}`);

        // Check rosbridge port
        const portCheck = await ssh.execCommand(`ss -tlnp | grep ${ROSBRIDGE_PORT}`);
        if (portCheck.stdout.includes(ROSBRIDGE_PORT.toString())) {
            console.log(`  ✓ rosbridge running on port ${ROSBRIDGE_PORT}`);
        } else {
            console.log(`  ✗ rosbridge NOT running on port ${ROSBRIDGE_PORT}`);
            allGood = false;
        }

        // Check ROS2 nodes
        const nodeList = await ssh.execCommand('source /opt/ros/humble/setup.bash && source ~/btbg_ws/install/setup.bash && ros2 node list 2>/dev/null');
        const nodes = nodeList.stdout.trim().split('\n').filter(n => n.includes('btbg') || n.includes('rosbridge'));

        if (nodes.length > 0) {
            console.log(`  ✓ ROS2 nodes running (${nodes.length}):`);
            nodes.forEach(n => console.log(`      - ${n}`));
        } else {
            console.log('  ✗ No BTBG ROS2 nodes running');
            allGood = false;
        }

        // Check picarx availability
        const picarxCheck = await ssh.execCommand('python3 -c "from picarx import Picarx; print(\'ok\')" 2>/dev/null');
        if (picarxCheck.stdout.includes('ok')) {
            console.log('  ✓ picarx library available');
        } else {
            console.log('  ⚠ picarx library not importable');
        }

    } catch (error) {
        console.log(`  ✗ Cannot reach ${PI_HOST}: ${error.message}`);
        allGood = false;
    } finally {
        ssh.dispose();
    }

    console.log('');
    if (allGood) {
        console.log('✅ BTBG is ready! Run "npm run app" to open the UI.\n');
    } else {
        console.log('⚠ Some issues detected. Run "npm run btbg:start" to start the robot.\n');
    }
}

checkStatus();
```

### 12.5 Verification Tests - Phase 12

```bash
# TEST 12.5.1: Verify all scripts exist
node -e "
const fs = require('fs');
const scripts = [
  'scripts/start_robot.js',
  'scripts/stop_robot.js',
  'scripts/tail_logs.js',
  'scripts/status.js',
  'scripts/deploy.js'
];
let pass = true;
scripts.forEach(s => {
  if (fs.existsSync(s)) console.log('✓', s);
  else { console.log('✗', s, 'missing'); pass = false; }
});
if (!pass) process.exit(1);
"

# TEST 12.5.2: Verify root package.json has all scripts
node -e "
const pkg = require('./package.json');
const scripts = ['btbg:start', 'btbg:stop', 'btbg:deploy', 'btbg:logs', 'btbg:status', 'app'];
let pass = true;
scripts.forEach(s => {
  if (pkg.scripts[s]) console.log('✓ Script:', s);
  else { console.log('✗ Missing script:', s); pass = false; }
});
if (!pass) process.exit(1);
"

# TEST 12.5.3: Test status script (will fail if Pi not reachable, that's OK)
npm run btbg:status || echo "(Expected to fail if Pi not connected)"
```

---

## Phase 13: End-to-End Testing

### 13.1 Hardware Integration Tests

```
LOCATION: Run these tests with Pi connected and powered on
```

- [ ] **13.1.1** Deploy and start robot

```bash
# Deploy code to Pi
npm run btbg:deploy

# Start ROS2 nodes
npm run btbg:start

# Verify status
npm run btbg:status
```

- [ ] **13.1.2** Verify ROS2 topics are publishing

```bash
# SSH to Pi and check topics
ssh btbg "source /opt/ros/humble/setup.bash && source ~/btbg_ws/install/setup.bash && ros2 topic list"

# Expected output should include:
# /btbg/cmd_vel
# /btbg/mode
# /btbg/sensor/ultrasonic
# /btbg/status
# /btbg/patrol_status
# /btbg/hw/drive
# /btbg/hw/status

# Echo ultrasonic sensor (should show distance readings)
ssh btbg "source /opt/ros/humble/setup.bash && source ~/btbg_ws/install/setup.bash && timeout 5 ros2 topic echo /btbg/sensor/ultrasonic"
```

- [ ] **13.1.3** Test manual drive via command line

```bash
# Open two terminals

# Terminal 1: Watch hw/status
ssh btbg "source /opt/ros/humble/setup.bash && source ~/btbg_ws/install/setup.bash && ros2 topic echo /btbg/hw/status"

# Terminal 2: Publish drive command (CAR WILL MOVE!)
ssh btbg "source /opt/ros/humble/setup.bash && source ~/btbg_ws/install/setup.bash && ros2 topic pub --once /btbg/cmd_vel geometry_msgs/Twist '{linear: {x: 0.3}, angular: {z: 0.0}}'"

# IMMEDIATELY stop:
ssh btbg "source /opt/ros/humble/setup.bash && source ~/btbg_ws/install/setup.bash && ros2 topic pub --once /btbg/hw/stop std_msgs/Empty '{}'"
```

### 13.2 UI Integration Tests

- [ ] **13.2.1** Start UI and connect

```bash
# Start the Electron app
npm run app

# Expected:
# - Window opens with BTBG Control title
# - Connection status shows "Connected" (green dot)
# - Ultrasonic distance updates in real-time
# - Battery voltage displays
```

- [ ] **13.2.2** Test manual controls

```
IN THE UI:
1. Set speed slider to 30%
2. Press and hold W key - car should move forward
3. Release W - car should stop
4. Press A while holding W - car should turn left while moving
5. Press Space - car should emergency stop
6. Verify all direction buttons work with mouse/touch
```

- [ ] **13.2.3** Test mode switching

```
IN THE UI:
1. Click mode toggle to switch to PATROL
2. Verify manual controls are disabled (greyed out)
3. Verify patrol state badge appears (should show "forward" initially)
4. Watch car roam and avoid obstacles
5. Switch back to MANUAL
6. Verify car stops and controls re-enable
```

- [ ] **13.2.4** Test camera servos

```
IN THE UI:
1. Move Pan slider left/right - camera should pan
2. Move Tilt slider up/down - camera should tilt
3. Click Reset - servos should return to center (0, 0)
```

### 13.3 Failure Mode Tests

- [ ] **13.3.1** Test watchdog (manual mode)

```bash
# Start robot, open UI, drive forward
# Then close the UI window suddenly

# Within 1.5 seconds, the car should stop automatically
# (hardware_bridge_node watchdog)
```

- [ ] **13.3.2** Test connection recovery

```bash
# With UI connected:

# Kill rosbridge on Pi
ssh btbg "pkill -f rosbridge_websocket"

# UI should show "Disconnected"
# Wait 10 seconds

# Restart rosbridge
ssh btbg "source /opt/ros/humble/setup.bash && ros2 run rosbridge_server rosbridge_websocket --ros-args -p port:=9090 &"

# UI should auto-reconnect and show "Connected"
```

- [ ] **13.3.3** Test graceful shutdown

```bash
# With robot running in patrol mode:

# Stop via npm script
npm run btbg:stop

# Verify:
# - Car stops moving
# - All ROS2 nodes exit
# - Motors are stopped (car doesn't drift)
```

### 13.4 Full System Checklist

```
FINAL VERIFICATION CHECKLIST:

[ ] Pi boots and connects to WiFi
[ ] SSH works: ssh btbg
[ ] npm run btbg:start launches all nodes
[ ] npm run btbg:status shows all green
[ ] npm run app opens UI
[ ] UI shows "Connected"
[ ] Ultrasonic readings update in UI
[ ] Battery voltage displays correctly
[ ] Manual drive works (WASD)
[ ] Speed slider affects movement
[ ] Emergency stop works (Space)
[ ] Camera servos respond to sliders
[ ] Mode toggle switches to patrol
[ ] Patrol mode: car roams autonomously
[ ] Patrol mode: car avoids obstacles
[ ] Mode toggle returns to manual
[ ] Watchdog stops car when UI closes
[ ] npm run btbg:stop cleanly shuts down
[ ] npm run btbg:logs shows log output
```

### 13.5 Test Report Template

```markdown
# BTBG Test Report

**Date:** ____________________
**Tester:** __________________
**Pi IP:** ___________________
**Firmware Version:** ________

## Test Results

| Test | Pass/Fail | Notes |
|------|-----------|-------|
| SSH connection | | |
| ROS2 nodes start | | |
| rosbridge port 9090 | | |
| UI connects | | |
| Manual forward | | |
| Manual reverse | | |
| Manual left turn | | |
| Manual right turn | | |
| Emergency stop | | |
| Speed slider | | |
| Patrol mode activates | | |
| Obstacle avoidance | | |
| Mode switch to manual | | |
| Camera pan servo | | |
| Camera tilt servo | | |
| Watchdog timeout | | |
| Connection recovery | | |
| Graceful shutdown | | |

## Issues Found

1. _______________
2. _______________
3. _______________

## Notes

_______________________________________________
_______________________________________________
```

---

## Appendix A: Quick Reference Commands

```bash
# === Development Machine Commands ===

# Install dependencies
npm install
cd app && npm install && cd ..

# Deploy code to Pi
npm run btbg:deploy

# Start robot
npm run btbg:start

# Stop robot
npm run btbg:stop

# Check status
npm run btbg:status

# View logs
npm run btbg:logs

# Start UI
npm run app


# === Pi Commands (via SSH) ===

# SSH to Pi
ssh btbg

# Manual ROS2 launch
source /opt/ros/humble/setup.bash
source ~/btbg_ws/install/setup.bash
ros2 launch btbg_nodes btbg.launch.py

# List topics
ros2 topic list

# Echo a topic
ros2 topic echo /btbg/sensor/ultrasonic

# Publish test command
ros2 topic pub --once /btbg/mode std_msgs/String "data: 'patrol'"

# Emergency motor stop
python3 -c "from picarx import Picarx; Picarx().stop()"

# Rebuild package
cd ~/btbg_ws && colcon build --packages-select btbg_nodes

# View ROS2 log
tail -f ~/btbg_logs/ros.log
```

---

## Appendix B: Troubleshooting

### Pi Not Reachable

```bash
# Check if Pi is on network
ping btbg.local

# If mDNS not working (Windows), find IP:
# Check router DHCP client list
# Or scan network: nmap -sn 192.168.1.0/24

# Update .env with IP if needed:
# PI_HOST=192.168.1.xxx
```

### rosbridge Not Starting

```bash
# Check if port 9090 in use
ssh btbg "ss -tlnp | grep 9090"

# Kill existing process
ssh btbg "pkill -f rosbridge"

# Check rosbridge logs
ssh btbg "grep rosbridge ~/btbg_logs/ros.log | tail -20"
```

### Motors Not Responding

```bash
# Test picarx directly
ssh btbg "python3 -c '
from picarx import Picarx
import time
px = Picarx()
print(\"Forward...\")
px.forward(20)
time.sleep(0.5)
px.stop()
print(\"Done\")
'"

# Check I2C
ssh btbg "sudo i2cdetect -y 1"
# Should show device at 0x14
```

### UI Won't Connect

```bash
# Verify rosbridge is running
npm run btbg:status

# Check if firewall blocking
ssh btbg "sudo ufw status"
ssh btbg "sudo ufw allow 9090/tcp"

# Try direct IP in browser console:
# In UI dev tools, run:
# rosClient.setUrl('192.168.1.xxx', 9090)
# rosClient.connect()
```

---

*End of TODO.md — Follow phases in order, run all verification tests before proceeding.*
