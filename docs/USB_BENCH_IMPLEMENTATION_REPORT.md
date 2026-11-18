# USB bench configuration implementation report

Date: 18 November 2026. Base HEAD checked before editing: `e8243c8be7f88280ea5ef3a076574810bd5994e3`. Camera release `7835925` was already present. No physical device was opened or uploaded, and no GitHub push was performed.

## Behavior before and after

Before: LOW GPIO27 latched physical E-stop, preventing RESET/ARM/motor authorization. It did not prevent ultrasonic polling or TEL/DIST telemetry. The dashboard treated LOW feedback as unsafe and did not distinguish a deliberate no-motor bench build.

After: PROTECTED_ROVER remains the default, with the same active-HIGH feedback, falling-edge GPIO14 cut, latch/reset/arm sequence, PWM setup, enable protections, neutral time, manual timeout and autonomous sensor/navigation behavior. The explicit USB_BENCH_DIAGNOSTIC build keeps the real GPIO27 reading, boots disarmed, rejects ARM/AUTO/directions/cleaning ON and never configures or attaches LEDC motor PWM. Its adapter independently forces stop and GPIO14/16/17/18/19/21/22/23/25 LOW. Software STOP/ESTOP still latches; only explicit RESET while disarmed clears it, including when GPIO27 remains LOW. RESET never grants motor capability. Command silence cannot enable outputs.

All GPIO assignments and ultrasonic measurement/scheduler code are preserved. The camera firmware, pin mapping, HTTP/stream implementation, proxy and dashboard Camera component are unchanged. Legacy TEL fields/types remain; additive mode/motorCapable metadata lets the bridge/UI disable motor controls explicitly while retaining readiness, ranges, stop/disarm, ESTOP/RESET, diagnostics and independent camera use.

The handover PDF remains a frozen historical E2 artifact. Its checker now also validates the intentionally updated controller/configuration against that original software snapshot, as it already did for the adapter/generated sketch. Current electrical authorities, pin mapping, wiring and diagrams remain checked against current files; no physical acceptance criterion was relaxed.

## Files in the local change

- `README.md`
- `apps/rover-bridge/src/bridge.ts`
- `apps/rover-bridge/test/bench-integration.test.ts`
- `apps/rover-bridge/test/operating-mode.test.ts`
- `apps/rover-dashboard/src/App.tsx`
- `apps/rover-dashboard/src/navigation.ts`
- `apps/rover-dashboard/test/App.test.tsx`
- `docs/LAPTOP_CONTROL_SETUP.md`
- `docs/SERIAL_PROTOCOL.md`
- `docs/USB_BENCH_DIAGNOSTIC.md`
- `docs/USB_BENCH_IMPLEMENTATION_REPORT.md`
- `firmware/rover.ino`
- `include/rover_control.h`
- `include/rover_mode.h`
- `include/rover_telemetry.h`
- `packages/protocol/index.ts`
- `platformio.ini`
- `scripts/build_simulator.py`
- `scripts/check_team_handover.py`
- `scripts/package_main_arduino.py`
- `scripts/simulation/bench_serial.cpp`
- `scripts/sync_wokwi.py`
- `scripts/verify.py`
- `test/browser/bench.spec.ts`
- `test/stubs/Arduino.h`
- `test/test_bench/test_main.cpp`
- `test/test_io/test_main.cpp`
- `test/test_main_arduino_package.py`
- `wokwi/sketch.ino`

Security cleanup: `camera/include/secrets.h` is local-only and Git-ignored. Its accidental inclusion in the unpushed commit was removed by rewriting that commit and cleaning the affected local snapshot references. The working credential file is preserved byte-for-byte on disk; no credentials are reproduced in this report, logs or main-sketch packages. The unaffected parent commit and legitimate source changes are preserved. No GitHub push or firmware upload was performed.

## Automated results

| Check | Final result |
| --- | --- |
| Before-edit native baseline | 84/84 passed |
| Protected C++ controller / real firmware adapter / turning | 85/85 passed, including all original 84 plus LOW-feedback sensor polling |
| New diagnostic real-adapter host suite | 11/11 passed: boot, command rejection, ESTOP latch/RESET, GPIO27 changes, forced controller state, no PWM attachment/high writes, command loss/rollover, telemetry/ranges, overflow and buffer bounds |
| Native total after changes | 96/96 passed (`pio test -e native -e native_bench`) |
| Camera policy and real-handler host suites | Both passed via `python3 scripts/build_simulator.py` |
| Native simulation / bench serial harness build | Passed; bench harness uses actual firmware with synthetic ultrasonic echoes and GPIO/serial mocks |
| TypeScript/Vitest | 100/100 passed in 9 files (`npm test -- --maxWorkers=2`) |
| Python regression suite | 56/56 passed; the two package tests also passed after making package file writes explicitly UTF-8/LF for Windows portability |
| Bridge typecheck/build and dashboard typecheck/Vite build | Passed (`npm run build`) |
| Compiled production dashboard/asset/bridge API smoke | Passed on loopback; no device opened |
| Browser regressions | 8/8 passed, including existing manual/AUTO/lease/ESTOP/monitoring/camera tests and new bench controls/latch/sensors/mobile-layout test |
| PlatformIO esp32dev / usb_bench_diagnostic / wokwi_compile | All three compiled successfully; zero compiler warnings observed |
| Arduino IDE-compatible main packages | Both compiled using Arduino-ESP32 2.0.17 / ESP32 Dev Module, all warnings enabled; zero warnings |
| Source/pin/camera preservation | Hash checks passed; latest user-specified secrets.h bytes unchanged |
| Package verification | Both main ZIPs have exactly six matching source/config files, valid CRCs and no secret/camera/binary entries |
| Static / electrical / completion / system / frozen handover checks | Passed |
| Physical motor, sensor, video or radio acceptance | Not performed in this implementation; existing user reports are not presented as new measurements |

The initial unrestricted laptop run, launched during concurrent compilation, timed out in two handshake tests; both passed together in isolation and the complete 100-test run passed with two workers. The new browser test initially used an exact text locator that did not match the sensor DOM; it was corrected, and the final complete eight-test browser run passed. No unresolved automated failures remain. Playwright's environment emitted NO_COLOR/FORCE_COLOR notices; these are distinct from firmware compiler warnings.

Detailed captured results are in ignored `artifacts/usb-bench-diagnostic/`, including firmware/Arduino build logs, laptop/Python/browser logs, snapshots and preservation records. The physical USB was represented by host serial mocks; browser bench telemetry was a test fixture. Real USB enumeration alone was not treated as hardware testing.

## Verified flow boundaries

| Boundary | Evidence |
| --- | --- |
| Actual bench adapter -> TEL -> bridge | Host adapter integration completes readiness with LOW feedback and three synthetic echoes; ESTOP/RESET round-trip with no motor permission |
| Protected simulator -> bridge/WebSocket -> UI | Existing integration and browser suites retain arming, held movement, AUTO, stops and diagnostics |
| Diagnostic telemetry -> UI controls | Unit and browser tests show explicit no-motor banner, live distances, disabled motor controls and deliberate software latch reset |
| Camera proxy -> browser | Existing test-only multipart fixture decodes, downloads JPEG and disconnects; camera source/component hashes unchanged |
| Production build -> served UI/API | Built HTML, JavaScript asset and stopped/disarmed bridge API smoke passed |

## Selection, build and later upload from Windows

Use PlatformIO Core in PowerShell at the repository root:

```powershell
# Default production PROTECTED_ROVER
pio run -e esp32dev
# Explicit no-motor USB_BENCH_DIAGNOSTIC
pio run -e usb_bench_diagnostic
```

Only for a later deliberate manual upload after identifying the **main ESP32**, closing Mission Control/Serial Monitor, and disconnecting motor supplies/harnesses (replace COM7 with the actual port):

```powershell
pio run -e usb_bench_diagnostic -t upload --upload-port COM7
pio device monitor --port COM7 --baud 115200
```

The protected upload equivalent is `pio run -e esp32dev -t upload --upload-port COM7`; future motor-powered use still requires the separate hardware review. No upload command was executed here.

## Arduino IDE packages

A new **main** sketch package is needed for Arduino IDE; the independent camera ZIP is unchanged. Generated packages:

- Bench: `build/arduino/usb_bench_diagnostic/rover_main_usb_bench_diagnostic.zip`
- Protected: `build/arduino/protected_rover/rover_main_protected_rover.zip`

Each contains `rover_main.ino`, `rover_build_config.h`, `rover_mode.h`, `rover_control.h`, `rover_pins.h` and `rover_telemetry.h` in a `rover_main` directory. The selected mode is explicit in `rover_build_config.h`. Regenerate with `py -3 scripts/package_main_arduino.py --mode USB_BENCH_DIAGNOSTIC` or `--mode PROTECTED_ROVER`; the default is protected. PlatformIO needs no ZIP. Both packages were compiled, not uploaded.

Arduino IDE: install **esp32 by Espressif Systems 2.0.17**, extract the intended ZIP to its own directory, open `rover_main/rover_main.ino`, select **ESP32 Dev Module**, 240 MHz / DIO / 40 MHz / 4 MB / default partitions / PSRAM disabled, and click Verify. Select only the identified main-board COM port for a later manual Upload. Monitor at 115200 with newline. This is not the AI Thinker ESP32-CAM target.

## Wiring limits and unresolved blockers

The full [operating and wiring guide](USB_BENCH_DIAGNOSTIC.md) documents every labelled HW-039 terminal, protected R_EN/L_EN routing and bench inactive-state measurements with primary datasheet references. No direct 3.3 V drive into an unqualified 5 V HC244 receiver is approved; no enable or GPIO27 HIGH jumper substitutes for missing protection.

Independent cutoff/contactor/feedback hardware and external interface remain missing. Exact driver logic thresholds/defaults, power-rail/reset behavior, LiPo/protection/fuse/cable ratings, combined/stall motor currents and L298N load/thermal limits remain unresolved for motor power. Bench use requires physically disconnected motor supplies/loads/control harnesses. LOW GPIO measurements and reset/brownout captures have not been performed. Software ESTOP does not isolate the LiPo.
