# Simulation verification — E2, 8 November 2026

**Current Wokwi runtime: NOT EXECUTED.** `scripts/run_wokwi.py` was attempted; the local runner reports `WOKWI_CLI_TOKEN is not configured`. Eight scenarios are prepared and CLI lint can check structure. Neither compilation nor host tests count as a Wokwi runtime PASS. Earlier manual successes are owner reports for earlier tests, not fresh quantitative evidence for this package. Physical electronics remain untested.

## Reproduce without hardware

From the repository, run `.venv/bin/python scripts/verify.py` to compile both targets and execute host tests. Run `.venv/bin/python scripts/run_wokwi.py --prepare-only` to create eight scenes. With a valid token configured locally (never committed), run `.venv/bin/python scripts/run_wokwi.py`; inspect `artifacts/wokwi-scenarios/results.json`, per-case logs and VCD. Prepared files are ignored runtime artifacts. A failed/absent run must remain NOT EXECUTED or FAIL according to its evidence.

For manual simulation, build `esp32dev`, open `wokwi/` in Wokwi VS Code or copy the generated `sketch.ino`, `diagram.json`, and `libraries.txt` into an ESP32 project. The generated sketch matches canonical firmware. Use 115200-baud serial with LF. Start a new simulation for each independent row unless it explicitly describes recovery. E-stop switch LEFT is HIGH/healthy; RIGHT is LOW/stop. Three sensor controls are front/left/right, in cm. Wait for all three `DIST` values before AUTO. Send separate command lines. `STATE` changes expose motion/en/brush/conveyor/nav/time; logic analyzer D0/D1 left forward/reverse, D2/D3 right, D4 enable, D5 brush, D6 conveyor, D7 healthy feedback. Retain serial logs and exported traces; write actual result/date in the blank evidence worksheet below.

Physical U1/U2 are represented by ideal non-inverting digital paths. Direct virtual ECHO/LED connections are abstractions. K1, battery, current, heat, contact timing, sensor analog levels and mechanical motion are **not modeled**. A Wokwi pass would verify digital firmware behavior only.

## All 23 requested checks

Every runtime result below is currently **NOT EXECUTED**. Host tests covering related behavior are separately identified in native test sources and the final verdict; no row inherits a runtime PASS from them.

| # | Check | Reproducible action | Expected result / evidence to retain |
|---|---|---|---|
| 1 | Initial disarmed startup | Healthy switch, distances 100/100/100, restart simulation | READY DISARMED, all PWM/aux/EN LOW until explicit motion |
| 2 | ARM | Send ARM after row 1 | OK ARM; no movement and EN LOW |
| 3 | AUTO | After ARM, valid 100/100/100, send AUTO | FORWARD after neutral; EN HIGH, D0/D2 PWM, D1/D3 LOW |
| 4 | Forward and reverse | ARM, F; observe then send B | F uses D0/D2; B uses D1/D3 after >=100ms disabled neutral; stop by 1200ms since last accepted movement |
| 5 | Left turn | Restart; set 20/100/60, ARM, AUTO | SETTLE then TURN_DEAD_TIME then LEFT: D1/D2 PWM; auxiliary LOW |
| 6 | Right turn | Restart; set 20/60/100, ARM, AUTO | RIGHT: D0/D3 PWM; other direction pins LOW |
| 7 | Front obstacle | Start AUTO 100/100/100, then change front to 20 | Forward stops at next valid observation, >=180ms settle before requesting clearer-side turn |
| 8 | Blocked left | Restart 20/30/100, ARM, AUTO; separately try left=20 | Right selected at left=30; at either side <=20 the conservative policy stays stopped (no side-scraping pivot) |
| 9 | Blocked right | Restart 20/100/30, ARM, AUTO; separately try right=20 | Left selected at right=30; <=20 side stops both directions |
| 10 | All directions blocked | Restart 20/20/20, ARM, AUTO; observe >2s | EN LOW, no turn attempts while no safe path; remains waiting unless sensor fault disarms |
| 11 | Three-attempt recovery limit | Restart with constant 20/100/60, ARM, AUTO; leave values unchanged | Exactly three enabled LEFT intervals, each <=540ms target plus loop latency; stopped reassessment >=180ms with new reading from each sensor; then TURN_LIMIT disarmed. Clear sliders: no restart without ARM/AUTO |
| 12 | Brush only | Restart 100/100/100, ARM, F, BRUSH ON | D5 HIGH, D6 LOW while forward; both virtual brush indicators share D5; stop after manual timeout |
| 13 | Conveyor only | Same, CONVEYOR ON | D6 HIGH, D5 LOW while forward |
| 14 | Simultaneous cleaning | Same, CLEAN ON, or BRUSH ON then CONVEYOR ON | D5 and D6 HIGH while forward; no stationary/turn/reverse cleaning |
| 15 | Emergency stop | While moving, toggle switch RIGHT | D7 LOW, EN immediately cleared at firmware ISR boundary; all outputs stop next application; ESTOP latched |
| 16 | Stop during turn | Use row 5, toggle switch RIGHT during enabled LEFT | EN LOW, no continued turn; restoring switch cannot restart |
| 17 | Stop during cleaning | Use row 14 then physical switch; repeat fresh run with serial ESTOP | EN/aux/PWM disabled; both latch firmware state. Simulation does not prove physical K1 power removal |
| 18 | Restart rejection | After ESTOP, switch healthy, send ARM, F, AUTO, CLEAN ON; then RESET; then ARM | Motion/clean requests rejected while latched; RESET stays disarmed; ARM stays stopped until new motion. RESET rejected when switch unsafe |
| 19 | Sensor failure | Start AUTO clear, change a sensor control to 0cm if simulator permits, or use a scene with one ECHO connection removed before starting | Invalid/no echo -> SENSOR_FAULT disarm; EN/aux LOW. If 0cm is clamped to a valid range, it is not a fault injection; use disconnected ECHO scene |
| 20 | Sensor recovery | Following fault, restore a valid sensor/scene; for changed connectivity restart then repeat fault/recovery with an injectable scene | Healthy readings alone never restart the disarmed controller; explicit ARM then AUTO required. Connection-edit restart is only a reboot test; host sensor-recovery regression supplies this behavior if runtime injection unavailable |
| 21 | Driver-disable timing | Record analyzer trace for physical feedback LOW and for STOP, DISARM, S, timeout | No EN after physical falling ISR until deliberate RESET/ARM/motion; measure actual latency. Serial processing can wait up to one 25ms pulse timeout plus loop/serial work; do not claim physical cutoff time |
| 22 | Neutral interval | ARM/F, then B or L; export analyzer trace | All driver enables LOW for >=100ms between new-motion request and assertion; no opposing PWM simultaneously enabled. 100ms is electrical dead time, not proof rotor stopped |
| 23 | Software power-reset startup | While AUTO and cleaning active, restart simulation | New controller disarmed and auxiliary requests cleared; no auto restart. This tests reconstruction only, not brownout or boot-pin electrical glitches |

For sensor fault/recovery, a Wokwi sensor model that clamps distance controls may require manual disconnection of its ECHO wire while paused, if supported by the chosen editor/runtime. If live editing/injection is unsupported, retain runtime NOT EXECUTED for that row; host regression is separate evidence. No custom simulator capability is assumed.

## Timing evidence and current tooling limits

The eight automated scenes are auto_forward, auto_left, auto_right, obstacle_no_path (20/45/45), emergency_and_reset, brushes_only, conveyor_only and manual_deadman. They are a subset, not complete 23-case automation. Their VCD validator checks observed PWM channels, opposing-direction exclusion and auxiliary channels; **it does not independently calculate neutral intervals, interrupt latency, 540ms turn duration or three-attempt count**. Measure those from timestamped traces/serial logs with the manual procedure. Synthetic VCD unit tests validate the checker, not an ESP32 simulation.

| Runtime evidence record | Value |
|---|---|
| Current runner result | NOT EXECUTED; token unavailable |
| Simulator / firmware revision | Pending actual run |
| Run date, operator, case numbers | Pending actual run |
| Serial and VCD artifact paths | Pending actual run |
| Measured neutral / turn / feedback-disable times | Pending actual run |
| PASS / HOLD / FAIL with observed deviations | HOLD until execution |

The full host verification results and build scope are in [FINAL_GO_NO_GO.md](FINAL_GO_NO_GO.md) and `artifacts/verification-summary.json`.
