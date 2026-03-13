#!/usr/bin/env node
/**
 * Stop ROS2 nodes locally on the Pi.
 *
 * Usage: npm run btbg:stop
 * Run this ON the Raspberry Pi.
 */

const { execSync } = require('child_process');

// Check if running on Pi (Linux)
const isLinux = process.platform === 'linux';
if (!isLinux) {
    console.log('\n⚠️  This script should be run ON the Raspberry Pi, not Windows.\n');
    process.exit(1);
}

async function stopRobot() {
    console.log('\n🛑 Stopping BTBG...\n');

    // Stop motors first (safety)
    console.log('🔧 Stopping motors...');
    try {
        execSync(`python3 -c "
try:
    from picarx import Picarx
    px = Picarx()
    px.stop()
    print('   Motors stopped')
except Exception as e:
    print(f'   Motor stop skipped: {e}')
"`, { stdio: 'inherit' });
    } catch (e) {
        // Ignore if picarx not available
    }

    // Kill ROS2 processes
    console.log('🔧 Stopping ROS2 nodes...');

    const killCmds = [
        'pkill -f "ros2 launch btbg_nodes"',
        'pkill -f "btbg_nodes"',
        'pkill -f "rosbridge_websocket"',
    ];

    for (const cmd of killCmds) {
        try {
            execSync(cmd);
        } catch (e) {
            // Ignore if process not found
        }
    }

    // Verify stopped
    await new Promise(r => setTimeout(r, 1000));

    try {
        const check = execSync('pgrep -f "btbg_nodes"', { encoding: 'utf8' });
        if (check.trim()) {
            console.log('\n⚠️  Some processes may still be running. PIDs:', check.trim());
            console.log('   Try: pkill -9 -f btbg_nodes\n');
            return;
        }
    } catch (e) {
        // No processes found, good
    }

    console.log('\n✓ All BTBG processes stopped.\n');
}

stopRobot();
