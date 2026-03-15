#!/bin/bash
#
# BTBG Pi Setup Script (No ROS2 - pure Python)
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
    echo "WARNING: This script is meant for Raspberry Pi (ARM architecture)."
    echo "   Detected: $(uname -m)"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "[1/5] Updating system..."
sudo apt update && sudo apt upgrade -y

echo ""
echo "[2/5] Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv i2c-tools python3-smbus git

echo ""
echo "[3/5] Enabling I2C..."
sudo apt install -y i2c-tools
if [ -f /boot/firmware/config.txt ]; then
    if ! grep -q "dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null; then
        echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt
    fi
elif [ -f /boot/config.txt ]; then
    if ! grep -q "dtparam=i2c_arm=on" /boot/config.txt 2>/dev/null; then
        echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
    fi
fi
sudo usermod -aG i2c $USER 2>/dev/null || true

echo ""
echo "[4/5] Installing Python dependencies..."
cd "$(dirname "$0")/.."
pip3 install --user --break-system-packages -r robot/requirements.txt 2>/dev/null \
    || pip3 install --user -r robot/requirements.txt

echo ""
echo "[5/5] Installing Node.js (for npm scripts)..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
else
    echo "   Node.js already installed: $(node --version)"
fi

# Install npm dependencies
npm install

# Create log directory
mkdir -p ~/btbg_logs

echo ""
echo "=== Setup complete! ==="
echo ""
echo "REBOOT RECOMMENDED: sudo reboot"
echo ""
echo "After reboot, just run:"
echo "  cd btbg_picar"
echo "  npm run btbg:start"
echo ""
