import React from 'react';

function SensorDisplay({ ultrasonic, battery, batteryWarning, patrolState, isPatrolMode }) {
  // Color code ultrasonic based on distance
  const getDistanceColor = (dist) => {
    if (dist < 20) return 'text-red-500';
    if (dist < 40) return 'text-yellow-500';
    return 'text-green-500';
  };

  // Color code battery
  const getBatteryColor = (v) => {
    if (v < 6.5) return 'text-red-500';
    if (v < 7.0) return 'text-yellow-500';
    return 'text-green-500';
  };

  // Patrol state badge color
  const getPatrolStateColor = (state) => {
    switch (state) {
      case 'forward': return 'bg-green-600';
      case 'reversing': return 'bg-yellow-600';
      case 'turning': return 'bg-blue-600';
      case 'idle': return 'bg-gray-600';
      default: return 'bg-gray-600';
    }
  };

  return (
    <div className="space-y-3">
      {/* Ultrasonic */}
      <div className="flex justify-between items-center p-3 bg-btbg-darker rounded-lg">
        <span className="text-gray-400">Ultrasonic</span>
        <span className={`font-mono text-lg ${getDistanceColor(ultrasonic)}`}>
          {ultrasonic.toFixed(1)} cm
        </span>
      </div>

      {/* Battery */}
      <div className="flex justify-between items-center p-3 bg-btbg-darker rounded-lg">
        <span className="text-gray-400">Battery</span>
        <div className="flex items-center gap-2">
          {batteryWarning && (
            <span className="text-xs text-red-500 animate-pulse">LOW!</span>
          )}
          <span className={`font-mono text-lg ${getBatteryColor(battery)}`}>
            {battery.toFixed(2)}V
          </span>
        </div>
      </div>

      {/* Patrol State (only show in patrol mode) */}
      {isPatrolMode && (
        <div className="flex justify-between items-center p-3 bg-btbg-darker rounded-lg">
          <span className="text-gray-400">Patrol State</span>
          <span className={`px-3 py-1 rounded-full text-sm font-semibold uppercase ${getPatrolStateColor(patrolState)}`}>
            {patrolState}
          </span>
        </div>
      )}
    </div>
  );
}

export default SensorDisplay;
