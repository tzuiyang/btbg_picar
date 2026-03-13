# BTBG — Master Plan
> **Project Name:** BTBG (Big Thing Big Gun)
> **Version:** 1.1.0
> **Last Updated:** 2026-03-13
> **Purpose:** This document is the single source of truth for the BTBG robot car project. Feed this file to any coding agent to get full context on the system, hardware, software stack, architecture, and implementation plan.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Hardware Inventory](#2-hardware-inventory)
3. [Software Stack](#3-software-stack)
4. [System Architecture](#4-system-architecture)
5. [Directory Structure](#5-directory-structure)
6. [ROS2 Node Architecture](#6-ros2-node-architecture)
7. [Communication Protocol](#7-communication-protocol)
8. [Feature Specifications](#8-feature-specifications)
9. [Electron UI Specification](#9-electron-ui-specification)
10. [NPM Workflow](#10-npm-workflow)
11. [Network & SSH Setup](#11-network--ssh-setup)
12. [Environment Configuration](#12-environment-configuration)
13. [Implementation Phases](#13-implementation-phases)
14. [Error Handling & Recovery](#14-error-handling--recovery)
15. [Known Constraints & Gotchas](#15-known-constraints--gotchas)
16. [Future Features (Backlog)](#16-future-features-backlog)

---

## 1. Project Overview

BTBG is a Raspberry Pi 5 powered robot car built on the SunFounder PiCar-X kit. It is controlled via an Electron desktop application that communicates with the car over a local network (WiFi). The car runs ROS2 nodes on the Raspberry Pi 5 that handle all hardware abstraction, sensor processing, and autonomous behaviours.

### Core Philosophy
- The Electron UI is a **dumb passthrough** — it sends commands and displays state, it does not contain any robot logic.
- All intelligence (patrol algorithm, obstacle avoidance, sensor fusion) lives on the Pi in ROS2 nodes.
- Communication between the Electron UI and the Pi is via **WebSocket** (bridged from ROS2 using `rosbridge_suite`).
- The developer workflow mirrors a modern web app: `npm run btbg:start` boots the robot, `npm run app` opens the UI.

### Primary Features (v1.0)
1. **Manual Car Control** — Drive the car in real time from the Electron UI (forward, backward, left, right, stop, speed control).
2. **Random Patrol Mode** — Car roams autonomously using the ultrasonic sensor to detect and avoid obstacles with randomised turning.

### Secondary Features (Planned, not v1.0)
- Facial recognition security patrol
- Camera live stream in UI
- Voice command control
- Emotion-reactive behaviour
- Environmental heat mapping

---

## 2. Hardware Inventory

### 2.1 Compute
| Component | Model | Specs |
|---|---|---|
| Single Board Computer | Raspberry Pi 5 | 8GB LPDDR4X RAM, Quad-core ARM Cortex-A76 @ 2.4GHz |
| Storage | MicroSD | 64GB minimum, Class A2 (e.g. Samsung Pro Endurance) |
| Power (Pi) | USB-C PD | 27W 5V/5A (official Raspberry Pi 27W supply recommended) |

### 2.2 Robot Kit — SunFounder PiCar-X
| Component | Details |
|---|---|
| Kit | SunFounder PiCar-X v2.0 |
| Chassis | 2-wheel drive with front steering servo |
| Drive Motors | 2x DC gear motors (rear wheels) |
| Steering Servo | 1x servo for front axle direction |
| Camera Pan Servo | 1x servo (pan/horizontal) |
| Camera Tilt Servo | 1x servo (tilt/vertical) |
| Camera | Raspberry Pi Camera Module (connected via CSI ribbon) |
| Ultrasonic Sensor | HC-SR04 compatible (mounted front, for obstacle detection) |
| Grayscale Sensors | 3x grayscale sensors (line following, mounted underneath) |
| Battery | 7.4V 2000mAh LiPo (powers motors + Pi via HAT) |
| HAT | SunFounder Robot HAT (sits on Pi GPIO, controls all servos/motors/sensors) |
| Buzzer | On-board buzzer via Robot HAT |
| LEDs | On-board RGB LEDs via Robot HAT |

### 2.3 Robot HAT Pin Mapping (SunFounder Robot HAT v2)
The Robot HAT communicates with the Pi over I2C and direct GPIO.

| Function | HAT Channel / GPIO |
|---|---|
| Left motor (rear) | Motor channel M1 |
| Right motor (rear) | Motor channel M2 |
| Steering servo | Servo channel P0 |
| Camera pan servo | Servo channel P1 |
| Camera tilt servo | Servo channel P2 |
| Ultrasonic TRIG | GPIO pin (managed by picarx lib) |
| Ultrasonic ECHO | GPIO pin (managed by picarx lib) |
| Grayscale sensor | ADC channels A0, A1, A2 |
| Buzzer | via Robot HAT register |
| LEDs | via Robot HAT register |

### 2.4 Developer Machine
- Any macOS / Windows / Linux desktop or laptop on the same WiFi network as the Pi.
- Node.js 20+ and npm installed locally.
- Electron app runs locally on the developer machine.
- SSH access to the Pi configured.
- **Windows users:** Requires WSL2 or Git Bash to run shell scripts. Alternatively, use the cross-platform Node.js scripts (see Section 10).

---

## 3. Software Stack

### 3.1 Raspberry Pi (Robot Side)
| Layer | Technology | Version | Purpose |
|---|---|---|---|
| OS | **Ubuntu 22.04 Server 64-bit** | 22.04 LTS | Base OS (recommended for ROS2 compatibility) |
| Robot Framework | ROS2 | Humble Hawksbill | Node orchestration, pub/sub |

> **OS Choice Rationale:** We use Ubuntu 22.04 Server instead of Raspberry Pi OS because ROS2 Humble officially targets Ubuntu 22.04. Pi OS Bookworm (Debian 12) requires unofficial ROS2 builds that may have compatibility issues. Ubuntu Server runs headless on Pi 5 with full ROS2 apt repository support.
| ROS2 WebSocket Bridge | rosbridge_suite | Latest for ROS2 | Exposes ROS2 topics over WebSocket |
| Python Runtime | Python | 3.11+ | ROS2 nodes are written in Python |
| PiCar-X Library | picarx | 2.0.x | Hardware abstraction for motors/servos/sensors |
| Robot HAT Library | robot-hat | 2.0.x | Low-level HAT communication |
| Camera Library | picamera2 | 0.3.x | Camera capture and streaming |
| OpenCV | opencv-python-headless | 4.9.x | Image processing (future: face recognition) |

### 3.2 Developer Machine (UI Side)
| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Runtime | Node.js | 20 LTS | JS runtime |
| Desktop App | Electron | 30+ | Desktop UI wrapper |
| UI Framework | React | 18 | Component-based UI |
| Build Tool | Vite | 5 | Fast dev server + bundler |
| WebSocket Client | roslibjs | Latest | Connects to rosbridge on Pi |
| Styling | Tailwind CSS | 3 | Utility-first CSS |
| Package Manager | npm | Latest | Scripts + dependency management |

### 3.3 Communication Layer
| Protocol | Usage |
|---|---|
| WebSocket (ws://) | ROS2 ↔ Electron UI via rosbridge_suite on port 9090 |
| SSH | Developer machine → Pi for starting/stopping nodes |
| mDNS / hostname | Discover Pi on local network as `btbg.local` |
| WiFi (802.11ac) | Pi connects to local router, same network as dev machine |

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   DEVELOPER MACHINE                         │
│                                                             │
│   ┌──────────────────────────────────────────────────┐     │
│   │              Electron App (npm run app)           │     │
│   │                                                   │     │
│   │   ┌─────────────┐    ┌───────────────────────┐   │     │
│   │   │  React UI   │───▶│  roslibjs WebSocket   │   │     │
│   │   │  (controls) │◀───│  client               │   │     │
│   │   └─────────────┘    └──────────┬────────────┘   │     │
│   └──────────────────────────────────┼───────────────┘     │
│                                      │ WebSocket            │
│                           ws://btbg.local:9090              │
└──────────────────────────────────────┼─────────────────────┘
                                       │
┌──────────────────────────────────────┼─────────────────────┐
│              RASPBERRY PI 5 (btbg.local)                    │
│                                      │                      │
│   ┌──────────────────────────────────▼────────────────┐    │
│   │            rosbridge_server (port 9090)            │    │
│   │            Bridges WebSocket ↔ ROS2 topics        │    │
│   └───────┬──────────────────────────┬────────────────┘    │
│           │ ROS2 DDS                 │ ROS2 DDS             │
│   ┌───────▼──────────┐   ┌──────────▼─────────┐           │
│   │  /btbg/cmd_vel   │   │  /btbg/sensor_data  │           │
│   │  /btbg/mode      │   │  /btbg/camera       │           │
│   │  /btbg/servo_cmd │   │  /btbg/status       │           │
│   └───────┬──────────┘   └──────────┬──────────┘           │
│           │                         │                       │
│   ┌───────▼──────────────────────────▼──────────────┐      │
│   │              ROS2 Nodes                          │      │
│   │                                                  │      │
│   │  ┌──────────────┐  ┌───────────────────────┐   │      │
│   │  │ car_control  │  │   patrol_node         │   │      │
│   │  │ _node        │  │   (autonomous mode)   │   │      │
│   │  └──────┬───────┘  └──────────┬────────────┘   │      │
│   │         │                     │                 │      │
│   │  ┌──────▼──────────────────────▼────────────┐  │      │
│   │  │         hardware_bridge_node              │  │      │
│   │  │   (picarx lib — motors/servos/sensors)    │  │      │
│   │  └──────────────────┬───────────────────────┘  │      │
│   └─────────────────────┼─────────────────────────┘       │
│                          │ I2C + GPIO                       │
│   ┌──────────────────────▼─────────────────────────┐       │
│   │           SunFounder Robot HAT                  │       │
│   │   Motors | Servos | Ultrasonic | Grayscale      │       │
│   └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Directory Structure

```
btbg/                               ← project root (on developer machine)
├── package.json                    ← root npm scripts (btbg:start, app, etc.)
├── MASTER_PLAN.md                  ← this file
├── .env                            ← PI_HOST, PI_USER, SSH key path
├── .env.example
│
├── scripts/                        ← cross-platform Node.js scripts (called by npm)
│   ├── start_robot.js              ← SSH into Pi, launch ROS2 nodes
│   ├── stop_robot.js               ← SSH into Pi, kill ROS2 nodes
│   ├── deploy.js                   ← sync robot/ code to Pi, rebuild
│   ├── tail_logs.js                ← stream ROS2 logs from Pi
│   ├── status.js                   ← check Pi/rosbridge/node status
│   ├── setup_dev.js                ← one-time dev machine setup
│   └── bash/                       ← Unix shell script alternatives
│       ├── start_robot.sh
│       ├── stop_robot.sh
│       └── deploy.sh
│
├── app/                            ← Electron + React UI (runs on dev machine)
│   ├── package.json
│   ├── vite.config.js
│   ├── electron/
│   │   ├── main.js                 ← Electron main process
│   │   └── preload.js              ← Context bridge
│   └── src/
│       ├── main.jsx                ← React entry point
│       ├── App.jsx                 ← Root component
│       ├── ros/
│       │   ├── rosClient.js        ← roslibjs singleton connection
│       │   └── topics.js           ← All topic name constants
│       ├── components/
│       │   ├── ConnectionStatus.jsx
│       │   ├── DriveControls.jsx   ← WASD / joystick passthrough
│       │   ├── SpeedSlider.jsx
│       │   ├── ModeToggle.jsx      ← Manual ↔ Patrol
│       │   ├── SensorDisplay.jsx   ← Ultrasonic distance readout
│       │   └── StatusBar.jsx
│       └── styles/
│           └── index.css
│
└── robot/                          ← All code that runs ON the Raspberry Pi
    ├── setup.sh                    ← One-time Pi setup script
    ├── requirements.txt            ← Python pip dependencies (pinned versions)
    ├── launch/
    │   └── btbg.launch.py          ← ROS2 launch file (starts all nodes)
    ├── btbg_nodes/                 ← ROS2 Python package
    │   ├── package.xml
    │   ├── setup.py
    │   └── btbg_nodes/
    │       ├── __init__.py
    │       ├── car_control_node.py     ← Subscribes to cmd_vel, drives motors
    │       ├── patrol_node.py          ← Autonomous patrol logic
    │       ├── hardware_bridge_node.py ← picarx lib wrapper
    │       ├── sensor_node.py          ← Publishes ultrasonic + grayscale data
    │       └── camera_node.py          ← Publishes camera frames (future)
    └── config/
        ├── btbg_params.yaml        ← ROS2 parameters (speeds, distances, etc.)
        └── calibration.yaml        ← Servo calibration offsets
```

---

## 6. ROS2 Node Architecture

### 6.1 Node: `car_control_node`
**File:** `robot/btbg_nodes/btbg_nodes/car_control_node.py`

**Purpose:** Central command arbiter. Listens for drive commands from both the UI (manual mode) and patrol_node (patrol mode), and forwards the active mode's commands to hardware_bridge_node.

**Subscriptions:**
| Topic | Message Type | Description |
|---|---|---|
| `/btbg/cmd_vel` | `geometry_msgs/Twist` | From UI: Linear.x = forward/backward speed (-1.0 to 1.0), Angular.z = steering angle |
| `/btbg/patrol_cmd_vel` | `geometry_msgs/Twist` | From patrol_node: same format as cmd_vel |
| `/btbg/mode` | `std_msgs/String` | `"manual"` or `"patrol"` — switches active control mode |
| `/btbg/servo_cmd` | `std_msgs/Float32MultiArray` | [pan_angle, tilt_angle] for camera servos |

**Publishes:**
| Topic | Message Type | Description |
|---|---|---|
| `/btbg/hw/drive` | `std_msgs/Float32MultiArray` | [speed, steering_angle] forwarded to hardware_bridge_node |
| `/btbg/hw/servo` | `std_msgs/Float32MultiArray` | [pan, tilt] forwarded to hardware_bridge_node |
| `/btbg/status` | `std_msgs/String` | JSON string: current speed, angle, mode |

**Topic Flow Diagram:**
```
UI (roslibjs)                    patrol_node
     │                                │
     ▼                                ▼
/btbg/cmd_vel              /btbg/patrol_cmd_vel
     │                                │
     └──────────┬─────────────────────┘
                │
                ▼
        car_control_node
        (mode arbitration)
                │
                ▼
         /btbg/hw/drive
                │
                ▼
      hardware_bridge_node
                │
                ▼
           Picarx()
```

**Behaviour:**
- On `cmd_vel` message (from UI): if mode is `"manual"`, scale `linear.x` to speed 0–100, scale `angular.z` to steering angle -40° to +40°, publish to `/btbg/hw/drive`.
- On `patrol_cmd_vel` message (from patrol_node): if mode is `"patrol"`, forward to `/btbg/hw/drive`.
- If mode doesn't match the source, ignore the command.
- On zero velocity, publish stop command to `/btbg/hw/drive`.
- Watchdog: if no commands received for 1000ms in manual mode, publish stop (safety). Patrol mode has its own watchdog.

---

### 6.2 Node: `patrol_node`
**File:** `robot/btbg_nodes/btbg_nodes/patrol_node.py`

**Purpose:** Autonomous patrol behaviour. Drives forward until an obstacle is detected, then backs up and turns a random amount.

**Subscriptions:**
| Topic | Message Type | Description |
|---|---|---|
| `/btbg/mode` | `std_msgs/String` | Activates when value is `"patrol"` |
| `/btbg/sensor/ultrasonic` | `sensor_msgs/Range` | Incoming distance reading from sensor_node |

**Publishes:**
| Topic | Message Type | Description |
|---|---|---|
| `/btbg/patrol_cmd_vel` | `geometry_msgs/Twist` | Publishes drive commands to car_control_node (separate topic from manual) |
| `/btbg/patrol_status` | `std_msgs/String` | JSON: `{ "state": "forward" | "avoiding" | "reversing" | "turning" | "idle" }` |

**State Machine (non-blocking):**
```
States: IDLE, FORWARD, REVERSING, TURNING

PATROL_SPEED = 30           # % motor speed
OBSTACLE_THRESHOLD = 25     # cm (increased for stopping distance at 30% speed)
REVERSE_SPEED = 20          # % motor speed
REVERSE_DURATION = 0.5      # seconds
TURN_DURATION_BASE = 0.8    # seconds base turn time
TURN_ANGLES = [-120, -90, -60, 60, 90, 120]   # degrees, chosen randomly

┌─────────────────────────────────────────────────────────────┐
│                         IDLE                                 │
│  (mode != "patrol")                                         │
└─────────────────────┬───────────────────────────────────────┘
                      │ mode == "patrol"
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                       FORWARD                                │
│  - publish forward velocity at PATROL_SPEED ± random(5)     │
│  - check ultrasonic every 100ms                             │
└─────────┬──────────────────────────────────────┬────────────┘
          │ distance < OBSTACLE_THRESHOLD        │ mode != "patrol"
          ▼                                      ▼
┌─────────────────────────┐                    IDLE
│       REVERSING          │
│  - publish reverse vel   │
│  - start reverse_timer   │
└─────────┬───────────────┘
          │ timer fires (0.5s)
          ▼
┌─────────────────────────┐
│        TURNING           │
│  - pick random angle     │
│  - publish turn command  │
│  - start turn_timer      │
└─────────┬───────────────┘
          │ timer fires
          ▼
        FORWARD
```

**Implementation Notes:**
- Uses ROS2 timers instead of `sleep()` to avoid blocking the executor.
- All state transitions happen in timer callbacks, allowing mode changes to be processed immediately.
- If ultrasonic returns `None` for 5 consecutive readings, transition to IDLE and log warning.

**Parameters (from btbg_params.yaml):**
- `patrol.speed` (default: 30)
- `patrol.obstacle_threshold_cm` (default: 25)
- `patrol.reverse_speed` (default: 20)
- `patrol.reverse_duration_s` (default: 0.5)
- `patrol.turn_duration_base_s` (default: 0.8)
- `patrol.scan_interval_ms` (default: 100)

---

### 6.3 Node: `sensor_node`
**File:** `robot/btbg_nodes/btbg_nodes/sensor_node.py`

**Purpose:** Polls all hardware sensors and publishes their data to ROS2 topics at fixed intervals.

**Publishes:**
| Topic | Message Type | Rate | Description |
|---|---|---|---|
| `/btbg/sensor/ultrasonic` | `sensor_msgs/Range` | 10 Hz | Distance in cm from HC-SR04 |
| `/btbg/sensor/grayscale` | `std_msgs/Float32MultiArray` | 10 Hz | [left, center, right] ADC values 0–1.0 |
| `/btbg/sensor/battery` | `std_msgs/Float32` | 0.5 Hz | Battery voltage |

**Implementation note:** Uses `px.ultrasonic.read()` from the picarx library. Filters out `None` and values > 300cm (sensor noise). Publishes `sensor_msgs/Range` with `min_range=2cm`, `max_range=300cm`.

---

### 6.4 Node: `hardware_bridge_node`
**File:** `robot/btbg_nodes/btbg_nodes/hardware_bridge_node.py`

**Purpose:** Owns the single `Picarx()` instance. All other nodes that need to move the car must go through this node. This prevents two nodes from calling picarx simultaneously (which causes I2C conflicts).

**Subscriptions:**
| Topic | Message Type | Description |
|---|---|---|
| `/btbg/hw/drive` | `std_msgs/Float32MultiArray` | [speed, steering_angle] — speed -100 to 100 (negative = reverse) |
| `/btbg/hw/servo` | `std_msgs/Float32MultiArray` | [pan, tilt] in degrees |
| `/btbg/hw/stop` | `std_msgs/Empty` | Immediately stop all motors |
| `/btbg/hw/buzzer` | `std_msgs/Bool` | Buzzer on/off |

**Behaviour:**
- On `/btbg/hw/drive`: call `px.set_dir_servo_angle(steering)` then `px.forward(speed)` or `px.backward(abs(speed))`.
- Clamps speed to valid range (15–100, since motors stall below 15%).
- Hardware watchdog: if no `/btbg/hw/drive` received for 1500ms, call `px.stop()` automatically.
- Graceful shutdown: registers SIGTERM/SIGINT handlers to call `px.stop()` before exit.

**Graceful Shutdown Implementation:**
```python
import signal

def shutdown_handler(signum, frame):
    self.get_logger().info('Shutdown signal received, stopping motors')
    self.px.stop()
    rclpy.shutdown()

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)
```

**Note:** `car_control_node` handles mode arbitration and publishes only the active mode's commands to `/btbg/hw/drive`. This node does not need to know about modes.

---

### 6.5 Node: `rosbridge_server`
Not a custom node — this is the standard `rosbridge_suite` package. Launched via the launch file. Runs on **port 9090**. Bridges all ROS2 topics over WebSocket so the Electron UI can pub/sub without native ROS2.

---

## 7. Communication Protocol

### 7.1 WebSocket Connection
- **URL:** `ws://btbg.local:9090` (or `ws://<pi-ip>:9090`)
- **Protocol:** rosbridge v2 JSON protocol
- **Client library:** `roslibjs` in the Electron app

### 7.2 UI → Robot (Commands)

**Drive command (manual mode):**
```json
{
  "op": "publish",
  "topic": "/btbg/cmd_vel",
  "type": "geometry_msgs/Twist",
  "msg": {
    "linear": { "x": 0.5, "y": 0.0, "z": 0.0 },
    "angular": { "x": 0.0, "y": 0.0, "z": -0.3 }
  }
}
```
- `linear.x`: -1.0 (full reverse) to 1.0 (full forward). Scaled to 0–100% motor speed on Pi.
- `angular.z`: -1.0 (full right) to 1.0 (full left). Scaled to ±40° steering angle on Pi.

**Mode switch:**
```json
{
  "op": "publish",
  "topic": "/btbg/mode",
  "type": "std_msgs/String",
  "msg": { "data": "patrol" }
}
```
Valid values: `"manual"`, `"patrol"`

**Camera servo:**
```json
{
  "op": "publish",
  "topic": "/btbg/servo_cmd",
  "type": "std_msgs/Float32MultiArray",
  "msg": { "data": [30.0, -15.0] }
}
```
- `data[0]`: pan angle in degrees (-90 to +90)
- `data[1]`: tilt angle in degrees (-35 to +35)

**Emergency stop:**
```json
{
  "op": "publish",
  "topic": "/btbg/hw/stop",
  "type": "std_msgs/Empty",
  "msg": {}
}
```

### 7.3 Robot → UI (Telemetry)

**Ultrasonic sensor:**
```json
{
  "op": "publish",
  "topic": "/btbg/sensor/ultrasonic",
  "type": "sensor_msgs/Range",
  "msg": { "range": 45.3 }
}
```

**Status:**
```json
{
  "op": "publish",
  "topic": "/btbg/status",
  "type": "std_msgs/String",
  "msg": {
    "data": "{\"mode\": \"patrol\", \"speed\": 30, \"steering\": 0, \"patrol_state\": \"forward\"}"
  }
}
```

**Patrol status:**
```json
{
  "op": "publish",
  "topic": "/btbg/patrol_status",
  "type": "std_msgs/String",
  "msg": { "data": "{\"state\": \"avoiding\", \"distance\": 14.2}" }
}
```

---

## 8. Feature Specifications

### 8.1 Manual Car Control

**Input methods in UI:**
1. **Keyboard (WASD / Arrow keys):**
   - `W` / `↑` → forward
   - `S` / `↓` → backward
   - `A` / `←` → steer left (while driving)
   - `D` / `→` → steer right (while driving)
   - `Space` → emergency stop
   - Key held down = continuous publish at 20Hz
   - Key released = publish stop command

2. **On-screen D-pad buttons:** Same as keyboard, for mouse/touch use.

3. **Speed slider:** 0–100%, adjusts the scale factor applied to `linear.x`.

**Steering behaviour:**
- Steering only takes effect when the car is moving (forward or backward).
- Steering angle is proportional to `angular.z` value sent.
- Max steering angle: ±40 degrees (picarx hardware limit).

**Camera servo control (v1.0 — no live stream yet):**
- Two sliders in UI: Pan (-90° to +90°) and Tilt (-35° to +35°).
- Publish to `/btbg/servo_cmd` on slider change (throttled to 10Hz max).
- Note: Camera servos are functional in v1.0 for manual positioning. Live camera streaming is a future feature (see Section 15). The servos are useful for adjusting camera angle before patrol mode.

---

### 8.2 Random Patrol Mode

**Activation:** Toggle switch in UI sets mode to `"patrol"`. Manual controls are disabled (greyed out) in the UI while patrol is active.

**Algorithm (full detail):**
1. Drive forward at `PATROL_SPEED` (default 30%).
2. Continuously read ultrasonic sensor at 10Hz.
3. If distance reading < `OBSTACLE_THRESHOLD` (20cm):
   a. Stop immediately.
   b. Wait 100ms (settle).
   c. Reverse at `REVERSE_SPEED` (20%) for `REVERSE_DURATION` (0.4s).
   d. Stop.
   e. Pick a random turn angle from `[-120, -90, -60, 60, 90, 120]` degrees.
   f. Set steering to chosen angle.
   g. Drive forward briefly for `abs(angle) / 120.0` seconds (proportional to turn sharpness).
   h. Set steering back to 0.
   i. Resume forward driving.
4. Slight speed variation (`±5%`) on each forward segment for natural movement.
5. Watchdog: If ultrasonic returns `None` (sensor failure), stop and retry.

**UI display during patrol:**
- Show patrol state badge: `FORWARD` / `AVOIDING` / `TURNING` / `IDLE`
- Show live ultrasonic distance reading
- Show obstacle event log (last 5 events with timestamps)

---

## 9. Electron UI Specification

### 9.1 Design Principles
- The UI is a **dumb passthrough**. It sends ROS2 messages and displays ROS2 topic data. Zero robot logic in the UI.
- All state in the UI is derived from ROS2 topic subscriptions.
- Connection loss to rosbridge = UI shows "Disconnected" and disables all controls.
- Dark theme, minimal, functional. No decorative elements.

### 9.2 Layout

```
┌─────────────────────────────────────────────────────┐
│  BTBG Control                        ● Connected     │  ← Title bar / status
├─────────────────────────────────────────────────────┤
│                                                     │
│  Mode: [ MANUAL ●──────────────────── PATROL ]      │  ← Mode toggle
│                                                     │
├────────────────────────┬────────────────────────────┤
│                        │                            │
│   DRIVE CONTROLS       │   TELEMETRY                │
│                        │                            │
│   Speed: [====70%===]  │   Ultrasonic: 45.3 cm      │
│                        │   Battery: 7.2V            │
│   [  ↑  ]              │   Patrol state: FORWARD    │
│ [←][■][→]              │                            │
│   [  ↓  ]              │   Obstacle log:            │
│                        │   12:34:01 — 14.2cm avoid  │
│   Space = E-STOP       │   12:33:47 — 11.8cm avoid  │
│                        │                            │
├────────────────────────┴────────────────────────────┤
│  Camera Servo  Pan: [════0°════]  Tilt: [════0°════] │  ← v1.0 (no live stream)
└─────────────────────────────────────────────────────┘
```

> **Note:** Camera servo controls are included in v1.0 for manual positioning, even though live camera streaming is a future feature. Useful for adjusting camera angle before starting patrol mode.

### 9.3 Connection Status
- **Green dot + "Connected"**: WebSocket open, heartbeat OK.
- **Yellow dot + "Connecting..."**: Attempting WebSocket connection.
- **Red dot + "Disconnected"**: WebSocket closed or failed. All controls disabled. Auto-retry every 3 seconds.

### 9.4 Keyboard Shortcuts
| Key | Action |
|---|---|
| `W` / `↑` | Forward |
| `S` / `↓` | Backward |
| `A` / `←` | Steer left |
| `D` / `→` | Steer right |
| `Space` | Emergency stop |
| `P` | Toggle patrol mode |
| `Esc` | Emergency stop + switch to manual |

### 9.5 Electron Main Process
- `electron/main.js` creates a `BrowserWindow` loading the React app (via Vite in dev, or built index.html in prod).
- `electron/preload.js` exposes a minimal `contextBridge` API if needed (not required for roslibjs WebSocket — it connects directly from the renderer process).
- Window size: 900×600 minimum, resizable.
- No native menus except File > Quit.

---

## 10. NPM Workflow

### 10.1 Root `package.json` Scripts

```json
{
  "name": "btbg",
  "version": "1.0.0",
  "scripts": {
    "btbg:start":   "node scripts/start_robot.js",
    "btbg:stop":    "node scripts/stop_robot.js",
    "btbg:deploy":  "node scripts/deploy.js",
    "btbg:logs":    "node scripts/tail_logs.js",
    "btbg:status":  "node scripts/status.js",
    "app":          "npm run dev --prefix app",
    "app:build":    "npm run build --prefix app",
    "app:electron": "npm run electron --prefix app",
    "setup":        "node scripts/setup_dev.js"
  },
  "devDependencies": {
    "node-ssh": "^13.0.0",
    "dotenv": "^16.0.0"
  }
}
```

> **Cross-platform note:** Scripts are written in Node.js using `node-ssh` for Windows/macOS/Linux compatibility. The shell script versions (`*.sh`) are also provided in `scripts/bash/` for Unix systems.

### 10.2 Script Details

**`npm run btbg:start`** (`scripts/start_robot.js`):
```javascript
// Cross-platform Node.js script using node-ssh
// - Loads PI_HOST and PI_USER from .env
// - SSHes into Pi and runs:
//     source /opt/ros/humble/setup.bash
//     source ~/btbg_ws/install/setup.bash
//     nohup ros2 launch btbg_nodes btbg.launch.py > ~/btbg_logs/ros.log 2>&1 &
// - Detaches process so it doesn't block the terminal
// - Waits 3 seconds, then checks if rosbridge port 9090 is listening
```

**`npm run btbg:stop`** (`scripts/stop_robot.js`):
```javascript
// - SSHes into Pi and runs:
//     pkill -f "ros2 launch"
//     pkill -f "btbg_nodes"
// - Runs Python one-liner to ensure motors stop:
//     python3 -c "from picarx import Picarx; Picarx().stop()"
```

**`npm run btbg:deploy`** (`scripts/deploy.js`):
```javascript
// - Uses node-ssh SFTP to sync robot/ directory to Pi:~/btbg_ws/src/btbg_nodes/
// - Then SSHes in and runs:
//     cd ~/btbg_ws && colcon build --packages-select btbg_nodes
// - Prints build output in real-time
```

**`npm run btbg:logs`** (`scripts/tail_logs.js`):
```javascript
// - SSHes into Pi and runs: tail -f ~/btbg_logs/ros.log
// - Streams output to local console in real-time
// - Ctrl+C to stop
```

**`npm run btbg:status`** (`scripts/status.js`):
```javascript
// - Checks if Pi is reachable (ping)
// - Checks if rosbridge port 9090 is open
// - Checks ROS2 node status via: ros2 node list
// - Prints summary: ✓ Pi reachable, ✓ rosbridge running, ✓ 4 nodes active
```

**`npm run app`**:
- Starts Vite dev server for React (port 5173)
- Starts Electron pointing at `localhost:5173`

### 10.3 `.env` File
```env
PI_HOST=btbg.local
PI_USER=pi
PI_SSH_KEY=~/.ssh/btbg_pi
ROS2_WS=/home/pi/btbg_ws
ROS_DISTRO=humble
ROSBRIDGE_PORT=9090
```

---

## 11. Network & SSH Setup

### 11.1 Pi Hostname
Set the Pi hostname to `btbg` so it's reachable as `btbg.local` on the local network via mDNS (avahi-daemon, enabled by default on Pi OS Bookworm).

```bash
# On the Pi:
sudo hostnamectl set-hostname btbg
sudo systemctl enable avahi-daemon
```

### 11.2 SSH Key Setup (no password)
```bash
# On developer machine:
ssh-keygen -t ed25519 -f ~/.ssh/btbg_pi -C "btbg robot key"
ssh-copy-id -i ~/.ssh/btbg_pi.pub pi@btbg.local
```

Then add to `~/.ssh/config`:
```
Host btbg
    HostName btbg.local
    User pi
    IdentityFile ~/.ssh/btbg_pi
    ServerAliveInterval 30
```

### 11.3 SSH Multiplexing (for fast repeated connections)
Add to `~/.ssh/config`:
```
Host btbg
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 60s
```
This means `npm run btbg:start` and `npm run btbg:stop` don't re-authenticate each time.

### 11.4 WiFi Configuration on Pi
Configure in `/etc/wpa_supplicant/wpa_supplicant.conf` or via Raspberry Pi Imager before flashing:
```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
network={
    ssid="YOUR_WIFI_SSID"
    psk="YOUR_WIFI_PASSWORD"
    key_mgmt=WPA-PSK
}
```

### 11.5 rosbridge Port Firewall
```bash
# On Pi — allow rosbridge port through firewall:
sudo ufw allow 9090/tcp
```

---

## 12. Environment Configuration

### 12.1 Pi First-Time Setup (`robot/setup.sh`)

**Prerequisites:** Flash Ubuntu 22.04 Server (64-bit) onto the Pi's SD card using Raspberry Pi Imager. Configure WiFi and enable SSH during imaging.

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

# Update OS
sudo apt update && sudo apt upgrade -y

# Install ROS2 Humble (official Ubuntu 22.04 method)
sudo apt install -y software-properties-common curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list
sudo apt update
sudo apt install -y ros-humble-ros-base python3-colcon-common-extensions python3-pip

# Install rosbridge and message types
sudo apt install -y ros-humble-rosbridge-suite ros-humble-sensor-msgs ros-humble-geometry-msgs

# Install SunFounder libraries (pinned versions)
pip3 install "picarx>=2.0.0,<3.0.0" "robot-hat>=2.0.0,<3.0.0"

# Install Python dependencies (pinned versions)
pip3 install "opencv-python-headless>=4.9.0,<5.0.0" "picamera2>=0.3.0,<1.0.0"

# Create ROS2 workspace
mkdir -p ~/btbg_ws/src
cd ~/btbg_ws
source /opt/ros/humble/setup.bash
colcon build

# Create log directory
mkdir -p ~/btbg_logs

# Add ROS2 to bashrc
echo "" >> ~/.bashrc
echo "# BTBG ROS2 setup" >> ~/.bashrc
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source ~/btbg_ws/install/setup.bash" >> ~/.bashrc

# Enable I2C (Ubuntu method)
sudo apt install -y i2c-tools
echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt
sudo usermod -aG i2c $USER

# Enable camera (Ubuntu method)
echo "start_x=1" | sudo tee -a /boot/firmware/config.txt
echo "gpu_mem=128" | sudo tee -a /boot/firmware/config.txt

echo ""
echo "=== Setup complete ==="
echo "Please reboot the Pi: sudo reboot"
echo "After reboot, run calibration: python3 -c \"from picarx import Picarx; px=Picarx(); px.forward(30)\""
```

### 12.1.1 `robot/requirements.txt` (Pinned Dependencies)
```
# SunFounder libraries
picarx>=2.0.0,<3.0.0
robot-hat>=2.0.0,<3.0.0

# Camera and vision
opencv-python-headless>=4.9.0,<5.0.0
picamera2>=0.3.0,<1.0.0

# Future: face recognition
# face-recognition>=1.3.0,<2.0.0
# dlib>=19.24.0,<20.0.0
```

### 12.2 ROS2 Launch File (`robot/launch/btbg.launch.py`)
```python
import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get the package share directory for config files
    pkg_share = get_package_share_directory('btbg_nodes')
    params_file = os.path.join(pkg_share, 'config', 'btbg_params.yaml')

    return LaunchDescription([
        # Hardware bridge (must start first — owns Picarx instance)
        Node(
            package='btbg_nodes',
            executable='hardware_bridge_node',
            name='hardware_bridge_node',
            output='screen',
            parameters=[params_file],
        ),
        # Sensor node
        Node(
            package='btbg_nodes',
            executable='sensor_node',
            name='sensor_node',
            output='screen',
            parameters=[params_file],
        ),
        # Car control (mode arbiter)
        Node(
            package='btbg_nodes',
            executable='car_control_node',
            name='car_control_node',
            output='screen',
            parameters=[params_file],
        ),
        # Patrol node (autonomous mode)
        Node(
            package='btbg_nodes',
            executable='patrol_node',
            name='patrol_node',
            output='screen',
            parameters=[params_file],
        ),
        # rosbridge WebSocket server
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge_websocket',
            parameters=[{'port': 9090}],
            output='screen',
        ),
    ])
```

### 12.3 ROS2 Parameters (`robot/config/btbg_params.yaml`)
```yaml
patrol_node:
  ros__parameters:
    patrol:
      speed: 30
      obstacle_threshold_cm: 25.0       # Increased for better stopping distance
      reverse_speed: 20
      reverse_duration_s: 0.5
      turn_duration_base_s: 0.8
      scan_interval_ms: 100
      turn_angles: [-120, -90, -60, 60, 90, 120]
      max_none_readings: 5              # Stop if ultrasonic fails this many times

car_control_node:
  ros__parameters:
    max_speed: 100
    min_speed: 15                       # Motors stall below this
    max_steering_angle: 40.0
    watchdog_timeout_ms: 1000           # Increased for WiFi reliability

hardware_bridge_node:
  ros__parameters:
    watchdog_timeout_ms: 1500           # Hardware-level safety timeout
    min_motor_speed: 15                 # Clamp speed above stall threshold

sensor_node:
  ros__parameters:
    ultrasonic_rate_hz: 10
    grayscale_rate_hz: 10
    battery_rate_hz: 0.5
    ultrasonic_max_range_cm: 300.0
    ultrasonic_min_range_cm: 2.0
    battery_low_warning_v: 7.0          # Warn UI when battery below this
```

---

## 13. Implementation Phases

### Phase 1 — Pi Setup & Hardware Verification ✅ Pre-code
- [ ] Flash Pi OS, set hostname to `btbg`, enable WiFi, SSH, I2C, camera
- [ ] Run `robot/setup.sh` to install ROS2 and dependencies
- [ ] Verify picarx works: run `python3 -c "from picarx import Picarx; px=Picarx(); px.forward(30)"` on Pi
- [ ] Calibrate servos using SunFounder calibration script
- [ ] Verify ultrasonic sensor returns valid readings

### Phase 2 — ROS2 Nodes (Robot Side)
- [ ] Create ROS2 package `btbg_nodes` with correct `package.xml` and `setup.py`
- [ ] Implement `sensor_node.py` — publish ultrasonic data, verify with `ros2 topic echo`
- [ ] Implement `hardware_bridge_node.py` — subscribe to drive topic, test motors
- [ ] Implement `car_control_node.py` — subscribe to cmd_vel, forward to hardware bridge
- [ ] Implement `patrol_node.py` — implement patrol algorithm, test without UI
- [ ] Create `btbg.launch.py` — launch all nodes + rosbridge
- [ ] Test: `ros2 launch btbg_nodes btbg.launch.py` runs without errors

### Phase 3 — Electron UI (Dev Machine Side)
- [ ] Scaffold Electron + React + Vite app in `app/`
- [ ] Implement `rosClient.js` — roslibjs singleton, connection state
- [ ] Implement `ConnectionStatus.jsx` — connected/disconnected indicator
- [ ] Implement `ModeToggle.jsx` — manual/patrol switch
- [ ] Implement `DriveControls.jsx` — D-pad buttons + keyboard handler
- [ ] Implement `SpeedSlider.jsx` — speed percentage control
- [ ] Implement `SensorDisplay.jsx` — ultrasonic readout, patrol state badge
- [ ] Implement `StatusBar.jsx` — mode, battery, connection info
- [ ] Wire keyboard shortcuts (WASD, Space, P, Esc)
- [ ] Test UI with Pi running: drive car from UI

### Phase 4 — NPM Workflow & Scripts
- [ ] Create root `package.json` with all scripts
- [ ] Write `scripts/start_robot.sh` — SSH + launch ROS2
- [ ] Write `scripts/stop_robot.sh` — SSH + kill nodes + stop motors
- [ ] Write `scripts/deploy.sh` — rsync + colcon build
- [ ] Test full workflow: `npm run btbg:start` → `npm run app` → drive car

### Phase 5 — Testing

#### 5.1 Unit Tests (no hardware required)
- [ ] `patrol_node` state machine logic: mock sensor data, verify state transitions
- [ ] `car_control_node` mode arbitration: verify commands routed correctly per mode
- [ ] Speed/steering scaling: verify -1.0 to 1.0 maps correctly to motor/servo values
- [ ] Watchdog timer logic: verify timeout triggers stop command

#### 5.2 Integration Tests (with hardware)
- [ ] Test manual drive: all 4 directions, steering, speed control
- [ ] Test emergency stop (Space key)
- [ ] Test patrol mode: activate, verify car roams and avoids obstacles
- [ ] Test mode switching mid-session (manual → patrol → manual)
- [ ] Test connection recovery: kill rosbridge, verify UI shows disconnected and reconnects
- [ ] Test watchdog: close UI while car is driving, verify car stops within 1500ms
- [ ] Range test: verify WebSocket works across the room (~10m WiFi range)
- [ ] Test graceful shutdown: Ctrl+C on ROS2 launch, verify motors stop
- [ ] Test low battery warning: verify UI displays warning when battery < 7.0V

#### 5.3 Stress Tests
- [ ] Rapid mode switching: toggle manual/patrol 20 times quickly
- [ ] Command flooding: send cmd_vel at 100Hz, verify no I2C errors
- [ ] Long-running patrol: let robot patrol for 10+ minutes, check for memory leaks

---

## 14. Error Handling & Recovery

### 14.1 Failure Modes and Responses

| Failure | Detection | Response |
|---------|-----------|----------|
| **WiFi disconnect** | rosbridge WebSocket closes | UI shows "Disconnected", auto-retry with exponential backoff (1s, 2s, 4s, max 5s). Robot continues last mode until hardware watchdog triggers. |
| **Ultrasonic sensor failure** | `None` readings for 5+ consecutive samples | `patrol_node` transitions to IDLE, publishes warning to `/btbg/status`. UI shows "Sensor Error" badge. |
| **hardware_bridge_node crash** | Process exit | `systemd` or launch file should restart it. Hardware watchdog (separate from node) would stop motors. |
| **I2C bus error** | `picarx` raises `IOError` | Log error, attempt retry after 100ms. After 3 failures, stop motors and publish error status. |
| **Low battery** | `sensor_node` reads < 7.0V | Publish warning to `/btbg/sensor/battery_warning`. UI shows low battery indicator. |
| **UI sends commands in wrong mode** | Mode mismatch in `car_control_node` | Commands silently ignored. UI should disable controls based on mode. |
| **rosbridge crash** | No heartbeat / connection refused | Other ROS2 nodes continue running. UI auto-reconnects when rosbridge restarts. |

### 14.2 Watchdog Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  Level 1: UI Watchdog (JavaScript)                          │
│  - If no sensor data received for 3s, show "No Telemetry"  │
│  - Auto-reconnect WebSocket                                 │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Level 2: car_control_node Watchdog (ROS2)                  │
│  - If no cmd_vel for 1000ms in manual mode, publish stop   │
│  - patrol_node has its own internal state machine          │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Level 3: hardware_bridge_node Watchdog (ROS2)              │
│  - If no /btbg/hw/drive for 1500ms, call px.stop()         │
│  - Last line of software defense                           │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Level 4: Graceful Shutdown Handler (Python signal)         │
│  - SIGTERM/SIGINT caught, px.stop() called before exit     │
│  - Prevents runaway motors on Ctrl+C                        │
└─────────────────────────────────────────────────────────────┘
```

### 14.3 Logging Strategy

**Log Locations on Pi:**
- `~/btbg_logs/ros.log` — Combined stdout/stderr from all ROS2 nodes (via launch file)
- `~/btbg_logs/ros.log.1`, `.2`, etc. — Rotated logs (logrotate configured in setup)

**Log Levels:**
- `DEBUG`: Sensor readings, every cmd_vel received
- `INFO`: Mode changes, patrol state transitions, connection events
- `WARN`: Sensor timeouts, low battery, retry events
- `ERROR`: I2C failures, node crashes, unhandled exceptions

**Viewing Logs:**
```bash
# From developer machine (via npm script):
npm run btbg:logs

# Or manually via SSH:
ssh btbg "tail -f ~/btbg_logs/ros.log"

# Filter by node:
ssh btbg "grep 'patrol_node' ~/btbg_logs/ros.log | tail -50"
```

---

## 15. Known Constraints & Gotchas

### Hardware
- **Single Picarx() instance:** The `picarx` library is NOT thread-safe. Only one node (`hardware_bridge_node`) should ever instantiate `Picarx()`. All other nodes request movement via ROS2 topics.
- **Servo calibration:** Steering servo zero-point varies per assembly. Must run `sudo python3 calibrate.py` from the picarx repo before first use. Calibration offsets saved to `robot/config/calibration.yaml`.
- **Ultrasonic noise:** The HC-SR04 returns `None` on read failure and spurious values > 300cm. Always filter these in `sensor_node.py`. Do not trigger obstacle avoidance on `None` readings.
- **Motor stall at low speeds:** PiCar-X motors stall below ~15% power. Never set speed below 15% in any mode. Default patrol speed of 30% is safe.
- **Battery voltage sag:** Motor speeds may behave differently at low battery (< 7.0V). Consider adding a low-battery warning in the UI.
- **I2C bus:** The Robot HAT uses I2C. Do not run other I2C devices on the same bus without checking for address conflicts.

### ROS2 / Software
- **Ubuntu 22.04 required:** We use Ubuntu 22.04 Server (not Pi OS) for official ROS2 Humble support. If you must use Pi OS, you'll need unofficial ROS2 builds or Docker.
- **rosbridge latency:** rosbridge adds ~5–20ms latency over a local WiFi network. Acceptable for manual control at 20Hz command rate. Not suitable for latency-critical applications.
- **`colcon build` is slow on Pi 5:** First build takes several minutes. Subsequent incremental builds are faster. Use `--packages-select btbg_nodes` to only rebuild the relevant package.
- **`source setup.bash` in SSH sessions:** Non-interactive SSH sessions don't load `.bashrc`. The start scripts must explicitly `source /opt/ros/humble/setup.bash` before running ROS2 commands.
- **Electron + roslibjs:** roslibjs connects from the Electron renderer process directly to `ws://btbg.local:9090`. No Electron main process involvement needed for WebSocket. Ensure `contextIsolation` is set appropriately in `BrowserWindow` webPreferences.
- **Node.js scripts require `node-ssh`:** Install root package dependencies with `npm install` before running `npm run btbg:*` commands.

### Networking
- **mDNS on Windows:** `btbg.local` resolution requires Bonjour (iTunes installs it) or mDNS service on Windows. Alternative: use the Pi's IP address directly in `.env`.
- **WiFi disconnection:** If the Pi's WiFi drops, the rosbridge WebSocket closes. The Electron UI must implement auto-reconnect with exponential backoff (cap at 5s retry interval).
- **Same network requirement:** The Electron app must be on the same WiFi network as the Pi. VPN or separate subnets will break mDNS resolution.

### Security
- **Unencrypted WebSocket:** rosbridge uses `ws://` (not `wss://`). Anyone on your local network can send commands to the robot. This is acceptable for home use but avoid public networks.
- **No authentication:** rosbridge has no built-in auth. For demos at public venues, consider adding a simple token check via a custom rosbridge filter or running on a mobile hotspot you control.
- **SSH key security:** Protect `~/.ssh/btbg_pi` — anyone with this key has full Pi access.

---

## 16. Future Features (Backlog)

These are planned but NOT part of v1.0. Document here so a coding agent can implement them in later phases.

### Facial Recognition Security Mode
- Use `face_recognition` Python library (built on dlib) on the Pi.
- In patrol mode, after each obstacle avoidance stop, capture a camera frame and check for known faces.
- Registered faces stored as 128-dimensional encodings in `config/known_faces.pkl`.
- Unknown face detected → publish to `/btbg/alert` topic → Electron UI shows alert popup.
- Future: send Telegram message with photo via `python-telegram-bot`.
- New ROS2 node: `face_recognition_node.py`
- New UI component: `AlertPanel.jsx`

### Camera Live Stream
- Use `picamera2` + `opencv` to encode frames as MJPEG.
- Stream via HTTP (simple Flask server on Pi, port 8080) — NOT via rosbridge (too slow for video).
- Electron UI embeds `<img src="http://btbg.local:8080/stream.mjpg">` in a camera panel.
- Camera pan/tilt servos already implemented in v1.0 via `/btbg/servo_cmd`.

### Voice Commands
- Use `vosk` (offline speech recognition, runs on Pi 5 8GB) for wake word + command detection.
- Wake word: "Hey BTBG"
- Commands: "go forward", "stop", "patrol", "come here"
- New ROS2 node: `voice_command_node.py`
- No UI changes needed — voice commands publish to existing topics.

### Emotion-Reactive Behaviour
- Camera + `deepface` or `mediapipe` face mesh for expression detection.
- Expressions mapped to car behaviours:
  - Smile → spin 360°, flash LEDs
  - Frown → slow retreat
  - Surprise → quick stop + honk
- New ROS2 node: `emotion_node.py`

### Environmental Heat Mapping
- Attach BME280 sensor (temperature + humidity + pressure) via I2C.
- Add to `sensor_node.py` — publish `/btbg/sensor/environment`.
- Track car position over time (dead reckoning from wheel encoder — requires hardware upgrade).
- Build 2D heat map of room, display in Electron UI as colour overlay.

### SLAM (Future Hardware Upgrade Required)
- Add RPLiDAR A1 or YDLIDAR X2 via USB.
- Add wheel encoders to rear motors (hardware mod).
- Install `slam_toolbox` ROS2 package.
- Run `slam_toolbox` online async mode during patrol.
- Visualise map in Electron UI using a 2D canvas drawing the occupancy grid from `/map` topic.

---

*End of MASTER_PLAN.md — Feed this entire file to any coding agent to get full project context.*