#!/usr/bin/env node
/**
 * Setup development environment.
 *
 * Usage: npm run setup
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('\n🔧 BTBG Development Setup\n');

const rootDir = path.join(__dirname, '..');

// 1. Check/create .env
console.log('📋 Checking environment file...');
const envPath = path.join(rootDir, '.env');
const envExamplePath = path.join(rootDir, '.env.example');

if (!fs.existsSync(envPath)) {
    if (fs.existsSync(envExamplePath)) {
        fs.copyFileSync(envExamplePath, envPath);
        console.log('   ✓ Created .env from .env.example');
    } else {
        console.log('   ✗ .env.example not found!');
    }
} else {
    console.log('   ✓ .env already exists');
}

// 2. Install root dependencies
console.log('\n📦 Installing root dependencies...');
try {
    execSync('npm install', { cwd: rootDir, stdio: 'inherit' });
    console.log('   ✓ Root dependencies installed');
} catch (e) {
    console.log('   ✗ Failed to install root dependencies');
}

// 3. Install app dependencies
console.log('\n📦 Installing app dependencies...');
const appDir = path.join(rootDir, 'app');
try {
    execSync('npm install', { cwd: appDir, stdio: 'inherit' });
    console.log('   ✓ App dependencies installed');
} catch (e) {
    console.log('   ✗ Failed to install app dependencies');
}

// 4. Summary
console.log('\n' + '─'.repeat(50));
console.log('\n✓ Development environment setup complete!\n');
console.log('Next steps:');
console.log('  1. Edit .env with your Pi\'s hostname/IP');
console.log('  2. Set up your Raspberry Pi (see TODO.md Phase 2)');
console.log('  3. Deploy to Pi: npm run btbg:deploy');
console.log('  4. Start robot: npm run btbg:start');
console.log('  5. Launch UI: npm run app');
console.log('');
