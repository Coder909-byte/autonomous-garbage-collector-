# STOPPED / LEFT / RIGHT alternation investigation

Recorded 2 November 2026. This review concerns software and Wokwi control signals only. No hardware was uploaded, energized or electrically verified.

## Finding

The observed pattern is consistent with the previous navigation policy when a front obstacle stays present: complete a timed turn, stop, see the same blocked distances and request another turn. The interlock inserts one disabled interval at the start of each new motion; it does not independently oscillate during a stable turn request. Wokwi's sensor-distance settings do not automatically change to reflect a simulated heading change.

A deterministic host reproduction with front=20 cm, left=100 cm, right=100 cm produced:

```text
280 ms: LEFT
720 ms: STOPPED
1010 ms: LEFT
1450 ms: STOPPED
1740 ms: LEFT
2180 ms: STOPPED
```

The exact user's log timing cannot be established without timestamps or a waveform recording. Side-clearance loss or noisy measurements can also stop a turn early. The reproduction establishes the source-code behavior, not independent confirmation of a particular simulator recording.

Two weaknesses were corrected: the old 540 ms timer began with the turn request, consuming 100 ms of output dead time and leaving about 440 ms enabled; and the next turn could reuse pre-stop measurements without a bounded retry count. The previous logic was already non-blocking, but these phases were not separated adequately.

## Updated non-blocking phases

| Phase / telemetry | Outputs and transition |
|---|---|
| `CRUISE` | Forward until front ≤35 cm or either side ≤20 cm |
| `SETTLE` | All motor outputs disabled for at least 180 ms. If the front has cleared above 45 cm and both sides exceed 20 cm, resume forward without an unnecessary turn. Otherwise select the clearer side only when it exceeds 45 cm and both sides exceed 20 cm. Ties choose left. |
| `TURN_DEAD_TIME` | Turn requested, EN/PWM/auxiliaries disabled by the existing 100 ms output interlock. Sensor validity and side clearance remain checked. |
| `TURNING` | A single selected direction remains requested. Its 540 ms timer begins only when the output adapter reports applying that direction with EN permitted. Repeated output reports do not reset the timer. Lost side clearance stops it early. |
| `REASSESS` | Stop. Wait at least 180 ms **and a new reading from each of the three sensors after the stop**. Per-sensor sequence numbers prevent reuse of a still-fresh pre-stop frame. Choose forward only at front >45 cm with both sides >20 cm; otherwise select a safe new turn. |
| `TURN_LIMIT` | After three attempts without a newly assessed clear route, disarm and clear auxiliary requests. New distance values alone cannot restart. Fresh valid sensors plus explicit ARM and AUTO are required. A clear route found after the third turn can still recover before the unsuccessful-episode limit is applied. |
| `ESTOP` / `SENSOR_FAULT` | Emergency input/command or invalid/stale range preempts every active phase and disables outputs; there is no automatic recovery. |

The forward entry/exit thresholds provide hysteresis: start avoidance at front ≤35 cm; recover from avoidance only above 45 cm. This avoids repeated forward/stop transitions caused by small changes around 35 cm. Motion times are scheduled in the main loop; a stop occurs at the first evaluation at/after the target and can incur the existing single 25 ms echo timeout plus processing overhead. Output feedback is software feedback, **not an encoder or proof that a real wheel moved/stopped**. Electrical dead time and turn duration still require later physical calibration.

No navigation delay/sleep was added. The E-stop ISR still clears GPIO14 independently of sensor reads; serial work stays bounded. All phases retain invalid/stale-sensor checks before navigation decisions. Manual deadman, disabled startup, explicit ARM, output polarity interlocking, auxiliary gating, pin assignments and the resistor-free diagram are retained.

## What the new log means

```text
STATE motion=STOPPED en=0 brush=0 conveyor=0 nav=SETTLE ms=0
STATE motion=STOPPED en=0 brush=0 conveyor=0 nav=TURN_DEAD_TIME ms=180
STATE motion=LEFT en=1 brush=0 conveyor=0 nav=TURNING ms=280
STATE motion=STOPPED en=0 brush=0 conveyor=0 nav=REASSESS ms=820
```

These are illustrative host-model times, not a measured Wokwi/hardware trace. Repeated cycles are now bounded. In the asynchronous host reproduction, three 540 ms enabled turns are followed by `TURN_LIMIT`; see `artifacts/turn-investigation-after.log`. The pre-change trace is retained as `artifacts/turn-investigation-before.log`.

## Regression evidence and Wokwi follow-up

The 20 dedicated `test_turning` cases cover continuous left/right turns; duration measured after dead time; repeated feedback; three post-stop readings; minimum settling; clear-path recovery; threshold hysteresis; bounded retries both directions; new-direction selection; emergency and invalid/stale sensor preemption in every phase; timer rollover; early side-clearance abort; final-attempt recovery; clearing during initial settle; pending-turn safety; and STOP cancelling reassessment. Three additional firmware-adapter cases verify the timing through actual GPIO/PWM calls under host stubs, E-stop ISR preemption during an AUTO turn and disabled outputs on a reassessment sensor fault.

The owner manually confirmed startup, three distances, ARM, AUTO, forward, left/right avoidance, brush/conveyor activation, emergency stop and prevention of automatic restart **before this timing update**. Those results are recorded as owner-reported Wokwi passes in TEST_MATRIX.md. They do not verify the changed turn timing/reassessment implementation. The updated sketch must be retested in Wokwi; automated CLI execution still requires a token absent from this workspace.

On rerun, use the `nav`/`ms` fields and analyzer: confirm one continuous ~540 ms enabled turn after 100 ms neutral; a stopped reassessment before the next turn; disarm after three unsuccessful attempts with fixed blocked values; forward recovery only with front >45 cm; and ESTOP/sensor-fault interruption. No physical motor or LiPo connection is required for these simulation checks.
