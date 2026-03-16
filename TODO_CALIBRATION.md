# Steering Calibration TODO

> **Goal**: Calibration panel with nudge buttons (not slider) to micro-adjust the steering
> servo until wheels are straight, then save as center offset. Offset persists across restarts.

---

## Root Cause: Why Nothing Moved

The Pi is running commit `6286e45` (old code). Our calibration handlers (`calibrate_steer`,
`save_calibration`, `get_calibration`) only exist locally. The Pi's server silently ignores
unknown message types. **We must push and deploy the new code to the Pi.**

---

## Phase 1: Deploy Code to Pi

### 1.1 Push local changes to GitHub
- [ ] Commit all changes (backend + frontend calibration code)
- [ ] Push to `main`

### 1.2 Pull on Pi and restart server
- [ ] SSH to Pi: `cd ~/btbg_picar && git pull`
- [ ] Stop old server: `npm run btbg:stop`
- [ ] Start new server: `npm run btbg:start`

### 1.3 Verify deployment
- [ ] SSH to Pi: check `grep calibrate_steer robot/server/main.py` returns matches
- [ ] App connects and calibration messages are handled

**Test**: Send `calibrate_steer` from app → Pi logs should show the handler firing.

---

## Phase 2: Redesign CalibrationPanel — Buttons Instead of Slider

Replace the slider with two nudge buttons (`<` and `>`) for precise 1-degree adjustments.

### 2.1 Rewrite `CalibrationPanel.jsx`
- [ ] Remove the `<input type="range">` slider
- [ ] Add two large buttons: `< Left` and `Right >` (each nudge by 1 degree)
- [ ] Display current angle prominently in the center between the buttons
- [ ] Keep "Set as Center" button (saves current angle as offset)
- [ ] Keep "Reset to 0" button (clears offset)
- [ ] On mount: fetch current offset via `get_calibration`
- [ ] On each button click: update angle ±1, send `calibrate_steer` with new angle
- [ ] Clamp angle to -20..+20 range
- [ ] On close: send `calibrate_steer` with angle 0 (reset servo to neutral)

### 2.2 UI Layout
```
┌──────────────────────────────────────┐
│  Steering Calibration          [X]   │
│                                      │
│  Nudge the steering until the        │
│  wheels point perfectly straight.    │
│                                      │
│   ┌──────┐              ┌──────┐     │
│   │  <<  │    +3 deg    │  >>  │     │
│   │ Left │              │Right │     │
│   └──────┘              └──────┘     │
│                                      │
│  Saved offset: +3 deg               │
│                                      │
│  [  Set as Center  ] [ Reset to 0 ]  │
└──────────────────────────────────────┘
```

### Tests after Phase 2:

#### `app/src/components/__tests__/CalibrationPanel.test.jsx` (rewrite)
- [ ] Test: renders Left and Right nudge buttons
- [ ] Test: clicking Right increments angle by 1 and sends `calibrate_steer`
- [ ] Test: clicking Left decrements angle by 1 and sends `calibrate_steer`
- [ ] Test: angle is clamped at +20 (clicking Right at 20 stays at 20)
- [ ] Test: angle is clamped at -20 (clicking Left at -20 stays at -20)
- [ ] Test: displays current angle between buttons
- [ ] Test: displays saved offset value
- [ ] Test: "Set as Center" sends `save_calibration` with current angle
- [ ] Test: "Reset to 0" sends both `calibrate_steer` and `save_calibration` with 0
- [ ] Test: sends `get_calibration` on mount
- [ ] Test: buttons are disabled when `disabled=true`
- [ ] Test: calls onClose when X button clicked

---

## Phase 3: Verify All Tests Pass

- [ ] Run `npm test` in `app/` → all frontend tests pass (including updated CalibrationPanel tests)
- [ ] Run `python -m pytest robot/test/test_calibration.py -v` → all 17 backend tests pass

---

## Phase 4: Deploy and E2E Test

- [ ] Commit, push, pull on Pi, restart server
- [ ] Open app → click Calibrate
- [ ] Click Right button multiple times → wheels turn right incrementally
- [ ] Click Left button multiple times → wheels turn left incrementally
- [ ] When wheels are straight → click "Set as Center"
- [ ] Close calibration → drive with WASD → wheels straight at rest
- [ ] Restart server on Pi → offset persists

---

## File Change Summary

| File | Action | What Changes |
|------|--------|-------------|
| `app/src/components/CalibrationPanel.jsx` | Rewrite | Buttons instead of slider |
| `app/src/components/__tests__/CalibrationPanel.test.jsx` | Rewrite | Tests for button-based UI |
| Pi: `~/btbg_picar` | Deploy | Pull latest code, restart server |
