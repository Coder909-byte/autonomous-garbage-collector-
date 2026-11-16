# USB commissioning report — 16 November 2026

The repository firmware builds and the laptop software passes its tests. **Physical commissioning is blocked by corrupt serial reception before bootloader identification. No flash write or upload was attempted; the previously installed firmware has not been replaced.**

| Item | Result | Evidence / limits |
|---|---|---|
| Firmware build | PASS | `esp32dev`, pinned Espressif32 6.12.0 / Arduino 2.0.17. RAM 22,240/327,680 bytes (6.8%); flash 281,945/1,310,720 bytes (21.5%). `wokwi_compile` also passed. |
| Actual USB port | Detected | `/dev/cu.usbserial-0001`, with `/dev/tty.usbserial-0001` alias. CP2102 USB UART, Silicon Labs 10C4:EA60, serial 0001, USB location 20-2. Node SerialPort lists the `tty` alias for dashboard selection. |
| Firmware upload | NOT RUN — blocked | Both read-only bootloader identification attempts failed. No explicit upload approval requested while communication is broken; no uploader write command executed. |
| Firmware identity | Source/build identified; installed version unknown | Git `294c416b0c9f1d1e74cc90fc35783799ea120019`; expected firmware `rover-usb-v1`. No physical firmware-version observation. |
| ESP32 startup | NOT VERIFIED | No readable startup or chip-ID response. USB adapter enumeration alone does not identify the attached ESP32 silicon. |
| Serial telemetry | FAIL to obtain valid data | Passive 115200-baud capture collected 32,768 bytes, all zero; no `READY`, `STATE`, `DIST`, or valid `TEL` frame. This does not diagnose a firmware logic defect. |
| Laptop dashboard | PASS for serving/UI; live hardware NOT VERIFIED | Production dashboard/bridge at `http://127.0.0.1:8787`, disconnected, `protocolReady:false`, `telemetry:null`, ARM disabled, no browser page errors. Hardware was not opened by this UI check. |
| E-stop safety status | Physical state NOT VERIFIED | USB-only isolation explicitly confirmed by user. Source/host tests support disarmed boot and latched E-stop when GPIO27 is absent/LOW. Actual GPIO14/driver/cutoff voltages remain unmeasured. |
| Ultrasonic sensors | NOT TESTED physically | No valid distances. Unverified sensors remain isolated; no direct raw 5 V ECHO connection authorized. |
| Motors / brushes / conveyor | NOT RUN — HOLD | No hardware ARM, AUTO, motion, cleaning activation or safety-bypass command sent. Battery/motor-powered commissioning remains a separate approval stage. |
| ESP32-CAM | NOT TESTED physically | Separate firmware/programmer/power stage untouched. Camera policy/HTTP mocks passed; no real video claimed. |

NOT RUN / NOT VERIFIED explicitly distinguish missing evidence from a demonstrated hardware failure. No physical stage is marked PASS based on simulation.

Repository and firmware audit:

- The initial Git working tree was clean. No pull, reset, checkout, commit or remote operation occurred. The revision above is the newest locally checked-out code; remote freshness was not asserted.
- PlatformIO's default environment and requested build are `esp32dev`, board `esp32dev`, framework Arduino. `src/main.cpp` includes `../firmware/rover.ino` unless `ROVER_WOKWI_SKETCH` is defined. The main environment does not define it. The generated dependency file confirms the `.ino` and all three rover headers are compiled.
- GPIO contract passed: left wheel 16/17; right 18/19; brush 21/22; conveyor 23/25; shared enable 14; active-HIGH safety feedback 27; front sensor 32/34; left 33/35; right 13/36. No GPIO, motor, controller, emergency-stop or telemetry implementation was changed.
- Protocol is 115200 baud, `TEL ` followed by JSON containing `"v":1` and `"fw":"rover-usb-v1"`; it is not the literal text `TEL v1`. Legacy `STATE` and `DIST` remain. The bridge parser checks schema, range/age fields and contradictory outputs. Telemetry reports applied software outputs, not measured physical motion or power.
- The firmware begins with outputs disabled. GPIO27 uses `INPUT_PULLDOWN`; absent feedback causes emergency/disarm. GPIO14 gating, falling-edge ISR, physical interlocks, manual timeout, motion neutral interval and AUTO sensor-fault disarm were preserved. Startup/reset analog behavior still needs electrical measurements.
- The real compiler passed. Arduino-header/API diagnostics in VS Code would therefore be editor configuration issues for this configured target if they correspond to the successfully compiled code. The actual VS Code Problems list was unavailable, so individual diagnostics were not conclusively classified. Use the PlatformIO `esp32dev` environment and its Rebuild IntelliSense Index command; do not change working firmware to silence editor squiggles.

Mac and USB diagnosis:

- `df -h /` reported 1.6 GiB available, 91% capacity. No project, toolchain or user files were deleted. Builds completed with installed dependencies; no package reinstall was needed.
- `.venv/bin/pio` is Core 6.1.18. The pinned ESP32 platform, Arduino framework, Xtensa compiler, esptool and filesystem tools are installed. Node v24.14.1 meets the repository's >=22.12 requirement.
- Both serial device aliases had read/write permission. `lsof` found no holder before checks and after closing them. Only one serial diagnostic owned the port at a time; bridge startup did not automatically open it.
- Auto-reset chip identification at 115200 failed with `Invalid head of packet (0x00)`. After the user's confirmed BOOT/EN sequence, another read-only identification with `--before no_reset --after no_reset` failed identically. Neither command writes flash.
- A subsequent bounded passive capture, with flow control disabled and DTR/RTS deasserted, yielded only zero bytes. The source of the bad signal is unknown: adapter/driver, cable/power, UART line loading, reset/boot state, board connection or board hardware still need discrimination. No physical voltage or cable substitution result is inferred.
- A temporary `upload_speed = 115200` experiment was reverted after it changed the frozen electrical handover fingerprint. That checker passed again afterward. There is no retained `platformio.ini` change. The current failure is already present at 115200 before transfer. If a later transfer-rate change is justified, configure `upload_speed` under `[env:esp32dev]`; `pio run --upload-speed` is invalid.

Fresh software results:

| Check | Result |
|---|---|
| `scripts/verify.py` | PASS: GPIO/source contracts, electrical structure, export integrity, completion consistency, 84 native C++ tests, 54 Python tests, both ESP32 builds, Wokwi lint |
| `scripts/check_system.py` | PASS: 211 system connection records, original 201 electrical records preserved |
| `scripts/check_team_handover.py` | PASS after temporary upload-rate edit reverted; all physical records still PENDING |
| `npm run sim:build` | PASS, including separate camera policy/HTTP mock executables |
| `npm test` | Final PASS: 56/56. First attempt had one integration timeout; rebuilt the documented simulator prerequisite and reran successfully. No source/test change made. |
| `npm run build` | PASS: TypeScript bridge and React production dashboard |
| `npm run test:e2e` | PASS: 4/4 browser tests. C++ simulation and mock network failure only; no hardware motor commands. |
| Production smoke and browser | PASS: compiled dashboard/API served, disconnected controls disabled, no page errors |

The simulator's ARM/AUTO/motion/cleaning commands occurred only in software test processes with no GPIO or physical serial transport. Wokwi runtime was not executed; lint is not runtime verification.

The final main binary is `.pio/build/esp32dev/firmware.bin`, 282,304 bytes, SHA256 `85c08b1b5cdd109de0728a7432e99dcf1ae034039075dec819ced6a2fef522ea`. This identifies a built artifact, not an installed image.

Evidence is saved locally under `artifacts/usb-validation/`: full software verification, final main build, automatic/manual chip-ID logs, passive serial summary, browser-test log, disconnected dashboard screenshot and `summary.json`. This directory follows the existing ignored-artifact policy. Existing selected test logs/screenshots were refreshed by repository test scripts. No safety documents, frozen manifests or firmware source files were overwritten.

Next physical action: with all previously confirmed isolation conditions maintained, disconnect USB, inspect the detached DevKit and header connections (especially UART0, EN and BOOT), and reconnect directly using a different known data cable/USB port. Record the power LED and new enumeration. Then capture actual reset/BOOT output and investigate the UART path; do not repeat flashing blindly. If 3.3 V/EN/TX0 checks are needed, they require a qualified low-energy measurement procedure. Once read-only chip identification succeeds, request explicit approval immediately before uploading the identified main firmware.

The practical staged plan is [USB_COMMISSIONING_CHECKLIST.md](USB_COMMISSIONING_CHECKLIST.md). Existing electrical blockers B01–B14 remain open: actual module and motor ratings, two-motor BTS limits, shared L298 thermal/current capability, conveyor voltage, pack/protection/fuse/wire/contact selections, ECHO isolation, reset-safe enables, rail/backfeed qualification, physical cutoff and commissioning measurements. No motor/battery stage has been released.

Procedure references: [Espressif troubleshooting](https://docs.espressif.com/projects/esptool/en/latest/esp32/troubleshooting.html), [Espressif boot-mode selection](https://docs.espressif.com/projects/esptool/en/latest/esp32/advanced-topics/boot-mode-selection.html), [PlatformIO upload_speed](https://docs.platformio.org/en/latest/projectconf/sections/env/options/upload/upload_speed.html). Dashboard verification used the [vercel:verification skill](/Users/kokila/.codex/plugins/cache/openai-curated-remote/vercel/0.54.1/skills/verification/SKILL.md).
