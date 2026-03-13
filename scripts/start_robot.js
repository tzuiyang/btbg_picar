#!/usr/bin/env node
/**
 * Start BTBG on the Raspberry Pi.
 * Handles all setup automatically - just run this!
 *
 * Usage: npm run btbg:start
 */

const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Check if running on Pi (Linux)
const isLinux = process.platform === 'linux';
if (!isLinux) {
    console.log('\n⚠️  This script should be run ON the Raspberry Pi, not Windows.');
    console.log('   On Windows, run: npm run app\n');
    process.exit(1);
}

const REPO_ROOT = path.join(__dirname, '..');
const ROS2_WS = process.env.ROS2_WS || path.join(process.env.HOME, 'btbg_ws');
const SRC_DIR = path.join(ROS2_WS, 'src');
const LINK_PATH = path.join(SRC_DIR, 'btbg_nodes');
const ROBOT_PATH = path.join(REPO_ROOT, 'robot', 'btbg_nodes');
const LOG_DIR = path.join(process.env.HOME, 'btbg_logs');

function run(cmd, options = {}) {
    return execSync(cmd, { shell: '/bin/bash', encoding: 'utf8', ...options });
}

async function startRobot() {
    console.log('\n🤖 BTBG Starting...\n');

    // Check if already running
    try {
        const pgrep = run('pgrep -f "ros2 launch btbg_nodes"');
        if (pgrep.trim()) {
            console.log('✓ Already running (PID:', pgrep.trim() + ')');
            console.log('  To restart: npm run btbg:stop && npm run btbg:start\n');
            showIP();
            return;
        }
    } catch (e) { /* not running, continue */ }

    // Check ROS2 installed
    try {
        run('source /opt/ros/humble/setup.bash && ros2 --version', { stdio: 'pipe' });
    } catch (e) {
        console.log('✗ ROS2 not installed. Run the setup script first:');
        console.log('  chmod +x scripts/setup_pi.sh && ./scripts/setup_pi.sh\n');
        process.exit(1);
    }

    // Create directories
    if (!fs.existsSync(SRC_DIR)) {
        console.log('📁 Creating ROS2 workspace...');
        fs.mkdirSync(SRC_DIR, { recursive: true });
    }
    if (!fs.existsSync(LOG_DIR)) {
        fs.mkdirSync(LOG_DIR, { recursive: true });
    }

    // Setup symlink if needed
    if (!fs.existsSync(LINK_PATH)) {
        console.log('🔗 Linking robot code...');
        fs.symlinkSync(ROBOT_PATH, LINK_PATH);
    }

    // Link config and launch if needed
    const configDst = path.join(LINK_PATH, 'config');
    const launchDst = path.join(LINK_PATH, 'launch');
    if (!fs.existsSync(configDst)) {
        fs.symlinkSync(path.join(REPO_ROOT, 'robot', 'config'), configDst);
    }
    if (!fs.existsSync(launchDst)) {
        fs.symlinkSync(path.join(REPO_ROOT, 'robot', 'launch'), launchDst);
    }

    // Build ROS2 package
    console.log('📦 Building ROS2 package...');
    try {
        run(`
            source /opt/ros/humble/setup.bash &&
            cd ${ROS2_WS} &&
            colcon build --packages-select btbg_nodes --symlink-install 2>&1
        `, { stdio: 'inherit' });
    } catch (e) {
        console.error('\n✗ Build failed\n');
        process.exit(1);
    }

    // Launch ROS2
    console.log('\n🚀 Launching...');

    const logFile = fs.openSync(path.join(LOG_DIR, 'ros.log'), 'w');

    const child = spawn('/bin/bash', ['-c', `
        source /opt/ros/humble/setup.bash &&
        source ${ROS2_WS}/install/setup.bash &&
        ros2 launch btbg_nodes btbg.launch.py
    `], {
        detached: true,
        stdio: ['ignore', logFile, logFile]
    });

    child.unref();

    // Wait for rosbridge
    process.stdout.write('   Waiting for rosbridge');
    let ready = false;
    for (let i = 0; i < 15; i++) {
        await new Promise(r => setTimeout(r, 1000));
        process.stdout.write('.');
        try {
            const ss = run('ss -tlnp 2>/dev/null | grep 9090');
            if (ss.includes('9090')) {
                ready = true;
                break;
            }
        } catch (e) { /* not ready yet */ }
    }

    console.log('');

    if (ready) {
        console.log('\n✓ BTBG is running!\n');
        showIP();
    } else {
        console.log('\n⚠️  Timeout waiting for rosbridge.');
        console.log('   Check logs: tail -f ~/btbg_logs/ros.log\n');
    }
}

function showIP() {
    try {
        const ip = run("hostname -I | awk '{print $1}'").trim();
        console.log('─'.repeat(40));
        console.log(`Connect from Windows: edit .env and set`);
        console.log(`  PI_HOST=${ip}`);
        console.log(`Then run: npm run app`);
        console.log('─'.repeat(40) + '\n');
    } catch (e) { }
}

startRobot();
