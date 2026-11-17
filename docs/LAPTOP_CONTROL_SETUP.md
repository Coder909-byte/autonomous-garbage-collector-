# Laptop control setup

Intel macOS is supported using Node.js 22.12 or newer, npm, Python 3 and Apple's Command Line Tools (`c++`). Docker is not needed. The native SerialPort dependency provides platform bindings; if no matching prebuild exists, npm may need the normal compiler toolchain. No serial device is opened by build/test commands; no firmware is automatically uploaded.

## Install and run offline

From the repository root:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt -r requirements-design.txt
npm ci
npm run sim:build
npm run build
npm start
```

Open **http://127.0.0.1:8787**. This single production server hosts the built dashboard, local control WebSocket, serial bridge and camera proxy. It binds to loopback. Keep one operator tab open. A second tab cannot take control. Select Offline simulator, choose a scenario, then Connect rover. The amber SIMULATION MODE banner means all feedback is synthetic and no GPIO/motor output exists.

For development, use two terminals from the root:

```sh
npm run bridge
```

```sh
npm run dashboard
```

Open **http://127.0.0.1:5173**. The Vite proxy rewrites Host for the bridge and preserves the approved local Origin. Do not open the built index.html as a file or expose the dev server/backend to the LAN. Local software under the operator account is trusted; these services do not provide multi-user authentication.

## Simulator workflow

Clear path supplies synthetic front/left/right readings of 120/100/70cm. Obstacle scenario changes front to 25cm at 3s and restores it at 6s. Sensor-fault scenario changes front to invalid at 3s. E-stop scenario opens synthetic healthy feedback at 3s. Scenario time starts at Connect; reconnect to restart the script. No scenario automatically ARM-s or starts AUTO. The onboard three-turn limit can disarm before an obstacle clears; clearing it does not rearm. No simulated camera footage is included.

After versioned telemetry arrives and the initial DISARM handshake completes, click ARM. It must leave STOPPED and EN LOW. W/S/A/D or pointer controls are press-and-hold; release stops. Space sends non-latching S. AUTO requests onboard navigation and requires fresh valid sensors; MANUAL stops/exits AUTO. Cleaning toggles show requested and applied separately. CLEAN ON does not make the outputs run while stopped. Stop/disarm before changing the connection. The red dashboard control is **software ESTOP**, which latches the firmware; it is not a physical motor-power cutoff.

## Main ESP32 / real serial

Physical commissioning remains HOLD under `docs/FINAL_GO_NO_GO.md`. As of 16 November 2026, the user reports the latest main firmware was flashed on another laptop and produced `READY DISARMED` and protocol-v1 telemetry. This software session did not observe that board. The earlier `USB_VALIDATION_REPORT.md` is a historical report from this Mac, not a current finding about that later flash. No upload is needed for the laptop integration work. The following build/upload instructions are reference only for a separately approved future installation:

```sh
.venv/bin/pio run -e esp32dev
# Only later, with the identified detached board and approved setup:
.venv/bin/pio run -e esp32dev -t upload --upload-port YOUR_ACTUAL_MAIN_ESP32_PORT
```

Stop the bridge and close all Serial Monitors before any approved upload. Never run two serial owners. USB opening can reset a DevKit; new firmware boots disabled. Start the bridge/dashboard, select Main ESP32 USB serial, and choose the actual enumerated port. Ports refresh every three seconds; manual selection remains until that port disappears. Clicking Connect sends S and DISARM and waits for protocol-v1 stopped/disarmed feedback. The version is the `"v":1` field in `TEL { ... }`, not the literal string `TEL v1`. Older firmware without it cannot drive through the UI; its raw serial messages remain visible. No reconnect automatically RESET-s, ARM-s, selects AUTO or resumes motion. An incomplete protocol handshake times out within five seconds; missing ACKs can close it earlier.

For later USB + externally powered operation, the actual board USB/backfeed/ground path must be qualified first. Do not treat a data cable or SerialPort success as electrical approval. A released hardware procedure must establish physical S2/K1 readiness before any deliberate hardware S3 power-arm, firmware RESET or ARM. Firmware RESET is enabled only for healthy, disarmed feedback. Verify actual motor cutoff separately.

## Separate camera

Read `camera/README.md` and `docs/CAMERA_WIRING.md`. Identify the actual board, qualify its independent protected supply and programmer, copy the secrets template locally, and build camera firmware separately. Upload only under the approved detached procedure. Enter the numeric private camera IP printed at 115200 or listed by DHCP, or its HTTP URL (for example `http://192.168.50.20:81/stream`). The bridge normalizes this to a private numeric IPv4 and retains fixed ports 80/81 and firmware endpoint paths; hostnames, credentials, query strings, HTTPS and arbitrary ports are rejected. Connect camera checks real /status before opening the MJPEG feed through the loopback proxy. A streaming status alone does not establish decoded video; no decoded frame within 12 seconds fails explicitly. Proxy inactivity is bounded to five seconds; status/config requests have a seven-second browser deadline, and snapshots eight seconds. Disconnect closes the proxy stream; Snapshot downloads a timestamped real JPEG. Settings require stream disconnection. A missing camera remains visibly unavailable and cannot change motor authority.

Only nonsecret camera IP is saved in browser localStorage. Wi-Fi passwords live in ignored `camera/include/secrets.h`. The camera supports explicitly configured canonical RFC1918 /24 and /28 networks. For the verified iPhone hotspot, the configured network/mask are `172.20.10.0` / `255.255.255.240`; both the camera and Mission Control host must have usable addresses `.1` through `.14`. The Mac's `.3` is not the camera address. See [the Dell G15 Arduino guide](ESP32_CAM_ARDUINO_WINDOWS.md). No camera authentication/TLS is implemented; use the explicit trusted isolated WLAN, never public forwarding. Camera Wi-Fi loss is not evidence of a rover stop.

## Diagnostics and navigation display

The bridge records automatically while running. Every retained event has a laptop UTC receipt timestamp, session ID, source (`hardware`, `simulation`, or preconnection `bridge`) and port. Telemetry records retain raw range values/ages, requested and applied software motion, enables, cleaning requests/outputs, firmware time, navigation and safety feedback. Safety feedback/latch changes, serial failures, rejected commands and connection events are recorded separately. No encoders or power measurements are implied.

Use **Export CSV** or **Export JSON** to save the bounded 10,000-record buffer. Records survive disconnect and browser reload while the bridge stays running. Oldest records are evicted at capacity, with an eviction count; stopping the bridge loses unsaved data. CSV escapes external text and prevents spreadsheet-formula execution. JSON schema version is 1. Read-only endpoints: `/api/diagnostics`, `/api/diagnostics/export?format=csv`, and `/api/diagnostics/export?format=json`.

The trend chart uses the last 120 telemetry samples and draws only the latest session, never joining hardware to simulation. Invalid or sensor-stale samples create gaps; retained charts are historical, not a live connection indicator. The navigation diagram explains the reported C++ phase; it does not calculate an independent controller, position or heading. AUTO enters avoidance at front ≤35 cm or either side ≤20 cm; recovery needs front >45 cm and both sides >20 cm. See the panel explanations for settling, output dead time, turn limit and new-sample reassessment. Obstacle avoidance is not active in MANUAL.

## Verification

```sh
.venv/bin/python scripts/verify.py
npm run sim:build
npm test
npm run build
.venv/bin/pio run -d camera
.venv/bin/python scripts/check_system.py
.venv/bin/python scripts/check_team_handover.py
npm run test:e2e
```

Browser tests use installed Google Chrome on macOS by default; set `CHROME_PATH` to a Chromium/Chrome executable elsewhere, or install Playwright Chromium and set CHROME_PATH to it. They launch dedicated test servers on 18787/15173; the production smoke check uses 18788. These avoid the normal 8787/5173 ports so an existing operator tab cannot acquire the test bridge. Keep the test ports free. The one-operator restriction remains enforced. `scripts/verify_system.py` runs the complete sequence and writes individual logs and a machine-readable summary under `artifacts/system/`. No hardware uploads occur.

Normal application ports remain 8787/5173. For custom local ports, set `ROVER_BRIDGE_PORT` and `ROVER_DASHBOARD_PORT` consistently for both development processes. Only the selected loopback origins are accepted; no LAN binding is added.

For a fresh monitoring regression that preserves earlier commissioning logs, run `.venv/bin/python scripts/verify_monitoring.py`. It runs the source/electrical checks, native/Python/JavaScript suites, main/camera builds, simulator, production smoke and browser tests. Per-run logs and protected-source hashes go to a timestamped folder inside `artifacts/monitoring-validation/`. It does not open a physical serial port or upload firmware.

## Troubleshooting

| Symptom | Action |
|---|---|
| Connect disabled / bridge offline | Start bridge; use its loopback URL or Vite 5173; close the other operator tab; browser retries the control channel safely without reconnecting/rearming a rover |
| Port absent | Refresh; inspect actual USB cable/programmer and OS enumeration; do not guess a device path |
| Port busy | Stop uploader, PlatformIO Serial Monitor and other bridge processes; only one owner can hold the port |
| Raw DIST but no controls | Installed firmware is old; use the approved detached installation procedure for v1; do not bypass telemetry validation |
| No ACK / stale data / unplugged USB | Bridge stops lease, attempts S/DISARM, closes. Delivery is unconfirmed; use physical stop when required. Reconnect deliberately |
| ESTOP at physical boot | Expected with unarmed/open K1 feedback. Follow released hardware sequence; do not jumper feedback or automatically RESET |
| AUTO rejected / sensor fault | Inspect all three valid/fresh readings and conditioning; recovery needs deliberate ARM/AUTO after physical cause is resolved |
| Cleaning requested ON but applied OFF | Expected unless actually moving forward after neutral interval, armed and safety permitted |
| Camera unavailable | Verify actual board/power/WLAN/subnet, IP and serial diagnostics; endpoints are fixed at HTTP80 and stream81 |
| Camera busy/settings rejected | Disconnect stream, wait for bounded send timeout, then apply supported settings; VGA needs detected PSRAM |
| npm mirror timeout | Use an approved working registry, for example `npm ci --registry=https://registry.npmjs.org`; machine npm settings are not committed |
| Native simulator missing | Run `npm run sim:build` from repository root with C++ compiler installed |

If browser/backend fails, manual firmware timeout still operates. AUTO is onboard and can continue without laptop communication. Failed software stop is never proof of physical power removal. No commissioning step in this document is recorded as completed.
