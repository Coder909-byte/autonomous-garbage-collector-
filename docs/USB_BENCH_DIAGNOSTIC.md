# Main ESP32 operating configurations

Implementation base: `e8243c8` (18 November 2026), after camera release `7835925`. The user reports working main ESP32 USB telemetry on the Dell G15, all three ultrasonic readings, and independent ESP32-CAM video in Mission Control. Those reports are accepted as context; this software change does not repeat physical tests.

## Audit before editing

`firmware/rover.ino::healthy()` reads the actual GPIO27 input. The previous firmware latched E-stop when that input was LOW at boot, on its falling-edge interrupt and in the loop/controller. RESET required healthy feedback while disarmed; ARM required healthy feedback and successful PWM setup. The output adapter checked feedback again before asserting GPIO14, under the safety critical section. The ISR immediately cleared GPIO14. Independent qualified hardware remained responsible for removing motor power.

**GPIO27 did not block sensor acquisition or telemetry.** The loop continued polling one sensor every 65 ms, with 2 us LOW / 10 us HIGH triggering and a maximum 25 ms `pulseIn` wait. Sensor measurement/scheduling, 500 ms TEL/DIST reporting and GPIO assignments remain unchanged.

The existing protected controller retains its 1200 ms manual movement timeout, sensor freshness checks, neutral interval and autonomous navigation. There is no new protected AUTO serial-link deadman: backend loss can leave onboard AUTO running, as previously documented in [SERIAL_PROTOCOL.md](SERIAL_PROTOCOL.md). Bench outputs remain disabled regardless of command loss.

A separate [MOTOR_OPERATION configuration](MOTOR_OPERATION_HANDOVER.md) now provides the motor-capable path under an explicit commissioning record. It does not change either configuration documented here.

## Explicit compile-time configurations

| Behavior | PROTECTED_ROVER (default) | USB_BENCH_DIAGNOSTIC |
| --- | --- | --- |
| PlatformIO environment | `esp32dev` | `usb_bench_diagnostic` |
| GPIO27 | Actual input, pull-down, falling-edge interrupt and physical latch | Actual input and pull-down; reported without simulating installed protection; no physical-trip interrupt |
| Startup | Disarmed; LOW feedback latches E-stop | Disarmed; missing feedback does not itself latch software E-stop |
| STOP / ESTOP | Latched emergency disarm | Latched software emergency disarm |
| RESET | Disarmed, healthy feedback/PWM required | Disarmed; GPIO27 may stay LOW; cannot authorize motors |
| ARM, AUTO, F/B/L/R, cleaning ON | Existing protected rules | Rejected with ERR; no runtime override |
| S, DISARM, MANUAL, cleaning OFF | Existing behavior | Accepted; outputs remain disabled; none clears the E-stop latch |
| PWM peripheral | Existing 1200 Hz / 8-bit LEDC | Never configured or attached; PWM helper always writes LOW |
| GPIO14 and eight motor direction pins | Existing gated outputs | LOW after setup and through every command |
| Sensor / USB / independent camera | Preserved | Preserved |

`include/rover_mode.h` defaults to PROTECTED_ROVER and rejects invalid selections. The controller rejects bench motor commands and disarms on every tick. The adapter separately forces stop and denies enable even if controller fields are forcibly changed in a host test. No serial or dashboard command changes the build configuration.

Firmware cannot guarantee pin states before setup executes or during unstable reset/power ramps. Physical bench safety therefore requires disconnected motor power and driver harnesses, as described below.

## Backward-compatible telemetry and Mission Control

All existing TEL v1 fields and types remain. Added fields are `mode` (`PROTECTED_ROVER` / `USB_BENCH_DIAGNOSTIC`) and `motorCapable` (boolean build capability, not hardware certification). `healthy` still reports the real GPIO27 input. Bench telemetry can correctly contain `healthy:false`, `estop:false`, `armed:false`, `en:false`, `nav:"DISARMED"` and live distances together.

The parser accepts legacy v1 telemetry without these fields. New metadata is validated as a pair; diagnostic messages claiming arming, AUTO, nonzero requested/applied movement or cleaning requests/outputs are rejected. The bridge completes its existing DISARM/telemetry handshake with bench firmware and LOW feedback, rejects motor commands/hold leases, and permits deliberate software RESET while disarmed. Protected RESET still requires healthy feedback.

The dashboard retains its layout and camera component. It displays **USB BENCH DIAGNOSTIC · NO MOTOR POWER**, disables ARM/directional controls/AUTO/cleaning ON, and retains sensors, telemetry, stop/disarm, software ESTOP, deliberate RESET, diagnostics and camera access. Navigation text explains that bench outputs cannot drive motors. GPIO27 appears as its actual diagnostic input value.

## Actual IBT-2 / HW-039 terminals

The supplier guide specifies active-HIGH enables and a +5 V logic supply. Its broad 3.3 V compatibility advertisement does not qualify an unknown clone. Verify each actual board's chip marking, logic supply and header continuity. An onboard **SN74HC244** is a logic buffer, not galvanic isolation or the missing external **SN74AHCT244N**. [Supplier guide](https://www.handsontec.com/dataspecs/module/BTS7960%20Motor%20Driver.pdf)

TI's HC244 minimum HIGH levels are 3.15 V at a 4.5 V supply and 4.2 V at 6 V. A nominal 3.3 V ESP32 signal does not establish a guaranteed margin for a 5 V HC input. Direct drive is not approved from the module name alone. Do not assume changing the module VCC to 3.3 V qualifies its downstream circuitry. AHCT244 specifies TTL-compatible 2 V HIGH / 0.8 V LOW limits and is a candidate external interface, subject to the existing load/rail/reset qualification. [TI HC244, section 5.3](https://www.ti.com/lit/ds/symlink/sn74hc244.pdf), [TI AHCT244, sections 5.3/7.3](https://www.ti.com/lit/ds/symlink/sn74ahct244.pdf)

| Terminal | Intended protected connection |
| --- | --- |
| VCC / GND | Qualified regulated logic 5 V / common signal reference, per actual module requirements |
| Left RPWM / LPWM | GPIO16 / GPIO17 through qualified U1 level interface |
| Right RPWM / LPWM | GPIO18 / GPIO19 through qualified U1 level interface |
| Both R_EN and L_EN, each module | `EN_DRIVER_5V`, under GPIO14 and the independent S2 enable contact; no permanent HIGH links |
| R_IS / L_IS | Current/alarm outputs; unconnected and insulated unless separately qualified for ESP32 inputs; no current monitoring added |
| B+ / B- | Qualified fused, contactor-switched motor supply / heavy power return |
| M+ / M- | That side's motor pair in the existing design, subject to current/polarity/wiring review |

R_EN/L_EN enable their respective half bridges; they are not direction pins or physical power-isolation contacts. In normal operation LOW inhibit turns that half bridge's switches OFF. HIGH enables PWM/IN-controlled switching; PWM LOW with enable HIGH can turn on a low-side switch rather than disconnect the motor. [Infineon BTS7960, section 4.4.5](https://www.infineon.com/dgdl/Infineon-BTS7960-DS-v01_01-en.pdf?fileId=db3a304412b407950112b43945006d5d)

The proposed protected path remains **GPIO14 -> U1.11 (2A1) -> U1.9 (2Y1) -> S2.EN_COM -> S2.EN_NC -> both R_EN/L_EN pairs and L298N ENA/ENB**, with the existing six local pull-downs and no permanent HIGH jumpers. Separate contactor/power and 3.3 V GPIO27 feedback paths remain required. See [FINAL_WIRING.md](FINAL_WIRING.md) and [the cutoff drawing](diagrams/emergency_stop.svg). Never tie GPIO27 HIGH to imitate the missing assembly. Software ESTOP does not isolate the LiPo.

## USB-only bench wiring and inactive-state checks

1. Physically disconnect the LiPo and every motor supply from the wheel/cleaning drivers. Leave B+ feeds and motor loads disconnected. Keep the motor-driver control harness disconnected from the ESP32. Power the main board from USB and preserve the known working, voltage-qualified sensor arrangement. This change does not authorize raw 5 V ECHO connections to ESP32 inputs.
2. Leave driver boards unpowered for MCU/sensor diagnostics. For a separate logic-only module check, retain no motor supply/load, remove HIGH enable links and hold both R_EN/L_EN LOW to module GND. Disconnect the GPIO14/interface feed before grounding enables to prevent contention with another build. Do not leave enables floating or assume clone pull-downs exist; otherwise keep the entire module disconnected.
3. Confirm the bench startup banner and `mode:"USB_BENCH_DIAGNOSTIC",motorCapable:false`. Measure GPIO14, 16, 17, 18, 19, 21, 22, 23 and 25 against ESP32 GND: expected LOW after setup, during rejected motor commands, after ESTOP/RESET and after command silence. A scope/logic analyzer is needed for transient checks; a meter does not qualify reset/brownout behavior. These physical measurements were **not** performed here.
4. Leave GPIO27 unforced; a disconnected input should read LOW. Check front/left/right readings, USB readiness, software-latch behavior and the separate camera connection. Those checks do not authorize motor power.

All 16 assignments in `include/rover_pins.h` remain unchanged, including brush 21/22, conveyor 23/25, TRIG 32/33/13 and ECHO 34/35/36. No ultrasonic timing or measurement code changed.

## Windows build and later manual upload

With PlatformIO Core installed, run from the current repository checkout in PowerShell. The pinned `espressif32@6.12.0` uses Arduino-ESP32 2.0.17.

```powershell
# Build default PROTECTED_ROVER:
pio run -e esp32dev
# Build explicit USB_BENCH_DIAGNOSTIC:
pio run -e usb_bench_diagnostic
```

For a later deliberate bench upload, identify the **main ESP32** COM port, close Mission Control/Serial Monitor and establish the disconnected bench arrangement above. Replace COM7 with its actual port; do not select the camera.

```powershell
pio run -e usb_bench_diagnostic -t upload --upload-port COM7
pio device monitor --port COM7 --baud 115200
```

Protected motor-powered use requires separate hardware qualification. Its later manual upload command is `pio run -e esp32dev -t upload --upload-port COM7`. Neither upload command was executed here.

### Arduino IDE alternative

**Arduino IDE needs a new main-ESP32 sketch package** because its firmware/headers changed. The camera ZIP remains independent and unchanged. PlatformIO uses this repository directly and needs no ZIP.

```powershell
py -3 scripts/package_main_arduino.py --mode USB_BENCH_DIAGNOSTIC
py -3 scripts/package_main_arduino.py --mode PROTECTED_ROVER
```

On macOS use `python3` instead of `py -3`. Outputs are under `build/arduino/usb_bench_diagnostic/` and `build/arduino/protected_rover/`. Each ZIP contains exactly seven source files in `rover_main/`: `rover_main.ino`, `rover_build_config.h`, and the five canonical `rover_*.h` headers, including `rover_commissioning.h`. No camera source, credentials or binary is included. Default package generation selects PROTECTED_ROVER. Inspect `rover_build_config.h` to confirm the selected compile-time mode.

Extract only the intended package to a separate folder and open `rover_main/rover_main.ino`. In Boards Manager install **esp32 by Espressif Systems 2.0.17**. Select **ESP32 Dev Module**, 240 MHz CPU, DIO/40 MHz/4 MB flash, default 4 MB partition scheme, PSRAM disabled (matching esp32dev; confirm the actual main board). Click **Verify**. Only after the separate manual preparation above, select the main ESP32 COM port and click **Upload**. Serial Monitor uses 115200 and newline; close it before Mission Control connects. Do not select AI Thinker ESP32-CAM for this sketch.

## Validation and unresolved hardware

See [USB_BENCH_IMPLEMENTATION_REPORT.md](USB_BENCH_IMPLEMENTATION_REPORT.md) for exact modified files and automated results. Detailed logs stay in ignored `artifacts/usb-bench-diagnostic/`.

Missing cutoff/contactor/feedback hardware, the external buffer, unqualified HW-039 signal margins/input defaults, motor stall/combined currents, LiPo/fuse/cable/protection ratings, L298N load/thermal behavior and reset/brownout behavior still block future motor-powered commissioning. No physical upload or hardware acceptance test occurred here. Camera firmware, secrets, pin mapping and HTTP/stream implementation remain untouched. The local commit was subsequently cleaned so secrets.h remains ignored and untracked, with its working contents unchanged on disk. No changes are pushed pending review.
