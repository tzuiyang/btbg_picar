#!/usr/bin/env node
/**
 * Tail ROS2 logs locally on the Pi.
 *
 * Usage: npm run btbg:logs
 * Run this ON the Raspberry Pi.
 */

const { spawn } = require('child_process');
const path = require('path');

// Check if running on Pi (Linux)
const isLinux = process.platform === 'linux';
if (!isLinux) {
    console.log('\n⚠️  This script should be run ON the Raspberry Pi, not Windows.\n');
    process.exit(1);
}

const LOG_FILE = path.join(process.env.HOME, 'btbg_logs', 'ros.log');

console.log(`\n📜 Tailing ${LOG_FILE}...`);
console.log('   Press Ctrl+C to stop.\n');

const tail = spawn('tail', ['-f', LOG_FILE], { stdio: 'inherit' });

tail.on('error', (err) => {
    console.error('Failed to tail logs:', err.message);
    console.log('Make sure BTBG has been started at least once.\n');
});

process.on('SIGINT', () => {
    console.log('\n\n✓ Log tailing stopped.\n');
    process.exit(0);
});
