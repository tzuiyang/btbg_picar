# BTBG - One-Shot Workflow TODO

> **Goal**: SSH to Pi → `npm run btbg:start` → go to PC → `npm run app` → control the car.
> No manual localStorage hacks, no mDNS issues, just works.

---

## Problem Analysis

The app currently defaults to `ws://btbg.local:9090` which fails because:
1. Windows mDNS (`btbg.local`) doesn't resolve reliably on this network
2. The `.env` file has stale values (`PI_USER=ubuntu`, ROS2 references)
3. Vite doesn't pass the root `.env` variables to the frontend
4. The CSP header in `index.html` hardcodes `ws://btbg.local:9090`
5. There are no frontend tests to verify connection logic

---

## Phase 1: Fix `.env` Configuration

### 1.1 Update `.env` with correct values
- [ ] Change `PI_HOST=btbg.local` → `PI_HOST=192.168.45.102`
- [ ] Change `PI_USER=ubuntu` → `PI_USER=yze`
- [ ] Remove `PI_SSH_KEY=~/.ssh/btbg_pi` (we use default `~/.ssh/id_ed25519`)
- [ ] Remove all ROS2 references (`ROS2_WS`, `ROS_DISTRO`)
- [ ] Rename `ROSBRIDGE_PORT` → `BTBG_PORT`
- [ ] Add `VITE_PI_HOST=${PI_HOST}` (Vite only exposes vars prefixed with `VITE_`)
- [ ] Add `VITE_BTBG_PORT=9090`

### 1.2 Update `.env.example` to match
- [ ] Mirror the new `.env` structure
- [ ] Add comments explaining each variable

**Verify**: `cat .env` shows no ROS2 references, correct IP and username.

---

## Phase 2: Wire `.env` to Vite Frontend

### 2.1 Update `app/vite.config.js`
- [ ] Add `envDir: path.resolve(__dirname, '..')` to point Vite at the root `.env`
- [ ] This makes `import.meta.env.VITE_PI_HOST` available in frontend code

### 2.2 Update CSP header in `app/index.html`
- [ ] Change `connect-src` from `ws://btbg.local:9090 ws://localhost:9090 ws://*:9090`
      to just `connect-src 'self' ws://*:9090` (allow any host on port 9090)

**Verify**: Run `npm run app`, open DevTools → Console, type `import.meta.env.VITE_PI_HOST` → should show `192.168.45.102`.

---

## Phase 3: Update `rosClient.js` Connection Logic

### 3.1 Fix URL resolution priority
- [ ] Update `_getWebSocketUrl()` to use this fallback chain:
      1. `import.meta.env.VITE_PI_HOST` (from `.env` via Vite) ← **new default**
      2. `localStorage.getItem('btbg_host')` (user override)
      3. `'btbg.local'` (last resort fallback)
- [ ] Same for port: `import.meta.env.VITE_BTBG_PORT` → localStorage → `'9090'`
- [ ] Remove the `process.env.BTBG_WS_URL` check (doesn't work in browser context)

### 3.2 Log the resolved URL on connect
- [ ] Add a `console.log` showing which source was used (env/localStorage/fallback)

**Verify**: App connects automatically without any localStorage hacks.

---

## Phase 4: Clean Up Stale References

### 4.1 Update `scripts/start_robot.js`
- [ ] Verify it still works with `yze` user and current directory structure
- [ ] Remove any ROS2 references if present

### 4.2 Update `scripts/setup_pi.sh`
- [ ] Remove ROS2 installation steps (no longer needed)
- [ ] Remove references to `ubuntu` user
- [ ] Keep: system deps, I2C setup, Python deps, Node.js

### 4.3 Update root `package.json`
- [ ] Remove `btbg:build` script (was for ROS2 colcon build, no longer needed)
- [ ] Verify remaining scripts work

### 4.4 Update `scripts/tail_logs.js`
- [ ] Change log filename from `ros.log` to `btbg.log`

**Verify**: `npm run btbg:start` on Pi, `npm run btbg:status` shows all green.

---

## Phase 5: Add Frontend Unit Tests

### 5.1 Set up test framework in `app/`
- [ ] Install vitest: `npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom`
- [ ] Add `test` script to `app/package.json`: `"test": "vitest run"`
- [ ] Add vitest config in `app/vite.config.js` (test environment: jsdom)

### 5.2 Test `rosClient.js` - URL Resolution (`app/src/ros/__tests__/rosClient.test.js`)
- [ ] Test: uses `VITE_PI_HOST` from env when available
- [ ] Test: falls back to localStorage when env not set
- [ ] Test: falls back to `btbg.local` when nothing is set
- [ ] Test: `setUrl()` updates localStorage and internal URL
- [ ] Test: port defaults to 9090

### 5.3 Test `rosClient.js` - Connection Lifecycle (`app/src/ros/__tests__/rosClient.test.js`)
- [ ] Test: `connect()` creates WebSocket with correct URL
- [ ] Test: `connect()` resolves on open
- [ ] Test: `connect()` rejects on timeout (5s)
- [ ] Test: `disconnect()` closes WebSocket and prevents reconnect
- [ ] Test: `isConnected()` returns true only when WebSocket is OPEN
- [ ] Test: auto-reconnect on close (up to 10 attempts)
- [ ] Test: exponential backoff delay capped at 5s

### 5.4 Test `rosClient.js` - Messaging (`app/src/ros/__tests__/rosClient.test.js`)
- [ ] Test: `send()` serializes `{ type, ...data }` as JSON
- [ ] Test: `send()` is no-op when disconnected
- [ ] Test: `onMessage()` routes messages by type to correct callback
- [ ] Test: `onMessage()` ignores messages with wrong type
- [ ] Test: invalid JSON from server doesn't crash

### 5.5 Test `rosClient.js` - Events (`app/src/ros/__tests__/rosClient.test.js`)
- [ ] Test: `on('connection')` fires on WebSocket open
- [ ] Test: `on('close')` fires on WebSocket close
- [ ] Test: `on('error')` fires on WebSocket error
- [ ] Test: `off()` removes handler correctly

### 5.6 Test React Components (`app/src/components/__tests__/`)

#### `ConnectionStatus.test.jsx`
- [ ] Test: shows "Connected" with green dot when `isConnected=true`
- [ ] Test: shows "Connecting..." with yellow dot when `isConnecting=true`
- [ ] Test: shows "Disconnected" with red dot when both false

#### `ModeToggle.test.jsx`
- [ ] Test: renders Manual and Patrol buttons
- [ ] Test: highlights active mode
- [ ] Test: calls onChange with new mode on click
- [ ] Test: buttons disabled when `disabled=true`

#### `SpeedSlider.test.jsx`
- [ ] Test: renders slider with current value
- [ ] Test: calls onChange when slider moves
- [ ] Test: displays percentage label
- [ ] Test: disabled when `disabled=true`

#### `DriveControls.test.jsx`
- [ ] Test: WASD keys send correct drive commands
- [ ] Test: Arrow keys send correct drive commands
- [ ] Test: Space key triggers emergency stop
- [ ] Test: key release sends stop (speed=0, steering=0)
- [ ] Test: drive commands scaled by speed percentage
- [ ] Test: no commands sent when disabled

#### `SensorDisplay.test.jsx`
- [ ] Test: displays ultrasonic distance with unit
- [ ] Test: red color when distance < 20cm
- [ ] Test: yellow color when distance < 40cm
- [ ] Test: green color when distance >= 40cm
- [ ] Test: displays battery voltage
- [ ] Test: shows LOW warning when batteryWarning=true

#### `ServoControls.test.jsx`
- [ ] Test: pan slider range -90 to 90
- [ ] Test: tilt slider range -35 to 35
- [ ] Test: reset button sets both to 0
- [ ] Test: no commands sent when disabled

---

## Phase 6: Add Python Server Tests

### 6.1 Verify existing tests pass
- [ ] Run `python -m pytest robot/test/ -v` on Pi (or locally in sim mode)
- [ ] Fix any failures

### 6.2 Add WebSocket integration test (`robot/test/test_websocket.py`)
- [ ] Test: server starts and accepts WebSocket connections
- [ ] Test: server responds to `drive` message (no crash)
- [ ] Test: server responds to `mode` message (mode changes)
- [ ] Test: server responds to `stop` message (stops motors)
- [ ] Test: server responds to `servo` message (no crash)
- [ ] Test: server broadcasts telemetry to connected clients
- [ ] Test: server handles invalid JSON gracefully
- [ ] Test: server handles unknown message types gracefully
- [ ] Test: server removes disconnected clients from broadcast set

### 6.3 Add config loading test (`robot/test/test_config.py`)
- [ ] Test: default config has all required keys
- [ ] Test: YAML override merges correctly
- [ ] Test: missing YAML file uses defaults

---

## Phase 7: Add `npm test` to Root

### 7.1 Add root test script
- [ ] Add `"test"` script to root `package.json`: runs both Python and JS tests
- [ ] Add `"test:app"` script: `npm test --prefix app`
- [ ] Add `"test:robot"` script: `python -m pytest robot/test/ -v`

**Verify**: `npm test` from root runs all tests and reports results.

---

## Phase 8: End-to-End Verification

### 8.1 Full workflow test (manual)
- [ ] On Pi: `npm run btbg:start` → server starts, shows IP
- [ ] On PC: verify `.env` has `PI_HOST=192.168.45.102`
- [ ] On PC: `npm run app` → Electron app launches
- [ ] App shows **Connected** (green dot) within 5 seconds
- [ ] WASD keys move the car
- [ ] Speed slider adjusts motor speed
- [ ] Servo sliders move the camera
- [ ] Mode toggle switches to patrol → car drives autonomously
- [ ] Emergency stop (Space) halts all movement
- [ ] Telemetry panel shows live ultrasonic readings
- [ ] Close app → reopen → auto-connects again

### 8.2 Failure scenarios
- [ ] Start app without Pi running → shows "Connecting..." and retries
- [ ] Kill Pi server while app is open → shows reconnecting, auto-reconnects when server restarts
- [ ] Wrong IP in `.env` → shows "Connecting..." (doesn't crash)

---

## File Change Summary

| File | Action | What Changes |
|------|--------|-------------|
| `.env` | Edit | Fix PI_HOST, PI_USER, remove ROS2, add VITE_ vars |
| `.env.example` | Edit | Mirror `.env` structure |
| `app/vite.config.js` | Edit | Add `envDir` pointing to root |
| `app/index.html` | Edit | Fix CSP connect-src |
| `app/src/ros/rosClient.js` | Edit | Use `import.meta.env.VITE_PI_HOST` as default |
| `app/package.json` | Edit | Add test script + test deps |
| `package.json` | Edit | Add test scripts, remove btbg:build |
| `scripts/setup_pi.sh` | Edit | Remove ROS2 steps |
| `scripts/tail_logs.js` | Edit | Fix log filename |
| `app/src/ros/__tests__/rosClient.test.js` | Create | WebSocket client tests |
| `app/src/components/__tests__/*.test.jsx` | Create | Component tests |
| `robot/test/test_websocket.py` | Create | Server integration tests |
| `robot/test/test_config.py` | Create | Config loading tests |