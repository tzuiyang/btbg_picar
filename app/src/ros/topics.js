/**
 * BTBG Message Protocol Reference
 *
 * All messages are JSON over WebSocket on port 9090.
 *
 * CLIENT -> SERVER:
 *   { type: "drive",  speed: -1..1, steering: -1..1 }
 *   { type: "mode",   mode: "manual" | "patrol" }
 *   { type: "servo",  pan: -90..90, tilt: -35..35 }
 *   { type: "stop" }
 *
 * SERVER -> CLIENT:
 *   {
 *     type: "telemetry",
 *     sensors:  { ultrasonic: cm, battery: volts, batteryWarning: bool, grayscale: [l,c,r] },
 *     status:   { mode: str, speed: num, steering: num, isMoving: bool },
 *     patrol:   { state: str, isActive: bool, distance: cm, turnAngle: deg },
 *     hardware: { speed, steering, pan, tilt, isStopped, hardwareAvailable }
 *   }
 */

// This file is kept as protocol documentation.
// The old TOPICS export is no longer used.
export default {};
