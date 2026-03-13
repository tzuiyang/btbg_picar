import React, { useState, useEffect, useCallback } from 'react';
import { rosClient } from './ros/rosClient';
import { TOPICS } from './ros/topics';
import ConnectionStatus from './components/ConnectionStatus';
import ModeToggle from './components/ModeToggle';
import DriveControls from './components/DriveControls';
import SpeedSlider from './components/SpeedSlider';
import SensorDisplay from './components/SensorDisplay';
import ServoControls from './components/ServoControls';
import StatusBar from './components/StatusBar';

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
  const [robotStatus, setRobotStatus] = useState({
    speed: 0,
    steering: 0,
    isMoving: false,
  });

  // Connect to ROS on mount
  useEffect(() => {
    const connect = async () => {
      setIsConnecting(true);
      try {
        await rosClient.connect();
        setIsConnected(true);
        setIsConnecting(false);

        // Subscribe to topics
        rosClient.subscribe(TOPICS.SENSOR_ULTRASONIC, (msg) => {
          setSensorData(prev => ({ ...prev, ultrasonic: msg.range * 100 }));
        });

        rosClient.subscribe(TOPICS.SENSOR_BATTERY, (msg) => {
          setSensorData(prev => ({ ...prev, battery: msg.data }));
        });

        rosClient.subscribe(TOPICS.SENSOR_BATTERY_WARNING, (msg) => {
          setSensorData(prev => ({ ...prev, batteryWarning: msg.data }));
        });

        rosClient.subscribe(TOPICS.PATROL_STATUS, (msg) => {
          try {
            const status = JSON.parse(msg.data);
            setPatrolStatus(status);
          } catch (e) {
            console.error('Failed to parse patrol status:', e);
          }
        });

        rosClient.subscribe(TOPICS.STATUS, (msg) => {
          try {
            const status = JSON.parse(msg.data);
            setRobotStatus(status);
            if (status.mode) setMode(status.mode);
          } catch (e) {
            console.error('Failed to parse status:', e);
          }
        });

      } catch (error) {
        console.error('Connection failed:', error);
        setIsConnected(false);
        setIsConnecting(false);
      }
    };

    connect();

    // Handle disconnection
    rosClient.on('close', () => {
      setIsConnected(false);
      setIsConnecting(true);
      // Auto-reconnect after 3 seconds
      setTimeout(connect, 3000);
    });

    return () => {
      rosClient.disconnect();
    };
  }, []);

  // Handle mode change
  const handleModeChange = useCallback((newMode) => {
    setMode(newMode);
    rosClient.publish(TOPICS.MODE, { data: newMode });
  }, []);

  // Handle emergency stop
  const handleEmergencyStop = useCallback(() => {
    rosClient.publish(TOPICS.HW_STOP, {});
    handleModeChange('manual');
  }, [handleModeChange]);

  return (
    <div className="h-screen flex flex-col bg-btbg-dark">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 bg-btbg-darker border-b border-btbg-accent">
        <h1 className="text-xl font-bold">BTBG Control</h1>
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
    </div>
  );
}

export default App;
