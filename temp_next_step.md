# BTBG Setup Guide

## First Time Setup (Raspberry Pi)

### 1. Flash Ubuntu 22.04 to SD Card
- Download Ubuntu Server 22.04 LTS (64-bit) for Raspberry Pi
- Use Raspberry Pi Imager to flash to SD card
- Enable SSH and set WiFi credentials in imager settings

### 2. Boot and Connect
```bash
# Find Pi IP (check router or use nmap)
ssh ubuntu@<pi-ip>
# Default password: ubuntu (you'll be asked to change it)
```

### 3. Clone and Setup
```bash
git clone <your-repo-url> btbg
cd btbg
chmod +x scripts/setup_pi.sh
./scripts/setup_pi.sh
```

This will install:
- ROS2 Humble
- picarx and robot-hat libraries
- Node.js 20
- I2C tools
- All npm dependencies

### 4. Reboot
```bash
sudo reboot
```

---

## After Reboot (Every Time)

### On the Pi
```bash
cd btbg
npm run btbg:start
```

That's it. The script will:
- Create ROS2 workspace if needed
- Build the ROS2 package
- Launch all nodes
- Show the Pi's IP address

### On Windows
1. Edit `.env` file in the btbg folder:
   ```
   PI_HOST=<pi-ip-address>
   ```

2. Run the app:
   ```bash
   cd btbg
   npm run app
   ```

---

## Useful Commands

| Command | Description |
|---------|-------------|
| `npm run btbg:start` | Start robot (on Pi) |
| `npm run btbg:stop` | Stop robot (on Pi) |
| `npm run btbg:status` | Check if running (on Pi) |
| `npm run btbg:logs` | View live logs (on Pi) |
| `npm run app` | Start UI (on Windows) |

---

## Troubleshooting

### Can't connect from Windows?
- Check Pi IP is correct in `.env`
- Make sure rosbridge is running: `npm run btbg:status`
- Check firewall allows port 9090

### Robot not responding?
- Check I2C: `sudo i2cdetect -y 1`
- View logs: `npm run btbg:logs`

### Need to restart?
```bash
npm run btbg:stop
npm run btbg:start
```

---

## Hardware Checklist

Before first run, verify:
- [ ] PiCar-X assembled correctly
- [ ] Battery charged and connected
- [ ] Camera ribbon cable connected (if using camera)
- [ ] Robot HAT seated properly on GPIO
