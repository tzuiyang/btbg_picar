#!/usr/bin/env node
/**
 * Check BTBG status locally on the Pi.
 *
 * Usage: npm run btbg:status
 */

const { execSync } = require('child_process');

const isLinux = process.platform === 'linux';
if (!isLinux) {
    console.log('\nThis script should be run ON the Raspberry Pi, not Windows.\n');
    process.exit(1);
}

async function checkStatus() {
    console.log('\nBTBG Status Check\n');

    let allGood = true;

    // Check Python server process
    console.log('Server:');
    try {
        const pgrep = execSync('pgrep -af "python3.*server"', { encoding: 'utf8' });
        if (pgrep.trim()) {
            console.log('   RUNNING');
        } else {
            throw new Error('not running');
        }
    } catch (e) {
        console.log('   NOT RUNNING');
        allGood = false;
    }

    // Check WebSocket port
    console.log('\nWebSocket:');
    try {
        const ss = execSync('ss -tlnp | grep 9090', { encoding: 'utf8' });
        if (ss.includes('9090')) {
            console.log('   Listening on port 9090');
        } else {
            throw new Error('not found');
        }
    } catch (e) {
        console.log('   Not listening on port 9090');
        allGood = false;
    }

    // Check hardware
    console.log('\nHardware (I2C):');
    try {
        const i2c = execSync('sudo i2cdetect -y 1 2>/dev/null | grep -q "14" && echo "found"', { shell: '/bin/bash', encoding: 'utf8' });
        if (i2c.includes('found')) {
            console.log('   Robot HAT detected');
        } else {
            throw new Error('not found');
        }
    } catch (e) {
        console.log('   Robot HAT not detected (may need sudo, or HAT not connected)');
        allGood = false;
    }

    // Network
    console.log('\nNetwork:');
    try {
        const ip = execSync("hostname -I | awk '{print $1}'", { encoding: 'utf8' }).trim();
        console.log(`   IP: ${ip}`);
        console.log(`   UI connects to: ws://${ip}:9090`);
    } catch (e) {
        console.log('   Could not determine IP');
    }

    // Summary
    console.log('\n' + '-'.repeat(40));
    if (allGood) {
        console.log('All systems operational!\n');
    } else {
        console.log('Issues detected. Run: npm run btbg:start\n');
    }
}

checkStatus();
