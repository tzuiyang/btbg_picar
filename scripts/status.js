#!/usr/bin/env node
/**
 * Check BTBG status locally on the Pi.
 *
 * Usage: npm run btbg:status
 * Run this ON the Raspberry Pi.
 */

const { execSync } = require('child_process');

// Check if running on Pi (Linux)
const isLinux = process.platform === 'linux';
if (!isLinux) {
    console.log('\n⚠️  This script should be run ON the Raspberry Pi, not Windows.\n');
    process.exit(1);
}

async function checkStatus() {
    console.log('\n🔍 BTBG Status Check\n');

    let allGood = true;

    // Check ROS2 installation
    console.log('📦 ROS2:');
    try {
        execSync('source /opt/ros/humble/setup.bash && ros2 --version', { shell: '/bin/bash', encoding: 'utf8' });
        console.log('   ✓ ROS2 Humble installed');
    } catch (e) {
        console.log('   ✗ ROS2 not found');
        allGood = false;
    }

    // Check rosbridge port
    console.log('\n🌐 rosbridge WebSocket:');
    try {
        const ss = execSync('ss -tlnp | grep 9090', { encoding: 'utf8' });
        if (ss.includes('9090')) {
            console.log('   ✓ Listening on port 9090');
        } else {
            throw new Error('not found');
        }
    } catch (e) {
        console.log('   ✗ Not listening on port 9090');
        allGood = false;
    }

    // Check ROS2 nodes
    console.log('\n🤖 ROS2 Nodes:');
    const nodes = ['hardware_bridge_node', 'sensor_node', 'car_control_node', 'patrol_node'];

    for (const node of nodes) {
        try {
            const result = execSync(`pgrep -f "${node}"`, { encoding: 'utf8' });
            if (result.trim()) {
                console.log(`   ✓ ${node} running (PID: ${result.trim()})`);
            } else {
                throw new Error('not running');
            }
        } catch (e) {
            console.log(`   ✗ ${node} not running`);
            allGood = false;
        }
    }

    // Check hardware
    console.log('\n🔌 Hardware:');
    try {
        const i2c = execSync('sudo i2cdetect -y 1 2>/dev/null | grep -q "14" && echo "found"', { shell: '/bin/bash', encoding: 'utf8' });
        if (i2c.includes('found')) {
            console.log('   ✓ Robot HAT detected on I2C');
        } else {
            throw new Error('not found');
        }
    } catch (e) {
        console.log('   ✗ Robot HAT not detected on I2C');
        allGood = false;
    }

    // Get Pi IP address
    console.log('\n📡 Network:');
    try {
        const ip = execSync("hostname -I | awk '{print $1}'", { encoding: 'utf8' }).trim();
        console.log(`   IP Address: ${ip}`);
        console.log(`   Connect UI to: ws://${ip}:9090`);
    } catch (e) {
        console.log('   Could not determine IP address');
    }

    // Summary
    console.log('\n' + '─'.repeat(40));
    if (allGood) {
        console.log('✓ All systems operational!\n');
    } else {
        console.log('⚠️  Some issues detected. Run: npm run btbg:start\n');
    }
}

checkStatus();
