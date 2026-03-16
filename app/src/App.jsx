import React, { useState, useEffect, useCallback } from 'react';
import { btbgClient } from './ros/rosClient';
import ConnectionStatus from './components/ConnectionStatus';
import ModeToggle from './components/ModeToggle';
import DriveControls from './components/DriveControls';
import SpeedSlider from './components/SpeedSlider';
import SensorDisplay from './components/SensorDisplay';
import ServoControls from './components/ServoControls';
import StatusBar from './components/StatusBar';
import CalibrationPanel from './components/CalibrationPanel';

function App() {
  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  // Robot state
  const [mode, setMode] = useState('manual');
  const [speed, setSpeed] = useState(50);
  const [sensorData, setSensorData] = useState({
    ultrasonic: 0,
    battery: 7.4,
    batteryWarning: false,
  });
  const [patrolStatus, setPatrolStatus] = useState({
    state: 'idle',
    distance: 0,
  });
  const [showCalibration, setShowCalibration] = useState(false);
  const [robotStatus, setRobotStatus] = useState({
    speed: 0,
    steering: 0,
    isMoving: false,
  });

  // Connect on mount
  useEffect(() => {
    const connect = async () => {
      setIsConnecting(true);
      try {
        await btbgClient.connect();
        setIsConnected(true);
        setIsConnecting(false);
      } catch (error) {
        console.error('Connection failed:', error);
        setIsConnected(false);
        setIsConnecting(false);
      }
    };

    // Listen for telemetry messages (single stream from server)
    btbgClient.onMessage('telemetry', (msg) => {
      if (msg.sensors) {
        setSensorData({
          ultrasonic: msg.sensors.ultrasonic,
          battery: msg.sensors.battery,
          batteryWarning: msg.sensors.batteryWarning,
        });
      }
      if (msg.status) {
        setRobotStatus(msg.status);
        if (msg.status.mode) setMode(msg.status.mode);
      }
      if (msg.patrol) {
        setPatrolStatus(msg.patrol);
      }
    });

    btbgClient.on('close', () => {
      setIsConnected(false);
      setIsConnecting(true);
    });

    btbgClient.on('connection', () => {
      setIsConnected(true);
      setIsConnecting(false);
    });

    connect();

    return () => {
      btbgClient.disconnect();
    };
  }, []);

  // Handle mode change
  const handleModeChange = useCallback((newMode) => {
    setMode(newMode);
    btbgClient.send('mode', { mode: newMode });
  }, []);

  // Handle emergency stop
  const handleEmergencyStop = useCallback(() => {
    btbgClient.send('stop');
    handleModeChange('manual');
  }, [handleModeChange]);

  return (
    <div className="h-screen flex flex-col bg-btbg-dark">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 bg-btbg-darker border-b border-btbg-accent">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold">BTBG Control</h1>
          <button
            onClick={() => setShowCalibration(true)}
            disabled={!isConnected}
            className="text-xs px-2 py-1 bg-btbg-accent rounded hover:bg-btbg-highlight
                       disabled:opacity-50 disabled:cursor-not-allowed"
            title="Calibrate steering"
          >
            Calibrate
          </button>
        </div>
        <ConnectionStatus
          isConnected={isConnected}
          isConnecting={isConnecting}
        />
      </header>

      {/* Mode Toggle */}
      <div className="px-4 py-3 bg-btbg-darker">
        <ModeToggle
          mode={mode}
          onChange={handleModeChange}
          disabled={!isConnected}
        />
      </div>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left Panel - Controls */}
        <div className="w-1/2 p-4 flex flex-col gap-4 border-r border-btbg-accent">
          <div className="text-sm font-semibold text-gray-400 uppercase">
            Drive Controls
          </div>

          <SpeedSlider
            value={speed}
            onChange={setSpeed}
            disabled={!isConnected || mode === 'patrol'}
          />

          <DriveControls
            speed={speed}
            disabled={!isConnected || mode === 'patrol'}
            onEmergencyStop={handleEmergencyStop}
          />

          <div className="text-xs text-gray-500 text-center">
            WASD or Arrow Keys to drive - Space = E-STOP
          </div>

          <ServoControls disabled={!isConnected} />
        </div>

        {/* Right Panel - Telemetry */}
        <div className="w-1/2 p-4 flex flex-col gap-4">
          <div className="text-sm font-semibold text-gray-400 uppercase">
            Telemetry
          </div>

          <SensorDisplay
            ultrasonic={sensorData.ultrasonic}
            battery={sensorData.battery}
            batteryWarning={sensorData.batteryWarning}
            patrolState={patrolStatus.state}
            isPatrolMode={mode === 'patrol'}
          />

          <StatusBar
            mode={mode}
            speed={robotStatus.speed}
            steering={robotStatus.steering}
            isMoving={robotStatus.isMoving}
          />
        </div>
      </main>

      {showCalibration && (
        <CalibrationPanel
          disabled={!isConnected}
          onClose={() => setShowCalibration(false)}
        />
      )}
    </div>
  );
}

export default App;
