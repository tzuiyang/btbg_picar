const { contextBridge } = require('electron');

// Expose a minimal API to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  version: process.env.npm_package_version || '1.0.0',
});

// Log when preload script runs
console.log('BTBG preload script loaded');
