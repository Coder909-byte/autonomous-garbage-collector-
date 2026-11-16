# Laptop monitoring integration — 16 November 2026

The laptop stack is prepared for software-only operation and subsequent staged hardware acceptance. This session did not open a physical serial device, upload either firmware, energize motors, or observe a physical rover. The user reports successful main-firmware flashing and startup/telemetry verification on another laptop. That report supersedes older installation assumptions, but is not a measurement made in this session.

## Audit and justified changes

| Component | Existing functionality | Changes in this task |
|---|---|---|
| Main ESP32 | Canonical `firmware/rover.ino`, `rover_control.h`, fixed GPIOs; disarmed startup, GPIO14 gate, GPIO27 falling-edge trip, physical-feedback priority, 100 ms neutral interval, 1200 ms manual timeout, AUTO freshness fault disarm | No firmware, pin, controller, telemetry serializer or PlatformIO configuration changes |
| Telemetry | 115200 baud; `TEL ` plus JSON with `v:1`, firmware identity, requested/applied output, ranges/ages, cleaning and safety; separate ACKs | Existing validation preserved; browser state validation also checks port/error types |
| Node bridge | Exclusive enumerated serial port; allowlisted commands; 300 ms browser lease, 200 ms serial renewal, 1500 ms stale disconnect; STOP/DISARM on connect/close; no automatic rearm | Five-second incomplete-handshake deadline; cancelled old open failures cannot disconnect a later session; current console resets per session while diagnostics retain earlier sessions |
| Dashboard | ARM/DISARM, MANUAL/AUTO, hold controls, requested/applied cleaning and motion, sensor cards, serial log, WebSocket recovery, software ESTOP distinction | Three-second port discovery with manual choice; handshake status; stale safety/mode indicators become unknown; top-level firmware safety faults; separate GPIO27 feedback and firmware latch; obstacle diagram and firmware-phase explanations |
| Simulator | POSIX child process running the actual controller, gate and telemetry serializer; clear/obstacle/fault/E-stop scripts; never auto-arms | Preserved; isolation is now explicitly tested against calls to the physical serial opener |
| ESP32-CAM | Separate AI-Thinker board profile, fixed JPEG/MJPEG/status/settings endpoints, PSRAM-aware settings, bounded WLAN retry, mutex/frame cleanup, private-subnet policy | Firmware/configuration unchanged; private numeric HTTP URL support added in bridge/UI, stricter status validation, decoded-video status and first-video timeout, timestamped JPEG filenames and bounded snapshot fetch |
| Diagnostics | Latest 150 serial log entries and seven state changes only; no recording/export | Bounded 10,000-record server buffer, UTC timestamps, source/session/port provenance, safety events and communication failures, CSV/JSON exports, last-120-sample trend chart with invalid-sensor gaps and session isolation |
| Electrical docs | E2/S1 netlists, diagrams, 74-page handover, pending physical records and B01–B14 blockers | Frozen authorities preserved; this report adds an acceptance checklist without changing their release status |
| Browser test infrastructure | Used the same ports as normal operation, allowing an existing operator tab to acquire a test bridge | Dedicated test ports 18787/15173 and production-smoke port 18788; normal run ports unchanged; one-operator guard preserved |

The existing engineering-panel layout was extended, rather than rebuilt. No AI navigation, object recognition, localization, encoders, current sensing or battery monitoring was invented. Applied motion is firmware software-output feedback, never proof that a wheel moved or motor power is isolated.

## Ready integrations and limits

- Dashboard → local WebSocket → bridge → native C++ simulator → telemetry/UI/diagnostic export is testable without motors or sensors. All four existing scenarios remain available. Scenario time starts at Connect; explicit ARM and AUTO are still needed. The obstacle scenario may exhaust its three-turn budget before the obstacle clears.
- USB software discovery, single-owner handling, handshake, timeout, unplug/reconnect and explicit rearm guards are covered using mocks. This Mac's actual USB data path needs a new hardware observation. Discovery merely lists ports; it neither opens nor identifies a board. The operator must choose the main ESP32, never its separate camera programmer.
- Camera frontend, proxy formats/timeouts, JPEG download and MJPEG rendering have automated mock/fixture coverage. The fixture is test-only and never appears in the shipped UI. Actual board identity, Wi-Fi, optics, PSRAM, continuous frame delivery and power/noise performance remain unverified. Camera failure does not stop onboard AUTO.
- Diagnostics are bounded in memory. Export before stopping the bridge; there is no durable database or indefinite recorder. Exports include retained records from multiple sessions, each labelled independently. Charts show the latest session only and remain historical after disconnect. Wall-clock timestamps are laptop receipt times; device `ms` is retained separately, without clock synchronization. Raw invalid range `-1` is retained, not converted into zero distance.
- On communication loss, STOP/DISARM is best effort. The browser lease and firmware manual timeout constrain MANUAL; AUTO can continue onboard when a stop cannot be delivered. Use the physical cutoff for power isolation.

## Run on the Intel Mac

Verified environment: Intel `x86_64`, Node v24.14.1 (project minimum 22.12). Existing npm, Python/PlatformIO and Apple C++ dependencies were used.

```sh
cd /Users/kokila/Downloads/autonomous_rover_build
npm run sim:build
npm run build
npm start
```

Open **http://127.0.0.1:8787**, keep one operator tab open, select **Offline simulator**, choose a scenario and **Connect rover**. Confirm the SIMULATION MODE banner and disarmed/STOPPED/EN LOW before deliberately trying simulator ARM or AUTO. This server binds to loopback and never connects a rover by itself.

On a fresh checkout, first run `npm ci`; install Apple's Command Line Tools if `c++` is missing. For development, run `npm run bridge` and `npm run dashboard` in separate terminals, then open **http://127.0.0.1:5173**. Browser tests use dedicated ports 18787/15173 to avoid existing operator tabs; keep those test ports free. See [laptop setup](LAPTOP_CONTROL_SETUP.md) for Python dependencies and troubleshooting.

Run all software checks without replacing earlier commissioning logs:

```sh
.venv/bin/python scripts/verify_monitoring.py
```

Each run writes logs, exit codes and protected-source hashes into `artifacts/monitoring-validation/<UTC timestamp>/`. Google Chrome is the default browser; `CHROME_PATH` can select another installed Chromium executable. Wokwi lint runs when its CLI exists; Wokwi runtime is not performed.

## Hardware connection checklist — future staged acceptance

This is a checklist for the wiring team's released procedure, not approval to energize a stage. Existing [electrical blockers](ELECTRICAL_BLOCKERS.md), [assembly guide](ASSEMBLY_GUIDE.md) and [team handover](TEAM_HANDOVER.md) remain authoritative. Record actual measurements and reviewers; simulation cannot close a physical checkpoint.

1. **Before connection:** identify the actual DevKit, drivers, seven motors, buck converters, camera and connector terminal maps. Verify polarity, continuity, common-ground paths, protected rails, current/voltage ratings and the applicable B01–B14 gates. Keep motor/battery power isolated for laptop bring-up. Qualify USB/backfeed and partial-power behavior before combining USB with an external supply. Do not wire raw 5 V ultrasonic ECHO to the ESP32 or bypass the documented conditioning/default-low networks.
2. **Confirm the unchanged main pin contract:** wheels left 16/17 and right 18/19; brush 21/22; conveyor 23/25; driver enable 14; safety feedback 27; ultrasonic TRIG/ECHO front 32/34, left 33/35, right 13/36. Verify the separate camera mapping independently; its GPIO numbers are not main-board assignments.
3. **USB-only observation:** close PlatformIO monitors/uploaders and other bridges. Select the physically identified main port; open it deliberately. Observe fresh `TEL {"v":1,...}` and `fw:"rover-usb-v1"`. Expect DISARM acknowledged, armed false, applied STOPPED and EN LOW. GPIO27 absent/LOW should show an unsafe latched state; never jumper it or reset it merely to enable controls. Export this hardware-labelled session.
4. **Qualified logic/sensor checks with motor power isolated:** verify GPIO14 LOW during startup, reset, brownout and disabled states, and all drive/auxiliary outputs inactive. Under the released electrical test procedure, verify GPIO27 feedback and its independent physical trip path. Check all three sensors with known targets, missing ECHO and stale readings, including the 500 ms freshness bound and crosstalk. Confirm front/left/right are not swapped.
5. **Loss/recovery checks:** disconnect/reconnect USB and restart the dashboard under the same isolation conditions. Confirm delivery uncertainty is visible, reconnect is deliberate, STOP/DISARM handshake repeats, and no ARM/AUTO/cleaning/movement is replayed. Exercise manual timeout only at an explicitly approved commissioning stage; do not infer it from UI state.
6. **Separate camera:** qualify its protected supply and actual board type before any camera programming or power stage. Confirm private WLAN/subnet settings and camera IP, then verify stream, snapshot, disconnect, settings and recovery after Wi-Fi/power loss. Never flash camera firmware onto the main ESP32. Actual frame rate/latency and simultaneous stream/snapshot performance require physical testing.
7. **Before any motor-powered test:** obtain the required explicit approval and close the relevant electrical gates. The independent cutoff, contactor release, residual motor-bus voltage, GPIO27 trip and GPIO14 disable must be measured. Then follow the staged mechanical/load procedure for directions, stopping distance, wheel-pair currents, shared brush/conveyor L298 heating, noise and supervised AUTO. Do not treat software ESTOP, an ACK or `en:false` as measurement of disconnected motor power.

## Verification evidence

Final run: **all 16 checks passed**, with evidence in `artifacts/monitoring-validation/20261116T130959Z/`. The folder timestamp is UTC (16 November 2026, 18:39:59 India time at run start). `summary.json` contains every command/exit code and hashes proving the protected firmware/configuration sources stayed unchanged throughout the run. Git diff also shows no firmware, controller, pin, camera firmware/board or electrical-authority changes.

| Check / log basename | Final result | Scope |
|---|---|---|
| `source-contracts` | PASS | GPIO/source/Wokwi synchronization contracts |
| `electrical-contracts` | PASS | Existing electrical graph and protective-interface consistency |
| `native-tests` | **84/84 PASS** | Actual C++ controller and firmware-adapter host tests |
| `python-tests` | **54/54 PASS** | Existing electrical, waveform, export, system and handover regression tests |
| `design-exports` | PASS | Diagram/export integrity |
| `completion` | PASS | Existing completion-model consistency, not physical release |
| `main-builds` | PASS | `esp32dev` and `wokwi_compile`, compile only |
| `camera-build` | PASS | Separate `ai_thinker_esp32cam`, compile only |
| `wokwi-lint` | PASS | Diagram lint only; Wokwi runtime NOT RUN |
| `system-graph` | PASS | 211 records, original 201 preserved |
| `frozen-handover` | PASS | Frozen authorities and 74-page handover; physical records still pending |
| `simulator-camera-host` | PASS | Native simulator build and both camera policy/HTTP mock executables |
| `typescript-tests` | **74/74 PASS**, seven files | Protocol, bridge, reconnect races, timeout, simulated isolation, camera proxy, diagnostics/export, navigation and React state |
| `laptop-build` | PASS | TypeScript bridge and Vite production dashboard |
| `production-smoke` | PASS | Built page/asset/API served on isolated loopback; no physical device opened |
| `browser-tests` | **7/7 PASS** in installed Chrome | Control/release/blur, explicit reconnect/rearm, obstacle display, JSON/CSV downloads, mobile overflow, camera failures and decoded test-only MJPEG/JPEG |

Generated screenshots were visually reviewed for desktop and mobile, including disconnected unknown states and historical simulation trends. Evidence screenshots are under `artifacts/monitoring-validation/`: `dashboard-simulation.png`, `dashboard-navigation.png`, `dashboard-mobile.png`, and `dashboard-trends-mobile.png`. The export/browser scenario captures page errors and passed without a page error. Non-failing terminal warnings about `NO_COLOR`/`FORCE_COLOR` are present in the browser log.

Earlier results are preserved rather than hidden:

- Baseline simulator/camera host build and existing JavaScript suite passed (**56/56**) before changes.
- An intermediate frontend build failed because a type import reached a Node-only module. Moving the record type to the shared protocol package fixed the boundary; final builds pass.
- Two initial new reconnect fixtures attempted reopening before the mocked asynchronous close completed. Fixtures now wait for that close; the bridge continues refusing simultaneous owners. Subsequent unit runs passed (71, 73, then final 74 tests as coverage was completed).
- The first aggregate run (`20261116T130317Z`) failed its handover step because the new runner omitted the checker's import path. Correcting the runner produced an independent handover pass, then a full final pass; no frozen handover file was changed.
- That run's browser suite had **3 passes / 4 failures** because the normal-port bridge was unavailable to the test operator (403 lockout with proxy EPIPE errors, consistent with another reconnecting operator tab). Moving test infrastructure to isolated ports preserved the single-owner guard. An isolated 7/7 pass was followed by the final 7/7 pass above.
- Scoped source/documentation `git diff --check` passes. The unrestricted diff check reports existing trailing spaces in the pre-existing modified `artifacts/build.log`; those unrelated lines were left intact.

Earlier tracked artifacts and the two pre-existing USB commissioning documents were retained. No package/dependency change, data deletion, commit, push, firmware upload or physical motor command was performed. Real USB telemetry on this Mac, real camera performance and all electrical/mechanical acceptance remain **NOT VERIFIED** by this work.

React and full-flow checks used the [React review skill](/Users/kokila/.codex/plugins/cache/openai-curated-remote/vercel/0.54.1/skills/react-best-practices/SKILL.md) and [verification skill](/Users/kokila/.codex/plugins/cache/openai-curated-remote/vercel/0.54.1/skills/verification/SKILL.md). These do not confer a hardware release.
