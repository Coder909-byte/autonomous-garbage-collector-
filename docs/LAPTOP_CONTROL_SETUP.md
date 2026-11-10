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

## Future main ESP32 installation / real serial

Physical commissioning remains HOLD under `docs/FINAL_GO_NO_GO.md`. The actual main ESP32 still contains older firmware. After all prerequisites for a detached, unpowered-from-rover board are satisfied, manually build and then upload in an approved USB-only setup:

```sh
.venv/bin/pio run -e esp32dev
# Only later, with the identified detached board and approved setup:
.venv/bin/pio run -e esp32dev -t upload --upload-port YOUR_ACTUAL_MAIN_ESP32_PORT
```

Stop the bridge and close all Serial Monitors before upload. Never run two serial owners. USB opening can reset a DevKit; new firmware boots disabled. After upload, close the uploader/monitor, start the bridge/dashboard, select Main ESP32 USB serial, Refresh and choose the actual enumerated port. Clicking Connect sends S and DISARM and waits for protocol v1 stopped/disarmed feedback. Older firmware without TEL v1 cannot drive through the UI; its raw serial messages remain visible. No reconnect automatically RESET-s, ARM-s, selects AUTO or resumes motion.

For later USB + externally powered operation, the actual board USB/backfeed/ground path must be qualified first. Do not treat a data cable or SerialPort success as electrical approval. A released hardware procedure must establish physical S2/K1 readiness before any deliberate hardware S3 power-arm, firmware RESET or ARM. Firmware RESET is enabled only for healthy, disarmed feedback. Verify actual motor cutoff separately.

## Separate camera

Read `camera/README.md` and `docs/CAMERA_WIRING.md`. Identify the actual board, qualify its independent protected supply and programmer, copy the secrets template locally, and build camera firmware separately. Upload only under the approved detached procedure. Enter the numeric private camera IP printed at 115200 or listed by DHCP. Connect camera checks real /status before opening the MJPEG feed through the loopback proxy. Disconnect closes the proxy stream; Snapshot downloads the real JPEG. Settings require stream disconnection. A missing camera remains visibly unavailable and cannot change motor authority.

Only nonsecret camera IP is saved in browser localStorage. Wi-Fi passwords live in ignored `camera/include/secrets.h`. No camera authentication/TLS is implemented; use the explicit trusted isolated WLAN, never public forwarding. Camera Wi-Fi loss is not evidence of a rover stop.

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

Browser tests use installed Google Chrome on macOS by default; set `CHROME_PATH` to a Chromium/Chrome executable elsewhere, or install Playwright Chromium and set CHROME_PATH to it. They launch separate test servers on 8787/5173; stop your running bridge/dev server first. `scripts/verify_system.py` runs the complete sequence and writes individual logs and a machine-readable summary under `artifacts/system/`. No hardware uploads occur.

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
