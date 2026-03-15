#!/usr/bin/env node
/**
 * Stop BTBG server on the Pi.
 *
 * Usage: npm run btbg:stop
 */

const { execSync } = require('child_process');

const isLinux = process.platform === 'linux';
if (!isLinux) {
    console.log('\nThis script should be run ON the Raspberry Pi, not Windows.\n');
    process.exit(1);
}

async function stopRobot() {
    console.log('\nStopping BTBG...\n');

    // Stop motors first (safety)
    console.log('Stopping motors...');
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
    } catch (e) { }

    // Kill server process
    console.log('Stopping server...');
    const killCmds = [
        'pkill -f "python3.*server.main"',
        'pkill -f "python3 -m robot.server"',
    ];

    for (const cmd of killCmds) {
        try {
            execSync(cmd);
        } catch (e) { }
    }

    await new Promise(r => setTimeout(r, 1000));

    try {
        const check = execSync('pgrep -f "server.main"', { encoding: 'utf8' });
        if (check.trim()) {
            console.log('\nSome processes may still be running. PIDs:', check.trim());
            console.log('   Try: pkill -9 -f "server.main"\n');
            return;
        }
    } catch (e) { }

    console.log('\nAll BTBG processes stopped.\n');
}

stopRobot();
