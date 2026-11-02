# Engineering review — one L298N and electrical E1 revisions

The current firmware, generated sketch, diagram, pin definitions, PlatformIO configuration, all wiring/test documents, scripts and host tests were inspected. The owner confirmed one L298N and no resistors/level shifters. This revision supersedes the earlier two-L298N physical plan.

| Finding | Correction / disposition |
|---|---|
| Previous design used six auxiliary GPIOs and two L298Ns | One L298N: GPIO21/22 → IN1/IN2, both brushes parallel on channel A; GPIO23/25 → IN3/IN4, conveyor on channel B. Shared EN is GPIO14. |
| Independent brush/conveyor commands missing | Added BRUSH ON/OFF and CONVEYOR ON/OFF. CLEAN ON/OFF remains a both-channel convenience. Actual auxiliary outputs retain armed/forward-only gating and are low through neutral, turns, reverse and stop. |
| GPIO39 needed an unavailable external pull-down for NC E-stop sensing | Moved E-stop input to freed GPIO27 with internal pull-down. Old GPIO26/39 connections are removed. Physical reset-safe motor enables remain unqualified; they are not solved by this change. |
| Wokwi included resistors contrary to the current constraints | Removed every resistor. SPDT E-stop selects 3V3/GND. Virtual LEDs connect directly as diagnostic abstractions; analyzer exposes eight signals. No corresponding physical LED circuit is proposed. |
| Generic HC-SR04 name cannot identify exact output voltage | Owner confirms manufacturer/variant/datasheet unknown. Physical ECHO lines stay disconnected, with no exception inferred from successful simulation. Firmware and simulator work continue. |
| Summed brush current unknown | Shared channel-A arrangement explicitly unverified until combined running/start/stall current and shared module heating are established. No approval from voltage/RPM or chip headline current alone. |
| Short turns could be missed by 500 ms logs | Added event telemetry for applied motion, EN, brushes and conveyor, including the neutral interval. |
| Wokwi evidence updated by owner | Manual startup, three ranges, ARM/AUTO, forward, left/right avoidance, brush/conveyor activation, ESTOP and no-auto-restart passed before the turning update. Automated CLI execution remains unavailable without a token. The latest electrical-design request reports functional Wokwi completion; no independent quantitative timing trace is available. |
| Safety behavior must survive refactor | Disabled boot, explicit ARM, latched STOP/ESTOP, RESET without auto-arming, invalid/stale sensor disarm, direction neutral interval and manual deadman retained and tested. |

The earlier one-L298N software revision introduced no extra driver or buffer. Electrical E1 now proposes the additional non-inverting U1 interface, default-low resistors, ECHO dividers and independent cutoff/protection functions detailed in FINAL_WIRING.md. These are missing or unselected physical parts, not working inventory or additions to Wokwi. The one L298N arrangement is a proposed control architecture, not a claim of a safe electrically assembled rover.

Historical first-pass fixes retained include rollover-safe timers, bounded serial parsing/overflow disarm, no manual-timeout extension by invalid commands, reset of modes on ARM, per-sensor freshness, checked PWM allocation and version-aware LEDC calls. Historical logs are archived separately. Build/host evidence and runtime/physical gaps are recorded in TEST_MATRIX.md.

## Turn/stop alternation investigation

Fixed blocked readings reproduced an unbounded loop of 440 ms enabled turns, stops and retries in the previous controller. The 100 ms interlock was consumed inside a 540 ms request timer, and another attempt could reuse pre-stop readings. The updated controller separates SETTLE, TURN_DEAD_TIME, TURNING and REASSESS; starts the 540 ms timer from software-applied EN feedback; waits for three post-stop readings; uses front-clear hysteresis; and disarms after three unsuccessful attempts. Emergency stops and invalid/stale samples preempt every phase. No new delay or GPIO/hardware changes were introduced. See TURNING_REVIEW.md and the 20 dedicated navigation plus three firmware-adapter regressions.

## Electrical E1 disposition

The actual firmware, pin definitions, generated Wokwi sketch and circuit were re-audited. All 16 GPIO assignments and working source hashes are preserved; no firmware refactor was required. The physical net model accounts for all seven motors, two bucks, three sensors and driver pins. Equal-net terminal schematics, physical harness layout, ESP32 chart, motor/power/sensor/cutoff diagrams and pin-to-pin tables derive from one source.

KiCad is unavailable, so editable SVG and PDF are supplied. All component footprints remain unassigned; exact module header positions and generic protection-assembly terminal mapping remain unresolved. Structural checks are not ERC or physical electrical approval. Both ESP32 environments compile, 79 C++ and 21 Python tests pass, and source/export connectivity checks pass. See TEST_MATRIX.md, ELECTRICAL_AUDIT.md and ELECTRICAL_BLOCKERS.md.

Physical release remains HOLD. All real ECHO connections stay disconnected. Shared L298N current/thermal suitability, module interfaces/reset behavior, pack protection, DC cutoff, fusing, wiring capacity, suppression and USB isolation require actual data/parts and staged measurements. Serial STOP/ESTOP disables outputs but does not open K1; the independent S2 circuit must be physically qualified. No upload, battery connection or motor activation occurred.
