# BTBG - PiCar Robot Control System

Raspberry Pi 5 robot car with an Electron control app.
Pi runs the WebSocket server, PC runs the UI to drive, steer, and calibrate.

---

## Quick Start

### On the Pi
```bash
cd ~/btbg_picar
npm run btbg:start
```

### On your PC
```bash
# Edit .env — set VITE_PI_HOST to the Pi's IP
npm run app
```

---

## Network Modes

### Home WiFi (Pi and PC on the same router)

1. Both devices connect to the same WiFi network
2. Find Pi's IP: run `hostname -I` on the Pi
3. Set `VITE_PI_HOST=<Pi IP>` in `.env`
4. SSH: `ssh yze@<Pi IP>`

### Outdoor / Hotspot Mode (no router needed)

The Pi creates its own WiFi network. Your laptop connects directly to it.

**Enable hotspot on the Pi:**
```bash
sudo nmcli device wifi hotspot ifname wlan0 ssid BTBG password btbg1234
```

**Connect from your laptop:**
1. Connect to the `BTBG` WiFi network (password: `btbg1234`)
2. SSH: `ssh yze@10.42.0.1`
3. Set `VITE_PI_HOST=10.42.0.1` in `.env` on your PC
4. Run `npm run app` on your PC

**Switch back to home WiFi from the Pi:**
```bash
sudo nmcli connection down Hotspot
sudo nmcli device wifi connect "YOUR_WIFI_SSID" password "YOUR_PASSWORD"
```

**Make hotspot start automatically on boot:**
```bash
sudo nmcli connection modify Hotspot connection.autoconnect yes
```

**Stop auto-starting hotspot:**
```bash
sudo nmcli connection modify Hotspot connection.autoconnect no
```

---

## Steering Calibration

If the wheels aren't straight when steering is at 0:

1. Click **Calibrate** in the app header
2. Click **Left** / **Right** buttons to nudge the steering 1 degree at a time
3. When wheels are perfectly straight, click **Set as Center**
4. Close the panel — the offset is saved and persists across restarts

---

## Project Structure

```
btbg/
  .env                  # Pi IP and port config
  package.json          # NPM scripts (btbg:start, btbg:stop, app, test)
  app/                  # Electron + React control UI
    src/
      components/       # React components (DriveControls, CalibrationPanel, etc.)
      ros/              # WebSocket client (rosClient.js)
  robot/                # Python server (runs on Pi)
    server/
      main.py           # WebSocket server + controller
      hardware.py       # PiCar-X hardware interface
      patrol.py         # Autonomous patrol state machine
    config/
      calibration.yaml  # Steering offset (persisted)
  scripts/              # NPM helper scripts
```

---

## Useful Commands

| Command | Where | What |
|---------|-------|------|
| `npm run btbg:start` | Pi | Start the robot server |
| `npm run btbg:stop` | Pi | Stop the robot server |
| `npm run btbg:status` | Pi | Check server status |
| `npm run btbg:logs` | Pi | Tail server logs |
| `npm run app` | PC | Launch control UI |
| `npm test` | PC | Run all tests |

---

## Troubleshooting

**App shows "Connecting..."**
- Check `VITE_PI_HOST` in `.env` matches the Pi's IP
- Make sure the server is running on the Pi: `npm run btbg:status`
- Make sure both devices are on the same network

**SSH times out**
- Try the IP directly: `ssh yze@<IP>` instead of `ssh yze@btbg.local`
- Check if Pi is on the network: `arp -a` or `ping <IP>`

**Pi not on WiFi after reboot**
- Plug in ethernet or connect a monitor+keyboard
- Check WiFi: `nmcli device status`
- Reconnect: `sudo nmcli device wifi connect "SSID" password "PASS"`

**Steering is off-center**
- Use the Calibrate button in the app to set the correct center offset
