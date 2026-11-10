# USB serial protocol v1

115200 baud, ASCII newline-delimited input; CR/LF supported. Firmware `rover-usb-v1` retains existing command names and `OK <command>` / `ERR <command>` responses. Acknowledgement means the command was accepted by the controller, never that a motor moved. Only the bridge owns the serial port; close it before PlatformIO upload or Serial Monitor.

Commands: `ARM DISARM RESET AUTO MANUAL F B L R S STOP ESTOP`, `BRUSH ON/OFF`, `CONVEYOR ON/OFF`, `CLEAN ON/OFF`. Each command occupies its own line. `S` stops and exits AUTO without latching. `STOP` and `ESTOP` latch an emergency disarm. RESET clears the latch only when disarmed and GPIO27 is HIGH; it neither ARM-s nor restores any output. ARM alone starts no motion. AUTO requires three fresh valid ranges. Manual movements are open-loop requests; the existing firmware does not add autonomous obstacle avoidance to manual driving. The operator must assess the surroundings.

`LineParser::feed` in `include/rover_control.h` permits 48 characters, uppercases/trims, discards an entire overlong/control-character line and disarms on overflow. Loop serial work stays capped at 64 bytes per iteration. The bridge additionally validates exact command names, rejects embedded newlines and forbids direct F/B/L/R command messages; motion uses a hold lease.

Periodic JSON follows the prefix `TEL `:

```json
{"v":1,"fw":"rover-usb-v1","ms":500,"armed":false,"auto":false,"estop":false,"healthy":true,"requested":0,"applied":0,"en":false,"brushReq":false,"conveyorReq":false,"brush":false,"conveyor":false,"nav":"DISARMED","cm":[120,100,70],"age":[45,175,110]}
```

`ms` and ages are unsigned 32-bit milliseconds, using rollover-safe subtraction on the MCU. Sensor ages are elapsed time since the last attempt, including invalid attempts. `cm=-1` is invalid, never a fabricated distance. Values 2–400 cm are in the controller's accepted numeric range. Reading freshness requires age <=500ms; the UI also adds elapsed laptop time since receipt. `requested`/`applied`: 0 STOPPED, 1 FORWARD, 2 BACKWARD, 3 LEFT, 4 RIGHT. `brushReq`/`conveyorReq` are requested states; `brush`/`conveyor` describe gated software outputs. `en` is adapter permission, not a measured motor-power voltage. No physical motion, current, speed, battery level or contact-opening measurement exists. Healthy feedback represents GPIO27, not a safety certification. Existing DIST and event STATE text messages remain compatible.

`include/rover_telemetry.h::telemetry` is shared by firmware and the native simulator. Bounded 512-byte formatting includes an explicit truncation check in the ESP32 adapter. Telemetry every 500ms adds UART transmission time: at 115200, a maximum 511-byte JSON line plus legacy DIST can occupy roughly 50ms on the wire. The serial buffer can block part of that duration. Software stop latency includes UART work plus a possible 25ms pulseIn timeout and other overhead; no real worst-case stop latency is measured. The hardware ISR and independent cutoff remain required.

## Laptop control protocol

Loopback HTTP/WebSocket only, port 8787. Development Vite proxies `/api` from port 5173 with Host rewriting. Exact local Host/Origin checks reject DNS rebinding and cross-site writes. HTTP mutations require `X-Rover-Client: dashboard`. WebSocket `/api/control` requires an approved Origin and permits one client. These measures restrict browser access; they are not authentication against malicious software already running under the local account. No remote-network listener, cloud service, token or Wi-Fi password is required for rover control.

Browser messages:

```json
{"type":"connect","simulation":true,"scenario":"obstacle"}
{"type":"connect","simulation":false,"port":"/dev/cu.YOUR_ACTUAL_PORT"}
{"type":"command","command":"ARM"}
{"type":"hold","direction":"F"}
{"type":"release"}
{"type":"disconnect"}
```

The bridge sends a non-latching S and DISARM on open and again after READY. `protocolReady` becomes true only after DISARM acknowledgement and stopped/disarmed v1 telemetry; old installed firmware remains observable but cannot drive through this UI. No automatic RESET, ARM, AUTO or movement on reconnect. Browser control-channel reconnection returns to a disconnected rover session.

Held controls renew an intent lease every 80ms while focused/visible. Bridge movement heartbeats run every 200ms only while that lease is younger than 300ms and fresh telemetry permits manual movement. Release, blur, hidden page, mode changes, ESTOP, rejection, errors, control-channel loss or disconnection cease renewal/heartbeats; the bridge attempts S and, on disconnect, DISARM. The controller's independent 1200ms manual timeout remains unchanged. A delayed/failed STOP cannot prove a physical stop. If the backend dies during AUTO, the existing autonomous controller can continue navigating: no new AUTO serial-link deadman is claimed. Its sensor/safety decisions remain onboard, and critical stopping requires physical S2.

Bridge input lines are capped at 1024 bytes; malformed JSON and contradictory output fields are rejected. Acknowledgement timeout is 2s, stale telemetry disconnect is 1.5s; queued duplicate commands retain the earliest ACK deadline. State snapshots and 150 timestamped log entries are bounded. WebSocket payload and rate limits protect the local control loop. No command string from the browser is interpolated into shell commands.
