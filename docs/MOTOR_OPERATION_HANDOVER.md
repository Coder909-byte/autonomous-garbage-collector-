# MOTOR_OPERATION implementation and handover

18 November 2026. Audited starting HEAD: `bfc06ed8a5c88302b835828901ff1813225501f0`, the credential-cleaned local commit. No camera source, GPIO assignment, sensor measurement timing, working secrets or physical device was changed. No firmware upload, Git commit or GitHub push was performed in this implementation.

## Three milestones

| Milestone | Result |
| --- | --- |
| Motor-capable software implementation | Complete: commands, PWM, direction interlock, shared enable, cleaning, AUTO, heartbeat timeout, telemetry and Mission Control support are implemented and exercised with host GPIO/serial mocks |
| Actual hardware electrically qualified | **NO.** Required driver interface, protected/disconnectable motor supply, fail-off behavior and current/thermal evidence are missing |
| Physical motor movement verified | **NO.** No real motor, battery or physical commissioning test was performed |

**The delivered MOTOR_OPERATION build cannot currently energize motors:** its commissioning record truthfully remains incomplete, ARM is rejected, PWM requests are clamped to zero and GPIO14/auxiliary outputs remain LOW. This is a conditional motor-capable implementation, not a permanent diagnostic-only mode: after genuine electrical qualification and explicit release-record review, the same motor path supports drive/cleaning without requiring GPIO27. Do not change the record merely to suppress the blocker.

The user's existing working Dell USB telemetry, three ultrasonic readings and independent camera/video integrations are preserved as reported context; automated tests here do not constitute fresh physical acceptance.

## Audit and exact firmware behavior

The previous protected firmware used GPIO27 for boot/ISR/loop emergency latching, RESET/ARM authorization and final driver-enable permission. Ultrasonic acquisition and telemetry were not blocked by LOW GPIO27. USB_BENCH_DIAGNOSTIC deliberately rejected all motor commands and never attached PWM. The current implementation keeps both behaviors.

New constants identify MOTOR_OPERATION, whether physical feedback is required, motor capability and whether the release record permits outputs. Only PROTECTED_ROVER requires GPIO27 and attaches its falling-edge safety ISR. `healthy()` still reads the actual input in every mode, with INPUT_PULLDOWN; no code writes/spoofs it HIGH. In MOTOR_OPERATION the controller authorization input reflects PWM/controller readiness rather than pretending physical feedback is installed.

`rover_commissioning.h` requires all six conditions plus a nonempty retained evidence identifier: driver interface, motor-power protection, independent supply disconnect, fail-off behavior, supply/common-ground/backfeed qualification, and motor-current/thermal qualification. All are false in the supplied record. This is a visible compile-time release attestation, not runtime hardware detection or a serial/dashboard bypass. The positive-path native fixture is explicitly rejected when Arduino/ESP32 hardware macros are present.

Both the controller and GPIO adapter check output permission. The adapter also clamps direct PWM requests in an unreleased MOTOR_OPERATION build. For a released build, existing 1200 Hz / 8-bit LEDC is used with the unchanged map:

| Request | GPIO16 left RPWM | GPIO17 left LPWM | GPIO18 right RPWM | GPIO19 right LPWM |
| --- | --- | --- | --- | --- |
| F | 150 | 0 | 150 | 0 |
| B | 0 | 150 | 0 | 150 |
| L: left reverse / right forward | 0 | 140 | 140 | 0 |
| R: left forward / right reverse | 140 | 0 | 0 | 140 |
| Stop / disarmed / inhibited | 0 | 0 | 0 | 0 |

A direction change first sets GPIO14 LOW and channels zero, observes the existing 100 ms neutral interval, prepares the selected PWM and then asserts enable. Opposing channels are not commanded together. ARM alone never starts motion. Physical forward direction still requires actual motor-lead/polarity validation; PWM duties are not measured wheel speed.

Brush GPIO21/22 and conveyor GPIO23/25 retain their separate ON/OFF requests, fixed reverse inputs LOW, and existing forward-motion-only application. Cleaning is suppressed while stopped/turning/reversing and is cleared by disarm/ESTOP/command expiry. GPIO14 remains shared across both BTS R_EN/L_EN pairs and L298N ENA/ENB through the qualified interface described in the wiring document.

Normal S stops and exits AUTO without latching. STOP/ESTOP latch and disarm. Explicit software RESET while disarmed does not require GPIO27 in MOTOR_OPERATION and cannot satisfy commissioning or restore motion. The original protected RESET still requires healthy physical feedback, and bench remains incapable of motor output.

MOTOR_OPERATION additionally requires accepted serial commands within 1200 ms, including during AUTO. The serial bridge sends internal HEARTBEAT every 200 ms while protocol telemetry is fresh. A missing command stream disarms/clears outputs; invalid lines cannot refresh it, and later heartbeat traffic does not rearm. Browser disconnect retains the existing stop/disarm behavior. Protected/bench firmware and bridge traffic retain their original behavior; this does not add an AUTO link watchdog to PROTECTED_ROVER.

## Preserved integrations and display

All 16 GPIO assignments are unchanged. Sensor code still uses TRIG 32/33/13, ECHO 34/35/36, 2 us LOW / 10 us HIGH triggering, one attempt per 65 ms and a maximum 25 ms pulseIn wait. The three-sensor navigation thresholds, timing, neutral interval, turning and sensor-fault logic are unchanged.

TEL remains protocol v1 with the same existing field types and actual GPIO27 value. MOTOR_OPERATION adds `commissioningReady` and `inhibit`; older v1 and the existing modes remain accepted. The parser rejects contradictory release/output claims. Mission Control retains its layout, camera component, sensor readings and serial handshake while adding explicit operating mode and motor-output state: DISARMED, ARMED, INHIBITED or COMMANDED ACTIVE. Its MOTOR_OPERATION banner distinguishes release-record status from physical power isolation. GPIO27 LOW can coexist with commanded outputs only in an explicitly released MOTOR_OPERATION frame, never by weakening protected telemetry rules. No encoder/physical-movement claim was added.

Camera firmware, pins, private configuration, ZIP, HTTP endpoints, MJPEG implementation, proxy and dashboard Camera component are preserved by hash checks. Camera regression tests use explicit test fixtures, not a claim of new real video acceptance. Credentials remain ignored and untracked; no package includes them.

## Configuration selection and Windows commands

PlatformIO Core, PowerShell, repository root; the pinned espressif32@6.12.0 framework is Arduino-ESP32 2.0.17:

```powershell
# Original protected production default:
pio run -e esp32dev
# Existing permanently no-motor USB diagnostics:
pio run -e usb_bench_diagnostic
# New motor-capable configuration, currently commissioning-inhibited:
pio run -e motor_operation
```

A future reviewed release requires real electrical evidence and an updated `include/rover_commissioning.h` record, followed by rebuilding. No GPIO27 jumper, enable-HIGH jumper, dashboard control, timeout or automatic fallback can replace that process.

For a later deliberate **main ESP32** upload, close Mission Control/Serial Monitor, identify the actual main-board COM port in Device Manager, and use a verified single-source detached programming setup with motor supplies/loads disconnected. COM7 below is a placeholder, not an identified port. Do not select the ESP32-CAM.

```powershell
pio run -e motor_operation -t upload --upload-port COM7
pio device monitor --port COM7 --baud 115200
```

Use `-e esp32dev` or `-e usb_bench_diagnostic` in the upload command to select the other configurations. A successful upload of the currently inhibited motor build is not an electrical release or an instruction to connect the LiPo. No upload command was executed by this implementation.

## Arduino IDE package

A fresh main-controller ZIP was generated at `build/arduino/motor_operation/rover_main_motor_operation.zip`. Updated protected and bench packages are under their corresponding build/arduino directories. Each contains exactly seven source files: `rover_main.ino`, `rover_build_config.h`, `rover_commissioning.h`, `rover_mode.h`, `rover_control.h`, `rover_pins.h`, `rover_telemetry.h`. None contains credentials, camera firmware or compiled binaries. The camera ZIP is unchanged.

Regenerate on Windows with `py -3 scripts/package_main_arduino.py --mode MOTOR_OPERATION` (macOS: python3). Default export selection remains PROTECTED_ROVER. Extract the intended ZIP into its own folder; open `rover_main/rover_main.ino`; confirm its mode in `rover_build_config.h` and the unreleased commissioning record. Use **esp32 by Espressif Systems 2.0.17**, **ESP32 Dev Module**, 240 MHz CPU, DIO / 40 MHz / 4 MB flash, default partitions and PSRAM disabled, matching the existing main target. Click Verify. Only later, under the detached preparation above, select the identified main COM port and click Upload. Monitor at 115200 with newline and close it before Mission Control reconnects. The new MOTOR_OPERATION package was compiled with Arduino CLI and zero warnings; all three main profiles were also compiled with PlatformIO.

## Exact electrical handover

[Motor-operation wiring](MOTOR_OPERATION_WIRING.md) supplies both complete 12-terminal BTS7960 tables, the explicit GPIO14 -> external U1 pin 11 -> U1 pin 9 -> all six enable inputs path, U1 input/output/power pins, L298N connections, buck/ESP32/motor-power requirements, every enable-state limitation and primary datasheet references. Candidate missing parts are marked BLOCKED, not represented as installed. The original E2 protected topology is unchanged.

Current motor power cannot be released with the verified inventory. Minimum missing remedies/evidence are a qualified HC244-compatible interface and fail-off defaults, rated battery/branch protection and independent DC disconnect/harness, actual combined/stall-current and thermal data, and measured logic/buck/reset/brownout/backfeed behavior. The new profile does not require the unavailable original GPIO27/contactor assembly, but cannot substitute software for those separate electrical conditions. Software stop does not isolate the LiPo.

## Automated verification

| Verification | Final result |
| --- | --- |
| Native protected controller/adapter/navigation/turning regressions | 85 passed |
| Existing USB bench real-adapter suite | 11 passed; no motor/PWM attachment capability |
| MOTOR_OPERATION with incomplete real commissioning record | 10 passed; GPIO27 HIGH/RESET/HEARTBEAT cannot bypass inhibition |
| Motor path with host-only qualification fixture | 19 passed: PWM F/B/L/R, neutral/enable sequence, normal stop, cleaning, ESTOP/reset, AUTO, stale sensors, invalid commands, serial overflow, PWM failure, manual/AUTO command loss and millis rollover |
| Total native firmware tests | **125 passed** |
| Python tests | **59 passed**, including all release-mode preprocess checks, rejection of host fixture in three hardware contexts, unknown-mode rejection and all three exact Arduino package inventories |
| Complete TypeScript/Vitest suite | **125 passed**, one worker; includes actual host firmware -> TEL -> bridge, heartbeat-backed AUTO and command-loss disarm, all legacy camera/bridge/dashboard regressions |
| Bridge and dashboard TypeScript builds / Vite | Passed |
| Built production serving smoke | Passed; compiled asset and stopped/disarmed API served on loopback |
| Complete browser suite | **9 passed**; original controls/camera/monitoring plus bench and new motor mode, inhibited/commanded states, raw feedback, ESTOP/RESET and mobile overflow checks |
| Main firmware compilation | PROTECTED_ROVER / USB_BENCH_DIAGNOSTIC / MOTOR_OPERATION / generated Wokwi all passed; zero compiler warnings |
| Arduino IDE-compatible new MOTOR_OPERATION package | ESP32 core **2.0.17**, ESP32 Dev Module; passed, zero warnings |
| Main Arduino archives | All three regenerated; exactly seven matching source files each; valid CRCs, no secrets/camera/binaries |
| Camera policy and actual HTTP-handler host suites | Both passed unchanged |
| Static GPIO/generated-sketch consistency | Passed |
| Electrical, PDF/design-export, completion, system and historical handover consistency | Passed; original protected wiring authorities unchanged |
| Wokwi CLI lint | Passed; no new remote runtime or physical test claimed |
| Preservation/security | Camera/proxy/component/ZIP, 16 GPIOs, ultrasonic measurement/scheduler and private credential bytes/mode/mtime unchanged; secrets remain ignored/untracked; no configured credentials in any changed file |
| Physical electrical qualification / motor movement | **Not performed; not verified; hardware release remains blocked** |

The positive motor path uses host GPIO/serial mocks and synthetic echoes; it never opens a physical device. The browser motor release transition is a test-only incoming telemetry fixture, not a production UI/API commissioning control. No motor movement, electrical qualification, actual power interruption or new physical sensor/video test was claimed. An initial two-worker laptop run hit the existing startup-handshake timeout in one protected integration test; the complete suite passed with one worker. No runtime feature was changed to suppress that timeout.

Detailed logs and snapshots remain ignored under `artifacts/motor-operation/`. The source changes are left uncommitted for review; no GitHub push occurred.

## Exact changed-file inventory

- `README.md`
- `apps/rover-bridge/src/bridge.ts`
- `apps/rover-bridge/test/motor-integration.test.ts`
- `apps/rover-bridge/test/motor-operation.test.ts`
- `apps/rover-dashboard/src/App.tsx`
- `apps/rover-dashboard/src/navigation.ts`
- `apps/rover-dashboard/test/App.test.tsx`
- `docs/MOTOR_OPERATION_HANDOVER.md`
- `docs/MOTOR_OPERATION_WIRING.md`
- `docs/SERIAL_PROTOCOL.md`
- `docs/USB_BENCH_DIAGNOSTIC.md`
- `firmware/rover.ino`
- `include/rover_commissioning.h`
- `include/rover_control.h`
- `include/rover_mode.h`
- `include/rover_telemetry.h`
- `packages/protocol/index.ts`
- `platformio.ini`
- `scripts/build_simulator.py`
- `scripts/package_main_arduino.py`
- `scripts/simulation/bench_serial.cpp`
- `scripts/sync_wokwi.py`
- `scripts/verify.py`
- `test/browser/motor-operation.spec.ts`
- `test/stubs/Arduino.h`
- `test/test_commissioning.py`
- `test/test_main_arduino_package.py`
- `test/test_motor_operation/test_main.cpp`
- `wokwi/sketch.ino`
