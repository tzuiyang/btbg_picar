#!/usr/bin/env node
/**
 * Build ROS2 workspace on the Pi.
 * Creates symlink from repo to ROS2 workspace and builds.
 *
 * Usage: npm run btbg:build
 * Run this ON the Raspberry Pi.
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Check if running on Pi (Linux)
const isLinux = process.platform === 'linux';
if (!isLinux) {
    console.log('\n⚠️  This script should be run ON the Raspberry Pi, not Windows.\n');
    process.exit(1);
}

const REPO_ROOT = path.join(__dirname, '..');
const ROS2_WS = process.env.ROS2_WS || path.join(process.env.HOME, 'btbg_ws');
const SRC_DIR = path.join(ROS2_WS, 'src');
const LINK_PATH = path.join(SRC_DIR, 'btbg_nodes');
const ROBOT_PATH = path.join(REPO_ROOT, 'robot', 'btbg_nodes');

console.log('\n📦 BTBG ROS2 Build\n');

// Create workspace if needed
if (!fs.existsSync(SRC_DIR)) {
    console.log(`Creating workspace: ${ROS2_WS}`);
    fs.mkdirSync(SRC_DIR, { recursive: true });
}

// Create symlink to robot code
console.log('🔗 Linking robot code to workspace...');
try {
    // Remove existing link/directory
    if (fs.existsSync(LINK_PATH)) {
        const stat = fs.lstatSync(LINK_PATH);
        if (stat.isSymbolicLink()) {
            fs.unlinkSync(LINK_PATH);
        } else {
            fs.rmSync(LINK_PATH, { recursive: true });
        }
    }

    // Create symlink
    fs.symlinkSync(ROBOT_PATH, LINK_PATH);
    console.log(`   ✓ ${LINK_PATH} -> ${ROBOT_PATH}`);
} catch (e) {
    console.error(`   ✗ Failed to create symlink: ${e.message}`);
    process.exit(1);
}

// Also link config and launch directories
const configSrc = path.join(REPO_ROOT, 'robot', 'config');
const configDst = path.join(LINK_PATH, 'config');
const launchSrc = path.join(REPO_ROOT, 'robot', 'launch');
const launchDst = path.join(LINK_PATH, 'launch');

try {
    if (!fs.existsSync(configDst)) {
        fs.symlinkSync(configSrc, configDst);
        console.log(`   ✓ config linked`);
    }
    if (!fs.existsSync(launchDst)) {
        fs.symlinkSync(launchSrc, launchDst);
        console.log(`   ✓ launch linked`);
    }
} catch (e) {
    // May already exist, that's fine
}

// Build
console.log('\n🔨 Building ROS2 package...\n');
try {
    execSync(`
        source /opt/ros/humble/setup.bash &&
        cd ${ROS2_WS} &&
        colcon build --packages-select btbg_nodes --symlink-install
    `, { shell: '/bin/bash', stdio: 'inherit' });

    console.log('\n✓ Build successful!\n');
    console.log('Run: npm run btbg:start\n');
} catch (e) {
    console.error('\n✗ Build failed\n');
    process.exit(1);
}
