#!/usr/bin/env node
/**
 * Start BTBG on the Raspberry Pi.
 * Launches the Python WebSocket server (no ROS2 needed).
 *
 * Usage: npm run btbg:start
 */

const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const isLinux = process.platform === 'linux';
if (!isLinux) {
    console.log('\nThis script should be run ON the Raspberry Pi, not Windows.');
    console.log('   On Windows, run: npm run app\n');
    process.exit(1);
}

const REPO_ROOT = path.join(__dirname, '..');
const SERVER_DIR = path.join(REPO_ROOT, 'robot', 'server');
const LOG_DIR = path.join(process.env.HOME, 'btbg_logs');
const CONFIG_FILE = path.join(REPO_ROOT, 'robot', 'config', 'btbg_params.yaml');

function run(cmd, options = {}) {
    return execSync(cmd, { shell: '/bin/bash', encoding: 'utf8', ...options });
}

async function startRobot() {
    console.log('\nBTBG Starting...\n');

    // Check if already running
    try {
        const pgrep = run('pgrep -f "python3.*server.main"');
        if (pgrep.trim()) {
            console.log('Already running (PID:', pgrep.trim() + ')');
            console.log('  To restart: npm run btbg:stop && npm run btbg:start\n');
            showIP();
            return;
        }
    } catch (e) { /* not running, continue */ }

    // Check Python3
    try {
        run('python3 --version', { stdio: 'pipe' });
    } catch (e) {
        console.log('Python3 not found. Install it first.\n');
        process.exit(1);
    }

    // Check websockets module
    try {
        run('python3 -c "import websockets"', { stdio: 'pipe' });
    } catch (e) {
        console.log('Installing Python dependencies...');
        run(`pip3 install --user -r ${path.join(REPO_ROOT, 'robot', 'requirements.txt')}`, { stdio: 'inherit' });
    }

    // Create log dir
    if (!fs.existsSync(LOG_DIR)) {
        fs.mkdirSync(LOG_DIR, { recursive: true });
    }

    // Launch server
    console.log('Launching BTBG server...');

    const logFile = fs.openSync(path.join(LOG_DIR, 'btbg.log'), 'w');

    const configArg = fs.existsSync(CONFIG_FILE) ? `--config ${CONFIG_FILE}` : '';

    const child = spawn('/bin/bash', ['-c', `
        cd ${REPO_ROOT} &&
        python3 -m robot.server ${configArg} --port 9090
    `], {
        detached: true,
        stdio: ['ignore', logFile, logFile]
    });

    child.unref();

    // Wait for server
    process.stdout.write('   Waiting for server');
    let ready = false;
    for (let i = 0; i < 10; i++) {
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
        console.log('\nBTBG is running!\n');
        showIP();
    } else {
        console.log('\nTimeout waiting for server.');
        console.log('   Check logs: tail -f ~/btbg_logs/btbg.log\n');
    }
}

function showIP() {
    try {
        const ip = run("hostname -I | awk '{print $1}'").trim();
        console.log('-'.repeat(40));
        console.log(`Connect from Windows: edit .env and set`);
        console.log(`  PI_HOST=${ip}`);
        console.log(`Then run: npm run app`);
        console.log('-'.repeat(40) + '\n');
    } catch (e) { }
}

startRobot();
