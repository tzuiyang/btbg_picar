import React from 'react';

function StatusBar({ mode, speed, steering, isMoving }) {
  return (
    <div className="mt-auto p-3 bg-btbg-darker rounded-lg">
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Mode:</span>
          <span className="font-semibold uppercase">{mode}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Moving:</span>
          <span className={isMoving ? 'text-green-500' : 'text-gray-500'}>
            {isMoving ? 'Yes' : 'No'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Speed:</span>
          <span className="font-mono">{Math.abs(speed).toFixed(0)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Steering:</span>
          <span className="font-mono">{steering.toFixed(1)}deg</span>
        </div>
      </div>
    </div>
  );
}

export default StatusBar;
