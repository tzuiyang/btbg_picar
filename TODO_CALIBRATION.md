# Steering Calibration Fix — Persist Offset on Panel Close

> **Bug**: Closing the calibration panel sends `calibrate_steer` with `angle: 0`,
> which calls `set_raw_steering(0)` — setting the servo to raw 0 degrees (no offset).
> The wheels jump back off-center even though the offset was saved.
>
> **Fix**: On close, send a normal `drive` command with `speed: 0, steering: 0`.
> This flows through `drive()` → `set_dir_servo_angle(0 + steering_offset)`,
> positioning the wheels at the calibrated center.

---

## Phase 1: Fix the Cleanup in CalibrationPanel.jsx

### 1.1 Change the useEffect cleanup
- [ ] Replace `btbgClient.send('calibrate_steer', { angle: 0 })` with
      `btbgClient.send('drive', { speed: 0, steering: 0 })`
- [ ] This ensures the servo moves to `0 + offset` (calibrated center) on close

### Tests:

#### Update `CalibrationPanel.test.jsx`
- [ ] Test: on unmount, sends `drive` with `{ speed: 0, steering: 0 }` (not `calibrate_steer`)

---

## Phase 2: Verify Drive Applies Offset Correctly

### 2.1 Confirm the backend flow
- [ ] `drive` message with `steering: 0` → `handle_drive()` → `hw.drive(0, 0)`
      → `set_dir_servo_angle(0 + steering_offset)` — wheels at calibrated center
- [ ] `drive` message with `steering: 0.5` → steering = `0.5 * 40 = 20`
      → `set_dir_servo_angle(20 + offset)` — correctly offset from center

### Tests (already covered in test_calibration.py):
- [x] `test_offset_positive_shifts_angle` — drive(50, 0) with offset=5 → servo at 5
- [x] `test_drive_uses_offset_after_save` — save offset=5, drive steering=0 → servo at 5

---

## Phase 3: Run All Tests, Deploy

- [ ] Run `npx vitest run` in app/ → all pass
- [ ] Run `python -m pytest robot/test/test_calibration.py` → all pass
- [ ] Commit, push, pull on Pi, restart server
- [ ] E2E: calibrate → set center → close → wheels stay straight

---

## File Changes

| File | Change |
|------|--------|
| `app/src/components/CalibrationPanel.jsx` | Line 19: `calibrate_steer` → `drive` |
| `app/src/components/__tests__/CalibrationPanel.test.jsx` | Verify cleanup sends `drive` |
