# Mission Control drive-control repair

The laptop software now runs Offline Simulator independently of ESP32 firmware
configuration and resets the control session when its source changes. No firmware
or commissioning settings were changed by this repair.

## Findings and changes

- The old simulator spawned `build/rover-sim`, a POSIX C++ program. The local
  executable is macOS Mach-O and cannot run on the Windows Dell. It also depends
  on firmware headers. `apps/rover-bridge/src/simulator.ts` replaces that runtime
  dependency with a virtual Node controller. Its telemetry explicitly identifies
  `fw:rover-sim-v1`, `mode:SIMULATION`, and `simulated:true`; it has no serial
  transport or commissioning record.
- The dashboard displayed controls from the connected bridge session, with no
  source-match gate or explanation of disabled controls. Selecting a different
  source now releases a held direction, disconnects the old session, clears its
  telemetry, waits for the transport to close, and requires Connect and ARM again.
  The Drive panel explains each unavailable state. Merely selecting Offline
  Simulator is insufficient: it needs its own connected session and explicit ARM.
- The bridge registered pending commands after writing them, and reset the line
  buffer after dispatch. Immediate/reentrant acknowledgements could consequently
  leave a command pending or corrupt a parsed line. Both operations now happen
  before dispatch. Physical sessions reject explicitly simulated telemetry.
- Firmware permission checks remain unchanged. MOTOR_OPERATION requires fresh
  protocol-v1 telemetry, the initial DISARM acknowledgement and stopped/disarmed
  handshake, `motorCapable:true`, `commissioningReady:true`, `inhibit:NONE`, and
  a clear software E-stop. Directional control additionally requires armed MANUAL.
  `motorCapable:true` alone grants no drive permission. Bench firmware still
  cannot run motors; PROTECTED_ROVER feedback requirements remain unchanged.

Production files changed: `apps/rover-bridge/src/{bridge,transports,simulator}.ts`,
`apps/rover-dashboard/src/App.tsx`, and `packages/protocol/index.ts`. Regression
tests cover virtual ARM/directions/timeouts, keyboard hold/release, source changes,
serial-close ordering, source mismatch, immediate ACKs, and WebSocket routing to a
COM7 mock with both permitted and inhibited firmware reports. Setup instructions
are updated in `docs/LAPTOP_CONTROL_SETUP.md`.

## Restart on the Dell G15

1. Use the updated project files on the Dell; changes on this Mac do not update
   that computer automatically. Stop the existing Mission Control server with
   Ctrl+C. Close Arduino/PlatformIO Serial Monitor so COM7 has one owner.
2. In a terminal at the Dell's project root, with Node 22.12 or newer:

   ```sh
   npm run build
   npm start
   ```

   If dependencies have not been installed, run `npm ci` first. No native
   simulator build or ESP32 upload is required for this repair.
3. Open `http://127.0.0.1:8787`, hard-refresh with Ctrl+F5, and keep one operator
   tab open. Choose **Offline simulator**, **Clear path**, then **Connect rover**.
   Wait for **Protocol ready** and synthetic telemetry. Click **ARM**, wait for
   the direction buttons to enable, then hold W/S/A/D or a direction button.
   Release must return requested/applied motion to STOPPED. ARM alone stays stopped.
4. Change the source to **Main ESP32 · USB serial**. The simulator disconnects;
   ARM and drive remain disabled. Choose **COM7** and **Connect rover**. The new
   connection starts with S/DISARM, never simulated ARM or direction commands.
   Verify the actual firmware permission fields above before explicitly arming.
   If it reports COMMISSIONING_REQUIRED, the Drive panel preserves that inhibit.
   Editing a local header does not change telemetry from already-flashed firmware.

## Verification limits

Bridge/dashboard builds and the production smoke check pass. The unit/integration
suite passes 134 tests, including host-firmware interlock regressions. All ten browser
tests pass, exercising the dashboard, simulated driving, source switching, and camera and
motor-status fixtures. Results are stored under `artifacts/drive-control-fix/`.

COM7 routing was tested with a mock serial device; this Mac cannot observe or
verify the Dell's physical motor outputs. Hash checks confirm all 29 recorded
firmware/header/camera/credential items, including the user's existing edit to
`include/rover_commissioning.h`, remain unchanged. No upload, push or physical
motor operation was performed.
