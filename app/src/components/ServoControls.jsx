import React, { useState, useCallback } from 'react';
import { btbgClient } from '../ros/rosClient';

// Simple throttle function
function throttle(func, limit) {
  let lastCall = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastCall >= limit) {
      lastCall = now;
      func.apply(this, args);
    }
  };
}

function ServoControls({ disabled }) {
  const [pan, setPan] = useState(0);
  const [tilt, setTilt] = useState(0);

  // Throttle servo commands to 10Hz max
  const publishServo = useCallback(
    throttle((panAngle, tiltAngle) => {
      btbgClient.send('servo', { pan: panAngle, tilt: tiltAngle });
    }, 100),
    []
  );

  const handlePanChange = (e) => {
    const value = parseInt(e.target.value);
    setPan(value);
    publishServo(value, tilt);
  };

  const handleTiltChange = (e) => {
    const value = parseInt(e.target.value);
    setTilt(value);
    publishServo(pan, value);
  };

  const resetServos = () => {
    setPan(0);
    setTilt(0);
    publishServo(0, 0);
  };

  return (
    <div className="mt-4 p-3 bg-btbg-darker rounded-lg">
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm font-semibold text-gray-400 uppercase">
          Camera Servo
        </span>
        <button
          onClick={resetServos}
          disabled={disabled}
          className="text-xs px-2 py-1 bg-btbg-accent rounded hover:bg-btbg-highlight
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Reset
        </button>
      </div>

      <div className="space-y-2">
        {/* Pan */}
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-400 w-10">Pan:</label>
          <input
            type="range"
            min="-90"
            max="90"
            value={pan}
            onChange={handlePanChange}
            disabled={disabled}
            className="flex-1 h-2 bg-btbg-accent rounded-lg appearance-none cursor-pointer
                       disabled:opacity-50"
          />
          <span className="text-sm w-12 text-right font-mono">{pan}deg</span>
        </div>

        {/* Tilt */}
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-400 w-10">Tilt:</label>
          <input
            type="range"
            min="-35"
            max="35"
            value={tilt}
            onChange={handleTiltChange}
            disabled={disabled}
            className="flex-1 h-2 bg-btbg-accent rounded-lg appearance-none cursor-pointer
                       disabled:opacity-50"
          />
          <span className="text-sm w-12 text-right font-mono">{tilt}deg</span>
        </div>
      </div>
    </div>
  );
}

export default ServoControls;
