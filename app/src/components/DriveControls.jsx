import React, { useState, useEffect, useCallback, useRef } from 'react';
import { btbgClient } from '../ros/rosClient';

function DriveControls({ speed, disabled, onEmergencyStop }) {
  const [activeKeys, setActiveKeys] = useState(new Set());
  const publishInterval = useRef(null);

  // Key mappings
  const keyMap = {
    'w': 'forward',
    'arrowup': 'forward',
    's': 'backward',
    'arrowdown': 'backward',
    'a': 'left',
    'arrowleft': 'left',
    'd': 'right',
    'arrowright': 'right',
    ' ': 'stop',
    'escape': 'estop',
  };

  // Calculate velocity from active keys
  const calculateVelocity = useCallback(() => {
    let linearX = 0;
    let angularZ = 0;

    if (activeKeys.has('forward')) linearX += 1;
    if (activeKeys.has('backward')) linearX -= 1;
    if (activeKeys.has('left')) angularZ += 1;
    if (activeKeys.has('right')) angularZ -= 1;

    // Scale by speed percentage
    linearX *= speed / 100;
    angularZ *= speed / 100;

    return { linearX, angularZ };
  }, [activeKeys, speed]);

  // Publish velocity
  const publishVelocity = useCallback(() => {
    if (disabled) return;

    const { linearX, angularZ } = calculateVelocity();

    btbgClient.send('drive', { speed: linearX, steering: angularZ });
  }, [calculateVelocity, disabled]);

  // Handle key down
  const handleKeyDown = useCallback((e) => {
    if (disabled) return;

    const key = e.key.toLowerCase();
    const action = keyMap[key];

    if (action === 'estop' || action === 'stop') {
      e.preventDefault();
      onEmergencyStop();
      setActiveKeys(new Set());
      return;
    }

    if (action && !activeKeys.has(action)) {
      e.preventDefault();
      setActiveKeys(prev => new Set([...prev, action]));
    }
  }, [activeKeys, disabled, onEmergencyStop]);

  // Handle key up
  const handleKeyUp = useCallback((e) => {
    const key = e.key.toLowerCase();
    const action = keyMap[key];

    if (action) {
      e.preventDefault();
      setActiveKeys(prev => {
        const next = new Set(prev);
        next.delete(action);
        return next;
      });
    }
  }, []);

  // Set up keyboard listeners
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [handleKeyDown, handleKeyUp]);

  // Publish at 20Hz when keys are active
  useEffect(() => {
    if (activeKeys.size > 0 && !disabled) {
      publishInterval.current = setInterval(publishVelocity, 50); // 20Hz
    } else {
      if (publishInterval.current) {
        clearInterval(publishInterval.current);
        // Send stop command when all keys released
        btbgClient.send('drive', { speed: 0, steering: 0 });
      }
    }

    return () => {
      if (publishInterval.current) {
        clearInterval(publishInterval.current);
      }
    };
  }, [activeKeys, disabled, publishVelocity]);

  // Handle button click
  const handleButtonDown = (action) => {
    if (disabled) return;
    setActiveKeys(prev => new Set([...prev, action]));
  };

  const handleButtonUp = (action) => {
    setActiveKeys(prev => {
      const next = new Set(prev);
      next.delete(action);
      return next;
    });
  };

  const isActive = (action) => activeKeys.has(action);

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Forward */}
      <button
        className={`control-btn ${isActive('forward') ? 'active' : ''}`}
        disabled={disabled}
        onMouseDown={() => handleButtonDown('forward')}
        onMouseUp={() => handleButtonUp('forward')}
        onMouseLeave={() => handleButtonUp('forward')}
        onTouchStart={() => handleButtonDown('forward')}
        onTouchEnd={() => handleButtonUp('forward')}
      >
        W
      </button>

      {/* Left, Stop, Right */}
      <div className="flex gap-2">
        <button
          className={`control-btn ${isActive('left') ? 'active' : ''}`}
          disabled={disabled}
          onMouseDown={() => handleButtonDown('left')}
          onMouseUp={() => handleButtonUp('left')}
          onMouseLeave={() => handleButtonUp('left')}
          onTouchStart={() => handleButtonDown('left')}
          onTouchEnd={() => handleButtonUp('left')}
        >
          A
        </button>

        <button
          className="control-btn bg-red-600 hover:bg-red-700"
          disabled={disabled}
          onClick={onEmergencyStop}
        >
          STOP
        </button>

        <button
          className={`control-btn ${isActive('right') ? 'active' : ''}`}
          disabled={disabled}
          onMouseDown={() => handleButtonDown('right')}
          onMouseUp={() => handleButtonUp('right')}
          onMouseLeave={() => handleButtonUp('right')}
          onTouchStart={() => handleButtonDown('right')}
          onTouchEnd={() => handleButtonUp('right')}
        >
          D
        </button>
      </div>

      {/* Backward */}
      <button
        className={`control-btn ${isActive('backward') ? 'active' : ''}`}
        disabled={disabled}
        onMouseDown={() => handleButtonDown('backward')}
        onMouseUp={() => handleButtonUp('backward')}
        onMouseLeave={() => handleButtonUp('backward')}
        onTouchStart={() => handleButtonDown('backward')}
        onTouchEnd={() => handleButtonUp('backward')}
      >
        S
      </button>
    </div>
  );
}

export default DriveControls;
