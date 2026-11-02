# Actual-project electrical audit — 2 November 2026

Read/reviewed: `firmware/rover.ino`, `include/rover_pins.h`, `include/rover_control.h`, generated `wokwi/sketch.ino`, `wokwi/diagram.json`, `wokwi/wokwi.toml`, `platformio.ini`, `src/main.cpp`, current wiring/turn/test documents, relevant generator/checker and host-test sources. The sketch synchronization check confirms the standalone file exactly derives from the canonical firmware. No firmware or GPIO reassignment is needed for E1.

| Firmware signal | GPIO | Physical E1 route | Audit |
|---|---|---|---|
| L_FWD / L_REV | 16 / 17 | U1 2->18 / 4->16 -> left RPWM/LPWM | Two independent PWM signals; WROOM-32 target, not PSRAM-reserved module |
| R_FWD / R_REV | 18 / 19 | U1 6->14 / 8->12 -> right RPWM/LPWM | Independent PWM pair |
| ENABLE | 14 | R5 default-low -> U1 11->9 -> S2 enable NC -> four BTS EN + L298 ENA/ENB | Software behavior agrees; electrical fanout/reset behavior remains unverified |
| BRUSH_IN1 / IN2 | 21 / 22 | L298 IN1/IN2 -> shared OUT1/OUT2 brush pair | IN2 held LOW; no second L298N |
| CONVEYOR_IN3 / IN4 | 23 / 25 | L298 IN3/IN4 -> OUT3/OUT4 conveyor | IN4 held LOW; voltage/current still unknown |
| TF / EF | 32 / 34 | U1 trigger; R23/R24 ECHO divider | GPIO34 input-only; ECHO blocked pending hardware |
| TL / EL | 33 / 35 | U1 trigger; R25/R26 divider | GPIO35 input-only; ECHO blocked |
| TR / ER | 13 / 36 | U1 trigger; R27/R28 divider | GPIO36/VP input-only; ECHO blocked; no JTAG GPIO13 |
| ESTOP_OK | 27 | Isolated S2 NC + K1 sense NO -> GPIO27 | Internal pull-down; LOW latches stop. K1-open physical boot intentionally unsafe. |

All 16 assignments are unique and agree with code and the Wokwi pin aliases Dxx/RX2/TX2/VP. The diagram has no resistor components, real motor-power models or physical voltage-protection representation. Its direct ECHO/LED wires are virtual signal abstractions. E1 adds only a **separate physical design**, not resistors to the simulator. Signal polarity is preserved by the non-inverting buffer; emergency contact gating only adds a disable condition.

## Missing, unassigned and conflicting electrical details

- GPIO26, GPIO39/VN and GPIO4 are unassigned to application functions. Serial GPIO1/3 are reserved for communications; boot straps GPIO0/2/5/12/15 and flash GPIO6–11 remain unused. Leave unlisted actual headers unconnected. EN/reset follows the DevKit circuit, not motor enable. No ESP32-CAM power/GPIOs are assigned.
- No firmware GPIO conflicts were found. Raw 5V ECHO or a hard-HIGH EN jumper would create an electrical conflict despite the valid pin map. Missing level translation, receiver pulls and common-reference details were not established by the previous direct/provisional GPIO wiring plan.
- Exact DevKit header positions, both IBT-2 buffers, L298 jumpers/regulator/diodes, buck boards, motor labels/currents and battery data are unknown. Physical connector order, wire ratings, fuse values, contactor/supervisor selection and actual electrical continuity cannot be inferred from module names.
- All seven motors are now accounted for explicitly: M1/M2 left, M3/M4 right, M5/M6 shared brushes, M7 conveyor. All driver VCC/GND/EN/PWM/direction/motor/power terminals are accounted for; unused BTS R_IS/L_IS are no-connect. L298's two channels are both used.
- E1 explicitly adds required protection functions and opens blockers for missing hardware. It does not claim stock parts contain safe default enable pulls, a cell-level cutoff, correct fuses, rail overvoltage protection or an independent E-stop circuit.
- The common-ground plan requires actual BTS logic/power-ground and buck-negative bonds to be checked; do not create thin duplicate motor returns. All high-current distribution/returns are separate from the MCU/breadboard paths.

## Working software retained

Four 1.2 kHz/8-bit PWM channels, mutual direction interlocking, disabled startup, explicit ARM, latched STOP/ESTOP, reset without motion, independent forward-gated auxiliary requests, manual deadman, and invalid/stale sensor protection are retained. The latest non-blocking turn phases are retained unchanged. Firmware sees only a healthy/unsafe GPIO27; the proposed series K1 feedback ensures any contactor dropout also presents unsafe feedback. The software cannot prove a real contact closed or motor stopped.

P1/OV1/OV2 are **required functional contracts with unselected implementations**, not invented commercial products. K1/S2 labels are functional contact roles until real parts are selected. PCB footprints and physical connector orientation are deliberately unassigned. The terminal-level schematic is complete as a proposal; the missing exact specifications prevent final electrical release. See FINAL_WIRING.md and ELECTRICAL_BLOCKERS.md for dispositions.
