#!/bin/bash
#
# BTBG Pi Setup Script
# Run this ONCE after cloning the repo on your Raspberry Pi.
#
# Usage: chmod +x scripts/setup_pi.sh && ./scripts/setup_pi.sh
#

set -e

echo ""
echo "=== BTBG Raspberry Pi Setup ==="
echo ""

# Check if running on Pi
if [[ "$(uname -m)" != "aarch64" && "$(uname -m)" != "armv7l" ]]; then
    echo "⚠️  This script is meant for Raspberry Pi (ARM architecture)."
    echo "   Detected: $(uname -m)"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Ubuntu version
if ! grep -q "22.04" /etc/os-release 2>/dev/null; then
    echo "⚠️  This script expects Ubuntu 22.04. Detected:"
    cat /etc/os-release | grep PRETTY_NAME
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "[1/7] Updating system..."
sudo apt update && sudo apt upgrade -y

echo ""
echo "[2/7] Installing ROS2 Humble prerequisites..."
sudo apt install -y software-properties-common curl gnupg lsb-release

echo ""
echo "[3/7] Adding ROS2 repository..."
if [ ! -f /usr/share/keyrings/ros-archive-keyring.gpg ]; then
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        -o /usr/share/keyrings/ros-archive-keyring.gpg
fi

if [ ! -f /etc/apt/sources.list.d/ros2.list ]; then
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
        http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
        | sudo tee /etc/apt/sources.list.d/ros2.list
fi

echo ""
echo "[4/7] Installing ROS2 Humble..."
sudo apt update
sudo apt install -y ros-humble-ros-base python3-colcon-common-extensions python3-pip

echo ""
echo "[5/7] Installing ROS2 packages..."
sudo apt install -y ros-humble-rosbridge-suite ros-humble-sensor-msgs ros-humble-geometry-msgs ros-humble-std-msgs

echo ""
echo "[6/7] Installing SunFounder PiCar-X libraries..."
pip3 install --user "picarx>=2.0.0,<3.0.0" "robot-hat>=2.0.0,<3.0.0"
pip3 install --user "opencv-python-headless>=4.9.0,<5.0.0"

echo ""
echo "[7/7] Setting up environment..."

# Create workspace
mkdir -p ~/btbg_ws/src
mkdir -p ~/btbg_logs

# Add ROS2 to bashrc
if ! grep -q "ROS2 setup" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# ROS2 setup" >> ~/.bashrc
    echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
    echo "source ~/btbg_ws/install/setup.bash 2>/dev/null || true" >> ~/.bashrc
fi

# Enable I2C
echo ""
echo "[Extra] Enabling I2C..."
sudo apt install -y i2c-tools python3-smbus
if ! grep -q "dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null; then
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt
fi
sudo usermod -aG i2c $USER

# Install Node.js if not present
if ! command -v node &> /dev/null; then
    echo ""
    echo "[Extra] Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
fi

# Install npm dependencies
echo ""
echo "[Final] Installing npm dependencies..."
cd "$(dirname "$0")/.."
npm install

echo ""
echo "=== Setup complete! ==="
echo ""
echo "REBOOT REQUIRED: sudo reboot"
echo ""
echo "After reboot, just run:"
echo "  cd btbg"
echo "  npm run btbg:start"
echo ""
