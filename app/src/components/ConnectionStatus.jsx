import React from 'react';

function ConnectionStatus({ isConnected, isConnecting }) {
  let statusClass = 'disconnected';
  let statusText = 'Disconnected';

  if (isConnected) {
    statusClass = 'connected';
    statusText = 'Connected';
  } else if (isConnecting) {
    statusClass = 'connecting';
    statusText = 'Connecting...';
  }

  return (
    <div className="flex items-center gap-2">
      <div className={`status-dot ${statusClass}`}></div>
      <span className="text-sm">{statusText}</span>
    </div>
  );
}

export default ConnectionStatus;
