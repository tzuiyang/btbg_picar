import React, { useState, useEffect, useCallback } from 'react';
import { btbgClient } from '../ros/rosClient';

function CalibrationPanel({ disabled, onClose }) {
  const [angle, setAngle] = useState(0);
  const [savedOffset, setSavedOffset] = useState(0);

  // Fetch current calibration on mount
  useEffect(() => {
    const handleCalibration = (msg) => {
      setSavedOffset(msg.steering_offset ?? 0);
      setAngle(msg.steering_offset ?? 0);
    };

    btbgClient.onMessage('calibration', handleCalibration);
    btbgClient.send('get_calibration');

    return () => {
      btbgClient.send('calibrate_steer', { angle: 0 });
    };
  }, []);

  const nudge = useCallback((direction) => {
    setAngle((prev) => {
      const next = Math.max(-20, Math.min(20, prev + direction));
      btbgClient.send('calibrate_steer', { angle: next });
      return next;
    });
  }, []);

  const handleSetCenter = useCallback(() => {
    setSavedOffset(angle);
    btbgClient.send('save_calibration', { steering_offset: angle });
  }, [angle]);

  const handleReset = useCallback(() => {
    setAngle(0);
    setSavedOffset(0);
    btbgClient.send('calibrate_steer', { angle: 0 });
    btbgClient.send('save_calibration', { steering_offset: 0 });
  }, []);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
      <div className="bg-btbg-darker border border-btbg-accent rounded-lg p-6 w-96 max-w-[90vw]">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold">Steering Calibration</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl leading-none"
          >
            &times;
          </button>
        </div>

        <p className="text-sm text-gray-400 mb-4">
          Nudge the steering until the wheels point perfectly straight,
          then click "Set as Center" to save.
        </p>

        {/* Nudge buttons */}
        <div className="flex items-center justify-center gap-6 mb-4">
          <button
            onClick={() => nudge(-1)}
            disabled={disabled || angle <= -20}
            className="w-20 h-16 bg-btbg-accent hover:bg-btbg-highlight rounded-lg
                       text-xl font-bold disabled:opacity-30 disabled:cursor-not-allowed"
          >
            &laquo; Left
          </button>

          <div className="text-center min-w-[80px]">
            <span className="font-mono text-3xl">{angle}&deg;</span>
          </div>

          <button
            onClick={() => nudge(1)}
            disabled={disabled || angle >= 20}
            className="w-20 h-16 bg-btbg-accent hover:bg-btbg-highlight rounded-lg
                       text-xl font-bold disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Right &raquo;
          </button>
        </div>

        {/* Saved offset */}
        <div className="text-sm text-gray-400 text-center mb-4">
          Saved offset: <span className="font-mono text-white">{savedOffset}&deg;</span>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleSetCenter}
            disabled={disabled}
            className="flex-1 py-2 bg-green-700 hover:bg-green-600 rounded font-semibold
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Set as Center
          </button>
          <button
            onClick={handleReset}
            disabled={disabled}
            className="flex-1 py-2 bg-btbg-accent hover:bg-btbg-highlight rounded font-semibold
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Reset to 0
          </button>
        </div>
      </div>
    </div>
  );
}

export default CalibrationPanel;
