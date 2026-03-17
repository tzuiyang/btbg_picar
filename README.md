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

### Hotspot Mode (default — no router needed)

The Pi automatically starts its own `BTBG` WiFi network on boot.
Your laptop connects directly to it. No router required.

**Default behavior:** Pi boots → `BTBG` hotspot is active → connect and go.

**Connect from your laptop:**
1. Connect to the `BTBG` WiFi network
   - If Windows asks for a PIN, click **"Connect using a password instead"**
   - Password: `BtbgCar2024`
2. SSH: `ssh yze@10.42.0.1`
3. Set `VITE_PI_HOST=10.42.0.1` in `.env` on your PC
4. Run `npm run app` on your PC

**Editing code on the Pi (no internet needed):**
While on the Pi's hotspot, you can SSH in and edit code directly:
```bash
ssh yze@10.42.0.1
cd ~/btbg_picar
# edit files, restart server, etc.
```

**Switch to home WiFi (when you need internet on the Pi):**
```bash
sudo nmcli connection down Hotspot
sudo nmcli device wifi connect "YOUR_WIFI_SSID" password "YOUR_PASSWORD"
```

**Switch back to hotspot:**
```bash
sudo nmcli connection up Hotspot
```

**Disable hotspot auto-start (if you want WiFi by default instead):**
```bash
sudo nmcli connection modify Hotspot connection.autoconnect no
```

**Re-enable hotspot auto-start:**
```bash
sudo nmcli connection modify Hotspot connection.autoconnect yes connection.autoconnect-priority 100
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

**Pi not reachable after reboot**
- By default the Pi starts in hotspot mode — connect to the `BTBG` WiFi and SSH to `10.42.0.1`
- If hotspot isn't showing, plug in a monitor+keyboard and check: `nmcli device status`

**Need internet on the Pi (git pull, apt install, etc.)**
- Switch to home WiFi: `sudo nmcli connection down Hotspot && sudo nmcli device wifi connect "SSID" password "PASS"`
- Switch back when done: `sudo nmcli connection up Hotspot`

**Steering is off-center**
- Use the Calibrate button in the app to set the correct center offset
