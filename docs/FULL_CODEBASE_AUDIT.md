# Full codebase audit — 10 November 2026

Initial branch `main`, HEAD `2da0b0a6c700491c66b8330811afd8091ed3638b`, clean working tree. `git fetch origin` confirmed the same remote head. No existing work was discarded. The recursively read tracked-file inventory, hashes, line counts and source references are in `audit_inventory.json`; binary drawings were inspected using PDF text/structural validators rather than treated as source code. Existing 74-page `artifacts/TEAM_ASSEMBLY_HANDOVER.pdf` is a frozen E2 handover.

## Baseline findings

| Finding | Evidence at baseline | Disposition |
|---|---|---|
| Main firmware exists and is functional | `src/main.cpp:1` includes `firmware/rover.ino`; `platformio.ini:4` pins Espressif32 6.12.0 | Preserve controller and adapter behavior |
| GPIO map matches requested 16 assignments | `include/rover_pins.h:3–12`; `scripts/check_project.py` expected-map contract; `electrical/design.json` gpio_bindings | Preserve byte-for-byte pin header |
| Startup, physical feedback, latched E-stop and gated enable implemented | `firmware/rover.ino` setup, stopInterrupt, applyOutputs; `include/rover_control.h` emergency, command, tick | Preserve; physical cutoff is independent and unverified |
| Manual commands, 1200ms timeout, neutral interval and forward-only independent cleaning implemented | `include/rover_control.h` Controller::command/tick, MotionGate::update; `firmware/rover.ino` applyOutputs | Original native regression tests cover these behaviors |
| AUTO navigation implemented | `include/rover_control.h` Controller::tick/reportApplied/beginReassessment; `test/test_turning/test_main.cpp` | Settling, applied-time turn duration, fresh reassessment, three-attempt limit and sensor-fault disarm retained |
| Parser bounded and command ACKs available | `include/rover_control.h` LineParser::feed; `firmware/rover.ino` loop | 48-character lines; overflow disarms; OK/ERR text compatibility retained |
| Laptop telemetry insufficient | `firmware/rover.ino` DIST periodic message lacks version/firmware ID, sample ages, requested auxiliaries and healthy feedback; STATE is event-only | Add periodic versioned JSON reflecting applied adapter outputs; retain DIST/STATE |
| No ESP32-CAM implementation | Entire initial inventory contains only main and Wokwi firmware | Implement separate supported AI-Thinker configuration, actual module compatibility pending identification |
| No laptop interface or serial bridge | Initial inventory has no apps/package.json/React/serial backend | Implement loopback bridge and React dashboard |
| No laptop simulation integration | `wokwi/`, `scripts/run_wokwi.py` cover controller simulation only; token-dependent runtime not evidenced | Add native C++ serial simulator sharing controller and protocol serializer |
| Electrical camera branch absent | `electrical/design.json` has 87 components, 72 nets and a reserved, disconnected CAM1; `electrical/current_budget.csv` has unknown MCU/logic/current budgets | Add separately protected third regulator branch in a canonical system overlay; preserve E2 wire IDs |
| Physical release blocked | `docs/FINAL_GO_NO_GO.md`, `docs/READY_TO_WIRE.md`, `docs/FINAL_PURCHASE_LIST.md` | P1/OV1/OV2/K1, fuse/current/thermal choices, USB backfeed and real interfaces remain HOLD |
| Installed firmware is older | `docs/TEAM_HANDOVER.md`, checkpoint F | No upload or hardware connection during this work |
| Handover checker freezes firmware source | `scripts/check_team_handover.py` check compares AUTHORITIES with d6cd479 | Adapt verification to validate frozen handover against its Git baseline, while preserving live electrical sources and separately testing new software |
| Wokwi runtime evidence missing | `scripts/run_wokwi.py`, `artifacts/wokwi-runtime.log`, `docs/SIMULATION_VERIFICATION.md` | CLI lint is available; do not claim fresh Wokwi runtime without a token |

## Initial verification

Executed `.venv/bin/python scripts/verify.py` before edits: existing native/Python checks and both firmware builds pass; Wokwi lint reports one informational legacy-board notice. Exact fresh results are collected again in the final report. These tests prove software properties within mocks, not motor operation, power integrity, contact opening, physical serial communication or camera performance.

## Architecture decision

USB serial remains the control path at 115200 baud. Main ESP32 remains final safety authority. Separate camera uses trusted local Wi-Fi. Browser requests carry a short manual intent lease; backend ceases motion heartbeats if lease renewal stops. No automatic ARM, RESET, AUTO or movement on reconnect. Local same-origin operator connection has exclusive control. Software ESTOP is labeled distinctly from physical motor-power isolation.

Final feature status, implementation references, tests and remaining physical acceptance procedures are in `FINAL_SYSTEM_IMPLEMENTATION_REPORT.md` and `SERIAL_PROTOCOL.md`.

## Final implementation cross-reference

The final main adapter adds telemetry only (`firmware/rover.ino::applyOutputs/loop`, `include/rover_telemetry.h::telemetry`). The controller and GPIO header remain unchanged. Camera initialization/network/HTTP logic is in `camera/src/main.cpp::setup/loop/statusHandler/snapshotHandler/streamHandler/settingsHandler`, board selection in `camera/include/board_ai_thinker.h`, and bounded reconnect/resource policies in `camera_policy.h`.

Bridge safety and handshaking are in `apps/rover-bridge/src/bridge.ts::Bridge.connect/command/hold/watchdog/receive/disconnect`; exclusive port ownership and mock transport in `transports.ts::Hardware/Simulation`; local authorization in `server.ts::makeServer`; camera address/endpoint validation in `camera.ts::cameraAddress/cameraPath/proxyCamera`. Runtime contracts and malformed telemetry rejection are in `packages/protocol/index.ts::telemetry/parseLine/isState`. Dashboard keyboard/pointer/focus lifecycle is in `apps/rover-dashboard/src/App.tsx::App` and `control.ts::HoldControl`; camera failure UI is in `App.tsx::Camera`.

Native simulation is `scripts/simulation/rover_sim.cpp::main`. Additive electrical source/export validation is `scripts/generate_system.py::load/generate`, `scripts/check_system.py::check/main`, and `test/test_system.py`. Existing `scripts/generate_wiring.py::Drawing` only gained optional revision/date labels so S1 sheets do not falsely display E2's date. Frozen handover verification is `scripts/check_team_handover.py::check/input_hash_matches`; firmware is checked against its archived baseline and CSV line-ending equivalence remains content-sensitive.

Final observed results: 84 native, 54 Python, 56 TypeScript/integration/component and four real-browser cases pass; two camera host executables pass; both main firmware environments and the supported camera environment compile. Production serving smoke test and dependency audit pass. Exact evidence, classifications, build sizes, known limits and physical acceptance steps are in `FINAL_SYSTEM_IMPLEMENTATION_REPORT.md` and `artifacts/system/summary.json`. No baseline actuation bug required a controller rewrite; fixes addressed the missing integrations and demonstrated implementation/portability defects.
