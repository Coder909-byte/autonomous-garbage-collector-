# Verification matrix — one L298N, turn-state update

Recorded 2 November 2026. This revision uses channel A for both brushes in parallel and channel B for the conveyor. **No physical firmware upload, battery connection, motor activation, electrical measurement or hardware commissioning was performed.**

## Evidence levels

| Level | Status | Evidence and limits |
|---|---|---|
| ESP32 firmware compile verified | **PASS** | `esp32dev`, Espressif32 6.12.0 / Arduino 2.0.17; `artifacts/build.log` |
| Standalone Wokwi sketch compile verified | **PASS** | `wokwi_compile`, generated from the same controller, pin definitions and adapter; same build log |
| Host controller/parser/interlock verified | **PASS: 38 tests** | Original 32 tests retained/adapted, plus independent auxiliary requests, ARM requirements, auxiliary commands not refreshing deadman, STOP latch/clearing requests, fault clearing both channels and CLEAN aliases |
| Host firmware I/O boundary verified | **PASS: 21 tests** | Original 12 retained/adapted, plus one-L298N outputs, auxiliaries off during neutral/turn, right-turn polarity, GPIO27 internal pull-down, STOP cuts both auxiliary channels, four-pin auxiliary topology, full AUTO turn duration after EN, E-stop ISR during AUTO turn and reassessment fault stopping |
| Host turning regressions verified | **PASS: 20 tests** | `test/test_turning/test_main.cpp`: continuous turns, full enabled duration, new post-stop sensor frame, bounded retries, hysteresis, updated direction, clear recovery, rollover, emergency/sensor faults across all phases |
| Host VCD evidence checker verified | **PASS: 10 tests** | Synthetic host traces test PWM detection, left direction, brush/conveyor independence, all-blocked state, and rejection of opposing PWM, unknown signals, stuck-HIGH output, missing channels and wrong auxiliaries. These traces are **not Wokwi recordings**. `artifacts/python-tests.log` |
| Electrical-model fault rejection | **PASS: 11 Python tests** | Structural netlist mutations reject raw ECHO, shared buck outputs, missing pulls, wrong GPIOs, bypassed cutoff/feedback, fabricated fuse ratings and footprints; not a powered electrical simulation |
| Electrical source/export agreement | **PASS** | E1 source defines 82 components, 69 nets, 188 connection rows and 276 modeled terminals including NC; all schematic SVG terminals, CSV connectivity and readable 21-page PDF validated. No KiCad/ERC or physical approval. `artifacts/design-export-checks.log` |
| Static code/diagram agreement | **PASS** | 16 unique GPIOs, exact one-L298N map, both brush indicators sharing GPIO21, separate conveyor GPIO23, GPIO27 E-stop, analyzer mapping, no resistor components and no stale GPIO26/39 connections. `artifacts/static-checks.log` |
| Wokwi diagram lint | **PASS, no errors or warnings** | Wokwi CLI v0.29.1. One informational notice remains about the older DevKit-v1 part. `artifacts/wokwi-lint.log` |
| Manual Wokwi functional results before turn update | **OWNER-REPORTED PASS: 11 checks** | Startup, three readings, ARM, AUTO, forward command, left/right avoidance, brushes, conveyor, ESTOP and no automatic restart. See manual results below; no raw trace supplied. |
| Wokwi runtime after turn update | **RETEST REQUIRED / NOT EXECUTED HERE** | Eight runnable scenarios prepared; no `WOKWI_CLI_TOKEN` exists in this environment. `artifacts/wokwi-runtime.log` and `artifacts/wokwi-scenarios/results.json` record the reason. Host tests and compilation do not substitute for these runs. |
| Arduino-ESP32 3.x build | **NOT EXECUTED** | Compatibility branch exists; only pinned Arduino 2.0.17 is compile verified. |
| Physical hardware | **UNTESTED / CONNECTION HOLDS ACTIVE** | ECHO voltage, driver logic/default enables, summed motor current, power distribution, battery protection and all mechanics remain unverified. |

Both firmware builds pass without compiler warnings and use **22,232 bytes RAM / 281,345 bytes flash** (`artifacts/build.log`). `artifacts/native-tests.log` records all **79 C++ cases passing**; the Python log records **21 cases passing** (10 VCD-checker and 11 electrical-model checks). Host Arduino stubs do not reproduce actual interrupt concurrency, electrical voltage/current, PWM peripheral behavior, acoustics or mechanical loads. Their E-stop ISR test verifies the requested register operation, not measured physical response time.

Run the entire software suite sequentially with `python3 scripts/verify.py`. Previous two-L298N logs are under `artifacts/previous_two_l298n/`; the pre-turn-update one-L298N results are under `artifacts/previous_one_l298n/`. Neither establishes verification for the changed turning behavior.

## Manual Wokwi results supplied by the owner

The following were explicitly confirmed working by the owner on 2 November 2026, on the one-L298N code **before this turning-state change**. They are accepted as manual simulation evidence, not assistant-executed tests or physical evidence. Independent auxiliary OFF behavior, exact thresholds/dead time and fault injection were not included in that report.

| Owner's manual check | Reported result |
|---|---|
| ESP32 startup | **PASS** |
| Three ultrasonic distance readings | **PASS** |
| ARM command | **PASS** |
| AUTO command | **PASS** |
| Forward movement command / simulated output | **PASS** |
| Left obstacle avoidance | **PASS**, with repeated STOPPED/LEFT transitions reported |
| Right obstacle avoidance | **PASS**, with repeated STOPPED/RIGHT transitions reported |
| Brush activation | **PASS** |
| Conveyor activation | **PASS** |
| Emergency stop | **PASS** |
| Emergency stop prevents automatic restart | **PASS** |

## Turn/stop alternation regression

A host reproduction showed the old controller retrying indefinitely on constant blocked ranges, with each enabled turn lasting ~440 ms because 100 ms dead time was inside a 540 ms request timer. This explains the reported pattern under static distances; the user's exact cadence cannot be verified without timestamps. Side-clearance loss can also cause early stops.

The update separates SETTLE → TURN_DEAD_TIME → TURNING → REASSESS. The turn timer begins after software-applied EN; a stopped reassessment requires at least 180 ms and one new reading from every sensor. Forward recovery uses >45 cm hysteresis. Three unsuccessful attempts disarm with `TURN_LIMIT`; clearing ranges alone cannot restart. All active phases remain interruptible by E-stop and invalid/stale sensors. See [TURNING_REVIEW.md](docs/TURNING_REVIEW.md), `artifacts/turn-investigation-before.log` and `artifacts/turn-investigation-after.log`.

The changed behavior is host-test/compile verified by the completed suite; **post-change Wokwi runtime timing and physical behavior remain unverified**. The manual passes above must not be presented as verification of this new implementation.

## Prepared Wokwi runtime cases

Run `python3 scripts/run_wokwi.py --prepare-only` to generate each scene, configuration and scenario. After configuring a Wokwi CI token locally, run `python3 scripts/run_wokwi.py`. The script never accesses a physical serial port. Wokwi requires the token for CLI execution; [official instructions](https://docs.wokwi.com/wokwi-ci/cli-usage).

Scenarios use documented serial and pin assertions; recorded VCD must additionally show actual active PWM levels, no opposing wheel channels while EN is high, and the expected auxiliary channels. A missing VCD or stuck-HIGH 'PWM' is a failure. The scenarios and their integration with the simulator remain unexecuted in this workspace; they may require adjustment when first run. [Scenario reference](https://docs.wokwi.com/wokwi-ci/automation-scenarios).

| Runtime case | Setup and expected result | Current revised-runtime status |
|---|---|---|
| `auto_forward` | All sensors 100 cm; ARM → AUTO; EN high, PWM on left/right FWD only, auxiliaries off | **NOT EXECUTED** |
| `auto_left` | Front 20, left 100, right 60; ARM → AUTO; stop/settle, left REV + right FWD, auxiliaries off | **NOT EXECUTED** |
| `auto_right` | Front 20, left 60, right 100; ARM → AUTO; stop/settle, left FWD + right REV, auxiliaries off | **NOT EXECUTED** |
| `obstacle_no_path` | Front 20, both sides 45; ARM → AUTO; EN/PWM/both auxiliary channels stay low | **NOT EXECUTED** |
| `emergency_and_reset` | Forward + CLEAN ON; ESTOP turns everything off; ARM rejected; RESET remains stopped; ARM alone remains stopped; new F resumes without auxiliaries; STOP latches again | **NOT EXECUTED** |
| `brushes_only` | ARM → F → BRUSH ON; both brush indicators share A, conveyor B low; BRUSH OFF then S | **NOT EXECUTED** |
| `conveyor_only` | ARM → F → CONVEYOR ON; channel B high, brushes A low; CONVEYOR OFF then S | **NOT EXECUTED** |
| `manual_deadman` | ARM → F once; after 1.2 s all outputs stop | **NOT EXECUTED** |

The model represents all motor control signals with virtual indicators/analyzer; it does **not** model BTS/L298 switching currents, actual wheel rotation, brush mechanics, conveyor load, power distribution or LiPo behavior. Virtual resistor-free LEDs and direct ECHO wires must never be copied into physical wiring.

## Post-update Wokwi rerun and remaining interactive checks

Use 115200 baud with Newline. Start switch LEFT. Wait for valid DIST readings before `ARM` then `AUTO`.

| Check | Action | Expected observation |
|---|---|---|
| Disabled startup | Start/reset simulation | `READY DISARMED`; EN and all actuator signals LOW |
| Sensor identity | Change each distance slider separately | Correct front/left/right DIST field changes |
| Front boundary | Front 35 cm, sides 100/60 | Stop/SETTLE, 100 ms neutral, continuous 540 ms enabled left turn, then REASSESS; auxiliaries off |
| Persistent obstacle | Keep front 20 cm, sides 100/60 (then mirror) | At most three turn attempts; `TURN_LIMIT`, disarmed, no automatic restart |
| Fresh reassessment / recovery | After turning, set front >45 cm and both sides >20 cm | Forward only after stopped settling and new readings from all three sensors |
| Threshold hysteresis | After entering avoidance, vary front from 35 to 36–45 cm | Does not resume forward until front exceeds 45 cm |
| Side intrusion | Set either side ≤20 cm | Stop; no turn into inadequate side clearance |
| E-stop switch | While moving, switch RIGHT | EN off, ISR trip latched; LEFT alone cannot restart; RESET + ARM + new motion needed |
| Independent auxiliaries | After ARM and forward motion, BRUSH ON/OFF and CONVEYOR ON/OFF | Only requested channel changes; both brush LEDs always agree |
| Neutral interval | Request opposite movement in MANUAL | 100 ms of disabled output before new polarity; inspect analyzer |
| Sensor fault | With simulation stopped, disconnect a virtual ECHO and restart | Missing reading; AUTO rejected. Host tests separately cover invalid/stale samples arriving during AUTO and disarming without automatic restart. |
| Serial overflow | Send >48 characters while moving | Disarms and discards the entire overlong line |

Serial `STOP` and `ESTOP` both latch. Exact recovery sequence with healthy switch:

```text
RESET
ARM
AUTO
```

`S` is the distinct non-latching stop/exits-AUTO command. For independent auxiliary checks use `ARM`, `AUTO`, then `BRUSH ON` or `CONVEYOR ON` on a clear scene. Auxiliary requests never activate motors when stopped, reversing, turning or in the neutral interval.

## Physical holds and future acceptance requirements

These are requirements for later commissioning, not tests executed or authorized during this software task. See [WIRING.md](docs/WIRING.md) for exact proposed connections.

| Area | Hold / required evidence before connection or powered trials |
|---|---|
| Three real ECHO lines | **Remain insulated/disconnected.** Owner confirms exact manufacturer/variant/datasheet unknown. Establish documented 3.3 V-compatible output at intended supply and check actual signal levels independently of ESP32. Otherwise necessary voltage translation is unavailable; no direct 5 V ECHO connection. |
| Shared brush channel | Measure/obtain both brush running/start/stall currents; compare their **sum** against derated verified channel-A capability and total package heating while conveyor also runs. Arrangement is unverified. |
| Conveyor channel | Establish motor voltage and running/start/stall requirements and shared thermal budget. |
| BTS7960 logic | Identify exact module buffer/supply/thresholds; no unsupported 5 V/3.3 V wiring assumptions. |
| Reset-safe enables | Remove EN jumpers; qualify module defaults through power ramps/reset/brownout. GPIO14 firmware LOW is insufficient before setup; missing pulls/translation cannot be bypassed. |
| Emergency cutoff | Establish independent appropriately rated motor-power removal for all three drivers, feedback isolation and deliberate restart behavior. Switch/contactor availability is not confirmed. |
| Power/battery | Continuity, polarity, correct buck outputs, USB backfeed prevention, current-rated returns/connectors, coordinated fuses, actual pack C rating, cell-level low-voltage protection and battery-specific limits. |
| Mechanical behavior | Only after electrical gates: guarded wheel-direction, inward brush/conveyor direction, thermal/current/jam and stopping-distance trials with suitably controlled equipment and supervision. |

Software does not establish the safety of current parts or a working physical rover. No motor-current sensing, battery-voltage sensing, rear/cliff sensing, encoders or real waste recognition is present.

## Electrical package E1 verification and supplied simulation status

The working firmware/controller/pin map/generated sketch hashes are unchanged from the prior verified revision (`artifacts/firmware-preservation.json`). Both ESP32 environments were rebuilt and all **79 C++ + 21 Python = 100 host tests** pass. The structural electrical check and complete SVG/CSV/PDF export checks pass. Main Wokwi pin/source consistency and lint pass; no resistor components were added to Wokwi.

In the latest electrical-design request the owner again reports successful Wokwi autonomous movement, obstacle avoidance, cleaning controls and emergency-stop latching. These are accepted as owner-reported functional simulation results. No independent CLI run or quantitative waveform trace was supplied/executed for this package. Simulation does not verify E1's added protection hardware or physical levels/currents.

**Physical verification: NONE.** No firmware was uploaded, no battery was connected and no real motor energized during this task. All E1 physical connections remain provisional/blocked. The independent cutoff/protection assemblies and motor-current/fuse/wire selections remain open. Physical K1-open feedback intentionally starts unsafe on GPIO27; future commissioning requires the hardware power-arm and RESET/ARM sequence in ASSEMBLY_GUIDE.md, not a bypass of GPIO27. Serial ESTOP disables EN but does not electrically isolate the live motor bus.
