# Final system implementation report — 10 November 2026

## Scope and source state

Audited baseline: `main`, `2da0b0a6c700491c66b8330811afd8091ed3638b`; initial working tree clean, origin confirmed by fetch. E2 engineering baseline `d6cd479` and the team handover were read rather than presumed to describe newer software. Implementation commits and the current software commit are recorded below after verification. No original work was discarded, hardware energized, serial device opened for control, or firmware uploaded. The main ESP32 therefore still contains its older program.

The full baseline inventory and source hashes are in `docs/audit_inventory.json`. Relevant inspected sources include `firmware/rover.ino` setup/loop/applyOutputs/stopInterrupt, `src/main.cpp`, `include/rover_control.h` Controller/LineParser/MotionGate, `include/rover_pins.h`, `platformio.ini`, all native/Python test modules, Arduino stubs, verification/export/handover scripts, Wokwi sketch/diagram/config/runner, electrical model/connection/terminal/BOM/budget/source files, READY_TO_WIRE, FINAL_WIRING, FINAL_GO_NO_GO, FINAL_PURCHASE_LIST, TEAM_HANDOVER, commissioning/operating/review documents and existing generated drawing/PDF contracts. Binary PDFs were checked for strict parsing, readable text, record coverage and drawing consistency; no actual part terminal photograph was available.

## Feature status

| Feature | Classification | Evidence and limit |
|---|---|---|
| Existing controller, GPIO map and motor-output behavior | IMPLEMENTED AND TESTED | Original Controller, MotionGate, GPIO header and E2 electrical sources unchanged; 84 native tests cover boot/interlock/manual timeout/AUTO/fault/stop/cleaning plus telemetry. Physical behavior remains unverified |
| Main periodic v1 telemetry | IMPLEMENTED AND TESTED | `include/rover_telemetry.h::telemetry`; `firmware/rover.ino::applyOutputs/loop` reports requested and adapter-applied outputs, healthy feedback, sample ages, identity; legacy commands/DIST/STATE retained |
| Camera firmware | IMPLEMENTED, HARDWARE TEST PENDING | `camera/src/main.cpp::setup/loop`, explicit `board_ai_thinker.h`; AI-Thinker build passes. Actual board/sensor/PSRAM identity remains unverified |
| Camera HTTP, memory cleanup and reconnect policy | IMPLEMENTED AND TESTED | Actual handlers compiled against host mocks in `camera/test/http_test.cpp`; policy/resource tests in `policy_test.cpp`. No real radio, sensor DMA or stream-performance test |
| Actual video streaming/snapshot on supplied hardware | BLOCKED BY SPECIFIC MISSING HARDWARE | No identified/attached camera and qualified independent supply/programmer. Endpoints/UI/proxy implemented; optical/video acceptance remains pending |
| Serial bridge and control protocol | IMPLEMENTED AND TESTED | `apps/rover-bridge/src/bridge.ts::Bridge`, `transports.ts::Hardware/Simulation`, shared `packages/protocol/index.ts`; driver mocks and real C++ mock-serial integration. No physical USB-to-ESP32 result claimed |
| Laptop dashboard | IMPLEMENTED AND TESTED | `apps/rover-dashboard/src/App.tsx`, `control.ts::HoldControl`; component/browser tests plus production serving smoke test. Desktop/mobile screenshots are simulator evidence only |
| Offline simulation | IMPLEMENTED AND TESTED | `scripts/simulation/rover_sim.cpp` uses real Controller/LineParser/MotionGate/serializer. Clear, timed obstacle, sensor-fault and E-stop scenarios; simulation explicitly labeled |
| Camera panel/proxy failure handling | IMPLEMENTED AND TESTED | Private IPv4/fixed endpoint validation, HTTP mocks, unavailable camera browser test; no synthetic feed presented as camera footage |
| Updated architecture and wiring | IMPLEMENTED AND TESTED | E2 201 records frozen; additive `electrical/system_design.json`, generated S1 aggregate netlist/CSV and two new PDF/SVG/PNG sheets. 211 total records, 206 external and five internal inspections |
| Actual electrical suitability and power-up release | BLOCKED BY SPECIFIC MISSING HARDWARE | E2 protection/current/thermal/module/USB holds plus new F3/BUCK3/OV3/C_CAM and camera-board qualification remain open. Physical release HOLD |
| Wokwi runtime | PARTIALLY IMPLEMENTED | Existing scenes/runner retained, sketch synchronized, build and CLI lint pass. No fresh token-authorized runtime or real waveform result claimed |

## Preserved behavior and decisions

`include/rover_control.h` and `include/rover_pins.h` are byte-for-byte unchanged from baseline. All 16 main GPIO assignments remain authoritative. Existing disabled startup, GPIO14 gating, active-HIGH GPIO27 feedback, latched ESTOP/STOP, safe RESET, 100ms neutral interval, 1200ms manual timeout, applied-time AUTO turns, fresh sensor reassessment/three-turn limit and independent forward-only cleaning requests remain intact. Serial S exits AUTO and stops without latching; ARM starts no movement.

Control path is browser -> loopback Node bridge -> exclusive USB serial main ESP32. Video path is separate ESP32-CAM -> explicitly configured trusted local WLAN -> fixed camera HTTP/MJPEG endpoints -> loopback proxy/browser. No motor-control Wi-Fi/Bluetooth path was invented. ESP32 remains final control authority.

Browser renews a manual intent lease every 80ms only during an intentional hold and while focused/visible; bridge heartbeats occur every 200ms while the lease is younger than 300ms. Release/blur/hidden page/mode change/error/disconnect stop renewal and attempt S; disconnect also attempts DISARM. Fresh v1 telemetry plus an initial DISARM ACK and stopped/disarmed report are required before active control. Reconnect never automatically RESET-s, ARM-s, selects AUTO or restores motion. Safe stop/output-off commands remain available before handshake. ACK, requested output, software-applied output and physical movement are explicitly different states. No encoders/physical movement measurement exist.

Loopback Host/Origin checks, mutation headers, one WebSocket operator, bounded commands/messages/logs, serial exclusive lock and ACK/freshness watchdogs constrain local access. They do not authenticate against malicious local-account software. Camera access has no TLS/per-user authentication: trusted WLAN isolation and no public forwarding are mandatory. No passwords/tokens are committed; empty camera credentials disable Wi-Fi. Camera IP is the only saved nonsecret UI preference.

PSRAM camera defaults: JPEG VGA 640x480, quality 12, two PSRAM buffers. Without PSRAM: QVGA 320x240, quality 14, one DRAM buffer. Only QVGA/VGA settings and quality 10–40 are permitted; VGA needs PSRAM. A capture mutex and distinct control/stream servers protect resources. One stream, bounded send timeouts, explicit unavailable responses and five-attempt reconnect bursts with cooldown are implemented. No frame-rate claim is made.

The S1 camera branch is independent F3 -> BUCK3 -> OV3 -> CAM1, fed before K1 with dedicated return. It does not consume an assumed spare budget on BUCK1/2 or main 3V3. Provisionally allocate 5V/1A continuous and 2A transient capacity; these are not measured currents. At assumed 80% efficiency, 5W/10W output requires 6.25W/12.5W input with 1.25W/2.5W regulator loss. Final ratings, actual efficiency/peak duration, camera LDO heat, protection and supply envelope remain unknown. Fuse amperages and vendor terminal numbering were not guessed. E2 full sheets retain every existing conductor; W202-W211 are traceable in the separate camera sheet. W205 is an internal bond inspection, not an added jumper.

## Defects found and resolved during implementation

- Baseline laptop telemetry lacked version/identity/reading age/healthy feedback and periodic requested-versus-applied cleaning fields. Added a bounded shared serializer without changing control decisions.
- Baseline had reserved CAM1 hardware only, with no camera firmware, laptop interface or complete control simulation. Implemented those components separately.
- Pinned SDK does not supply the assumed HTTP 503 enum; first camera build failed. Replaced it with an explicit 503 response helper and included the correct socket header. Later camera builds pass.
- Camera settings could partially change sensor state before an error. Status now reads back the sensor's actual setting fields.
- Browser keyboard target handling and development Host rewriting caused observed failures. Guarded the event target, preserved keyboard controls after button focus, ignored modifier shortcuts and configured proxy Host rewriting.
- React development remounts could race the single operator connection. Deferred initial connection, added safe channel retry and WebSocket liveness checks; no rover rearm/reconnection is performed by channel recovery.
- Added disarm-handshake gating, safe early output-off commands, earliest ACK deadlines, disconnect-during-open cancellation, telemetry safety cancellation and bounded malformed-input handling.
- E2 hash comparisons initially depended on CRLF working CSVs. Added LF-normalized system hashes and frozen-manifest CSV equivalence checks, with tests for fresh LF checkouts and rejection of changed content.
- The first dependency audit identified test-runner advisories. Updated the runner to the patched locked version; final npm audit has zero reported vulnerabilities.
- Timeline additions made broad browser text-count selectors ambiguous. Tests now scope applied/requested assertions to the operational-state region. Passing results below are from the corrected tests; earlier failures were not treated as success.
- Frozen handover validation originally required the entire live firmware to equal E2. It now checks archived handover firmware against Git `2da0b0a`, preserves the PDF/hash and live E2 electrical/controller/GPIO checks, and relies on current regressions for the telemetry extension.

## Verification evidence

Final logs and exact exit codes: `artifacts/system/summary.json` and individual `*.log` files. The summary records source HEAD plus working-tree status because verification precedes commits; the source manifest records the tested source hashes. Counts and build sizes below are updated from the final run, not historical E2 claims.

| Check | Actual result | Evidence |
|---|---|---|
| Main native C++ controller/parser/adapter/turn regressions | **84/84 PASS** | `artifacts/native-tests.log` |
| Python electrical/export/waveform/handover/S1/portability regressions | **54/54 PASS** | `artifacts/python-tests.log`; last two portability cases rerun after the consolidated baseline stage |
| TypeScript backend/protocol/camera-proxy/component/integration tests | **56/56 PASS**, five files | `artifacts/system/typescript-tests.log` |
| Real Chrome browser tests | **4/4 PASS** | `artifacts/system/browser-tests.log`: full simulator controls, pointer/blur/reconnect, mobile overflow, isolated camera-failure mock |
| Camera host suites | **2 executables PASS** | `artifacts/system/simulation-camera-host.log`: policy/resource tests and actual HTTP handlers with boundary mocks; assertions are not inflated into a test-case count |
| Main ESP32 build | **PASS**; RAM 22,240B / flash 281,945B | `artifacts/build.log`, `esp32dev` |
| Synchronized Wokwi sketch build | **PASS**; RAM 22,240B / flash 281,945B | `artifacts/build.log`, `wokwi_compile` |
| AI-Thinker camera build | **PASS**; RAM 49,996B / flash 871,241B | `artifacts/system/camera-build.log`; pinned Espressif32 6.12.0 / Arduino 2.0.17 |
| TypeScript and Vite production build | **PASS** | `artifacts/system/laptop-build.log`; no serial hardware required |
| Production dashboard/asset/API serving | **PASS**, loopback and initially disconnected/disarmed | `artifacts/system/production-smoke.log` |
| E2 and S1 graph/drawing consistency | **PASS**, existing 201 unchanged / aggregate 211 | `artifacts/system/system-graph.log`, baseline export logs; file consistency only |
| Frozen 74-page handover | **PASS** | `artifacts/system/frozen-handover.log`; original PDF unchanged |
| Dependency audit | **PASS**, zero reported vulnerabilities | `artifacts/system/dependency-audit.log`, lockfile installed on Intel x86_64 macOS / Node 24.14.1 |
| Wokwi CLI lint | **PASS with one informational legacy-board notice** | `artifacts/wokwi-lint.log`; runtime not executed |
| Physical USB/video/electrical/motor acceptance | **NOT EXECUTED, HOLD** | No hardware, uploads, measurements or physical approval claimed |

Wokwi CLI reports one informational undocumented legacy DevKit part notice. Browser test servers can emit Node NO_COLOR/FORCE_COLOR warnings; those are not passed-off test failures. No unresolved software test/build failure is intentionally concealed. Host camera tests use boundary mocks, not ESP32 hardware. The native simulator exercises the real controller but cannot establish electrical levels, timing under real motor load, physical cutoff, USB backfeed or live video performance.

## Operating commands

```sh
# Install from repository root, Node >=22.12 and C++ compiler available
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt -r requirements-design.txt
npm ci
npm run sim:build
npm run build
npm start
# Open http://127.0.0.1:8787; Offline simulator -> Connect -> ARM deliberately

# Development, separate terminals
npm run bridge
npm run dashboard
# Open http://127.0.0.1:5173

# Software-only complete verification
.venv/bin/python scripts/verify_system.py

# Build each real controller separately; these do not upload
.venv/bin/pio run -e esp32dev
.venv/bin/pio run -d camera -e ai_thinker_esp32cam

# Rebuild additive electrical exports; E2 base stays frozen
.venv/bin/python scripts/generate_system.py
.venv/bin/python scripts/check_system.py
```

Manual upload commands and physical prerequisite boundaries are in `docs/LAPTOP_CONTROL_SETUP.md` and `camera/README.md`. Close bridge/monitors before upload; one serial owner only. No automatic upload command is part of verification.

## Remaining physical acceptance / workflow status

Repository installation, builds, simulator control, software tests and documentation exports were executed here. VS Code opening, firmware installation on either physical controller, qualified USB/external supply connection, actual camera WLAN join/video, physical emergency readiness, ARM/manual/AUTO/cleaning on real motors and physical stopping were **not executed**.

Before physical commissioning: identify camera board/sensor/PSRAM and programmer; identify all controller/driver/protection terminal maps; resolve E2 P1/OV1/OV2/K1/contact and load-current/fuse/harness holds; qualify new F3/BUCK3/OV3/C_CAM; measure power/USB sequencing, ripple/transient/thermal behavior and grounds; complete unpowered continuity/isolation; use approved detached firmware procedures; perform motor-free cutoff tests before guarded individual/load motor tests; verify actual wheel/brush/conveyor directions, sensing/stopping distances, serial timeout/disconnects and real camera reconnects/performance. Follow E2 stage gates and add camera branch acceptance. No certification or power-up approval is claimed.

Manual communication loss is bounded by the existing onboard timeout, but failed software STOP never proves physical power removal. During AUTO, backend failure can leave onboard navigation operating; no new AUTO communication-loss deadman is claimed. Use independently verified physical S2/K1 for critical stopping.

## Commit record

Current software HEAD when this report was finalized: `325aa53cda379ea2cdcfb3bedd72c3564cebfb96` on `main`.

1. `07c75614189a4f8ff9958faf13e25e834cf638fe` — versioned main telemetry and separate ESP32-CAM firmware/host tests.
2. `325aa53cda379ea2cdcfb3bedd72c3564cebfb96` — local dashboard, serial bridge, typed protocol, C++ simulator and browser/integration tests.
3. The enclosing documentation/electrical/evidence commit follows these software commits; obtain its exact hash with `git rev-parse HEAD` after checkout. The final chat handoff provides that hash and push status. The report cannot embed its own enclosing Git commit hash.

Verification ran before commits on the recorded baseline plus reviewed implementation files. `artifacts/system/source-manifest.json` records the final tested source hashes, `preservation.json` proves unchanged critical E2 sources, and `summary.json` retains actual command exit codes plus the later successful LF/CRLF regression reruns. All ten consolidated checks passed; 54 Python cases and final S1/handover checks passed after the portability correction. Logs were normalized only for trailing whitespace.
