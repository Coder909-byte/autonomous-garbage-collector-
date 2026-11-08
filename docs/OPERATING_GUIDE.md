Current E2 evidence: [FINAL_GO_NO_GO.md](FINAL_GO_NO_GO.md), [READY_TO_WIRE.md](READY_TO_WIRE.md) and [SIMULATION_VERIFICATION.md](SIMULATION_VERIFICATION.md). U2 adds powered-off ECHO isolation; all GPIOs/commands unchanged. Historical owner simulation reports below are not fresh runtime evidence.

# Autonomous Waste Collection Rover — one L298N

ESP32-WROOM-32 firmware plus a Wokwi **digital control-signal model** for four wheel motors, two brushes controlled together and an independently requested conveyor. Physical hardware is untested. Real ultrasonic ECHO wires stay disconnected: their exact module/output compatibility is unknown and no resistors or level shifters are available.

Read [WIRING.md](WIRING.md) for the final pin map and connection holds, and [TEST_MATRIX.md](../TEST_MATRIX.md) for the verification evidence. No second L298N is required by the proposed architecture. Its channel A carries both brushes in parallel; channel B carries the conveyor. Suitability remains pending summed motor currents and shared thermal limits.

## Build and test without hardware

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt -r requirements-design.txt
python3 scripts/sync_wokwi.py
.venv/bin/python scripts/verify.py
```

The verifier runs source/diagram checks, host tests, both `esp32dev` and `wokwi_compile` builds, and Wokwi lint if installed. Keep PlatformIO invocations sequential. It never uploads firmware or opens a physical serial port. PlatformIO Core is pinned to 6.1.18, Espressif32 to 6.12.0, and its Arduino core is 2.0.17. The 3.x compatibility branch is supplied but not compile verified here. No external Arduino libraries are needed.

Canonical code: `include/rover_control.h`, `include/rover_pins.h`, `firmware/rover.ino`. The Wokwi sketch is generated from these and checked for drift. Binaries/ELFs are under `.pio/build/`; validation logs are under `artifacts/`. Previous two-L298N logs are archived separately and do not verify this revision.

## Exact Serial Monitor commands

Use **115200 baud**, **Newline** (LF; CRLF also accepted), one command per line. Commands are case-insensitive with a 48-character limit. The following is for **simulation only** during this task.

After boot, with switch LEFT/healthy and three valid readings:

```text
ARM
AUTO
```

`ARM` alone stays stopped. `AUTO` starts autonomous obstacle avoidance. Both brushes and conveyor default OFF; AUTO does not automatically enable cleaning. For both while traveling forward:

```text
CLEAN ON
```

Independent auxiliary requests:

```text
BRUSH ON
BRUSH OFF
CONVEYOR ON
CONVEYOR OFF
```

They take effect only while armed and actually moving forward. Both brushes always share one channel. These commands do not extend the manual movement timeout.

To stop and latch the emergency state, either command is sufficient:

```text
STOP
```

```text
ESTOP
```

Both require the same recovery, after returning the E-stop switch LEFT/healthy:

```text
RESET
ARM
AUTO
```

`RESET` clears a latch only with healthy feedback while disarmed; it never arms or moves the rover. `ARM` is rejected while latched. `DISARM` clears AUTO and both auxiliary requests. `S` is a non-latching stop that exits AUTO. `MANUAL` also exits AUTO and stops; after ARM, use `F`, `B`, `L`, `R` for supervised manual motion and resend within 1.2 s. Missing/invalid commands never refresh the deadman.

Boot is DISARMED; GPIO14 disables all drivers whenever stopped. Every new motion has a 100 ms neutral interval. GPIO27 is now E-stop feedback with internal pull-down; GPIO39 and GPIO26 are unused. Physical reset-safe enables have **not** been established with available parts.

AUTO stops at front ≤35 cm or either side ≤20 cm and settles 180 ms. If still blocked, it chooses the clearer side only when that side is >45 cm and both sides >20 cm; left wins ties. The output interlock holds EN low for 100 ms before the turn. The 540 ms turn timer starts when the adapter reports the turn outputs enabled, so dead time no longer consumes the turn duration. Lost side clearance can end a turn early. It then stops in REASSESS for at least 180 ms and requires a new reading from **each** sensor taken after that stop before selecting another motion. Forward recovery requires front >45 cm and both sides >20 cm, providing hysteresis against threshold jitter. At most three unsuccessful turn attempts are allowed per avoidance episode; persistent obstruction then disarms with `nav=TURN_LIMIT`. Clearing the distances alone cannot restart it: use ARM then AUTO. All three sensors must remain valid/fresh in every navigation phase; invalid/stale data disarms with `nav=SENSOR_FAULT` and requires new ARM/AUTO commands. There is no rear/cliff sensing, wheel feedback, battery monitoring, motor-current/jam monitoring, waste identification or external AUTO heartbeat. Manual motion is open loop.

## Wokwi

Copy `wokwi/sketch.ino`, `diagram.json` and `libraries.txt` into a Wokwi ESP32 project, or open `wokwi/` with Wokwi for VS Code after building `esp32dev`. No resistor components are included. Direct virtual ECHO and LED connections are simulation abstractions and must never be copied into physical wiring. LEDs indicate four wheel directions, both shared brushes, conveyor and EN; they do not model motor current, torque or motion. The logic analyzer records:

| Channel | Signal |
|---|---|
| D0 / D1 | Left FWD / REV PWM |
| D2 / D3 | Right FWD / REV PWM |
| D4 | Shared driver EN |
| D5 | Both brushes, L298N channel A |
| D6 | Conveyor, L298N channel B |
| D7 | E-stop healthy GPIO27 |

Switch LEFT = healthy; RIGHT = stop. Sensor sliders change front/left/right distance. `STATE motion=... en=... brush=... conveyor=... nav=... ms=...` reports applied output/navigation changes with millisecond timestamps; `DIST` reports distances periodically. LED/PWM indicators represent control outputs, not simulated mechanics.

Eight automated runtime cases are prepared by:

```sh
python3 scripts/run_wokwi.py --prepare-only
```

Once a Wokwi CI token is configured **locally** as `WOKWI_CLI_TOKEN`, run:

```sh
python3 scripts/run_wokwi.py
```

The runner uses scene-specific distances, serial/pin assertions and VCD checks for actual PWM activity, wrong/opposing directions and independent auxiliaries. It only accesses Wokwi, not a real rover. Runtime logs/results are under `artifacts/wokwi-scenarios/`. No token is configured here: these cases are prepared but **not executed**, regardless of host/build success. The owner's manual pass results for startup, three readings, ARM/AUTO, forward, left/right avoidance, brushes, conveyor and emergency-stop/no-restart are recorded in the test matrix for the version before the turning update. The latest owner request reports functional Wokwi testing complete; no new local CLI or quantitative timing run is recorded.

For the STOPPED/LEFT or STOPPED/RIGHT investigation and expected new phase sequence, see [TURNING_REVIEW.md](TURNING_REVIEW.md). Fixed Wokwi distance sliders do not change automatically with a turn: a static blocked scene can legitimately cause bounded turn/stop/reassess cycles; this is not repeated interlock switching during one turn.

## Electrical assembly package E2

Start with [FINAL_WIRING.md](FINAL_WIRING.md), the [38-page PDF wiring package](diagrams/electrical_package.pdf), [diagram index](diagrams/INDEX.md), [80-step assembly guide](ASSEMBLY_GUIDE.md), and [open electrical blockers](ELECTRICAL_BLOCKERS.md). GPIOs and firmware are unchanged; the proposed non-inverting buffers/protection are separate physical hardware, not Wokwi parts. Do not copy virtual ECHO/LED connections into the rover.

The package has no physically approved connections. Exact motor/current/battery/module ratings and actual protection hardware must be established before wiring/energizing affected branches. K1-open physical boot intentionally gives unsafe GPIO27 feedback; the guide distinguishes hardware power-arm from RESET/ARM.

Optional regeneration (uses pinned PDF tooling; never uploads or powers hardware):

```sh
.venv/bin/python -m pip install -r requirements-design.txt
.venv/bin/python scripts/generate_wiring.py
python3 scripts/check_electrical.py
```

Source data: `electrical/design.json`; filterable `connections.csv`, `terminal_map.csv`, `bom.csv` and the unfilled `current_budget.csv`. KiCad is unavailable here; no KiCad/ERC/PCB footprint verification is claimed.
