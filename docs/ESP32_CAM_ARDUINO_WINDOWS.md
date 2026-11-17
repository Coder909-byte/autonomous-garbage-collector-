# ESP32-CAM Arduino IDE preparation — Dell G15

Prepared on 17 November 2026. Upload has not been performed. Main rover firmware and GPIO assignments are unchanged.

The transfer archive is `~/Desktop/rover_camera.zip`. Treat it and its extracted folder as **SENSITIVE**: they contain the local configuration file and may contain Wi-Fi credentials after local editing. The ZIP is not encrypted. Do not commit it, attach it to a public issue, or upload it to an external service. Use a private local transfer to the Dell.

The archive contains exactly:

```text
rover_camera/
  rover_camera.ino
  board_ai_thinker.h
  camera_policy.h
  secrets.h
```

## Configuration and explicit /28 policy

Wi-Fi credentials are stored only in ignored local `camera/include/secrets.h` and its private Arduino-package copy. Never copy credential values into tracked source, documentation or build logs. The trusted network is now `172.20.10.0` with mask `255.255.255.240`, matching the verified iPhone hotspot. Hostname remains `rover-camera`. The sketch contains an identical local configuration copy. Both operator configuration files and ZIPs remain ignored by Git. Every file named `secrets.h` is Git-ignored. Host tests select `camera/test/stubs/camera_test_config.h` with `CAMERA_HOST_TEST`; this fixture contains only empty/synthetic values and never reads operator credentials.

The actual network was previously verified from the Mac interface and DHCP, and the user confirmed it for this update:

| Observation | Value |
| --- | --- |
| Interface | `en0` |
| Mac IPv4 | `172.20.10.3` |
| Interface and DHCP subnet mask | `255.255.255.240` |
| Actual / configured network | `172.20.10.0/28` |
| Usable hosts accepted by firmware | `172.20.10.1` through `172.20.10.14` |
| Excluded network / broadcast addresses | `172.20.10.0` / `172.20.10.15` |
| Supported configured masks | `255.255.255.0` (`/24`) or `255.255.255.240` (`/28`) |

The production `cam::TrustedNetwork` policy accepts only canonical RFC1918 `/24` or `/28` networks. It parses four strict decimal octets without leading zeros, whitespace, suffixes or CIDR notation, rejects noncontiguous/unsupported masks and network bases with host bits set, and fails closed after invalid reconfiguration. Explicit octet packing makes station and peer subnet arithmetic independent of integer byte order. Both addresses must be usable hosts of the configured subnet. Wildcard, public, loopback, link-local and multicast networks/peers are rejected. Every HTTP endpoint retains the same connection and peer checks. The pinned SDK enables IPv6 and its [ESP-IDF HTTP listener](https://github.com/espressif/esp-idf/blob/v4.4.7/components/esp_http_server/src/httpd_main.c) can represent IPv4 clients as `::ffff:a.b.c.d`; those addresses are decoded and checked against the same IPv4 policy. Native IPv6, unsupported socket families, truncated addresses and failed peer lookups fail closed. Streaming stops on Wi-Fi or station-subnet loss. Wi-Fi remains station-only, with no AP fallback.

This resolves the former `/28` policy mismatch without authorizing the surrounding `/24`. The policy is an explicit allowlist; it does not assign a static address or verify/change the DHCP mask at runtime. If the WLAN changes, inspect the actual network again and configure its aligned supported private subnet locally. Do not widen this hotspot's configured mask to `/24`.

A privately configured ZIP already includes the local hotspot settings. If configuration is needed, edit only the local `secrets.h`; never publish its contents. For a fresh Git clone, copy `camera/include/config.example.h` to ignored `camera/include/secrets.h`, enter the real settings locally, and copy it to ignored `rover_camera/secrets.h` before opening the sketch. Keep the verified network/mask above. Enable the iPhone's **Maximize Compatibility** setting if available to provide a compatible 2.4 GHz network ([Apple Wi-Fi security guidance](https://support.apple.com/en-afri/guide/security/secfd166f620/web)). The existing policy accepts SSID lengths 1–32 bytes and passwords 8–63 bytes. Keep passwords out of screenshots and logs. If credentials are empty, the sketch compiles but prints a configuration fault and leaves Wi-Fi disabled. The repository and Windows copies do not automatically synchronize after editing.

`172.20.10.3` identifies the Mac, not the camera. No Mission Control server IP needs to be embedded in camera firmware: Mission Control initiates HTTP connections to the camera's DHCP address. Confirm that the Dell and camera also join this hotspot and that hotspot clients can communicate; host tests cannot establish actual iPhone client-to-client reachability.

## Firmware and API compatibility

Use **esp32 by Espressif Systems, version 2.0.17**. The original PlatformIO environment pins `espressif32@6.12.0`; its installed `framework-arduinoespressif32` package is `3.20017.241212+sha.dcc1105b`, containing Arduino-ESP32 2.0.17. The leading `3` in that PlatformIO package number does not mean Arduino-ESP32 3.x.

All required libraries come with that ESP32 package: Arduino core, WiFi, ESPmDNS, esp32-camera, ESP-IDF HTTP server, FreeRTOS and lwIP. `<atomic>` is supplied by the toolchain. No separate camera/web-server library from Library Manager is needed.

The installed 2.0.17 headers provide the firmware's `camera_config_t.pin_sccb_sda`, `pin_sccb_scl`, `fb_location`, `grab_mode`, camera frame APIs, HTTP request/server APIs and Wi-Fi methods. The SCCB spelling used by this firmware is correct for that installed driver; the old `pin_sscb_*` spellings are deprecated aliases.

Arduino-ESP32 3.0 moves from ESP-IDF 4.4 to 5.1 and changes API/build behavior. Its Wi-Fi implementation introduces `STAClass`/`NetworkInterface` with a compatibility wrapper; old Arduino LEDC setup/attach APIs are removed. This firmware uses camera-driver LEDC fields rather than those removed Arduino calls, so their removal alone does not establish a failure in this sketch. Nevertheless the camera/HTTP/lwIP combination has not been built or tested here on 3.x. Compatibility with 3.x is not claimed. The packaged sketch deliberately emits a compile-time error for any core version other than 2.0.17.

`rover_camera.ino` contains the original camera implementation with a board-definition/version preamble and explicit function declarations for Arduino preprocessing. Its implementation matches the updated production camera source exactly after removing those packaging additions. The project-specific `CAMERA_BOARD_AI_THINKER` definition appears before `board_ai_thinker.h`; selecting the IDE board alone does not supply this custom definition. Both nonsecret headers are exact copies. `/status`, `/snapshot`, `/settings`, `:81/stream`, PSRAM fallback, retries, mutexes and network checks remain present.

References: [Espressif installation instructions](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html), [2.0.17 board definitions](https://github.com/espressif/arduino-esp32/blob/2.0.17/boards.txt), [2.x to 3.0 migration](https://docs.espressif.com/projects/arduino-esp32/en/latest/migration_guides/2.x_to_3.0.html), [2.0.17 Wi-Fi API](https://github.com/espressif/arduino-esp32/blob/2.0.17/libraries/WiFi/src/WiFiSTA.h), [3.0 Wi-Fi compatibility API](https://github.com/espressif/arduino-esp32/blob/3.0.0/libraries/WiFi/src/WiFiSTA.h).

## Arduino IDE on Windows

1. Install Arduino IDE on the Dell. Extract the ZIP using **Extract All**. Open `rover_camera/rover_camera.ino` from the extracted folder, not from inside the ZIP. Its containing folder and main sketch basename must both be `rover_camera`.
2. In **File > Preferences > Additional Boards Manager URLs**, add `https://espressif.github.io/arduino-esp32/package_esp32_index.json`.
3. Open **Boards Manager**, find **esp32 by Espressif Systems**, choose **2.0.17**, and install. Avoid accepting a later package upgrade for this sketch.
4. Select **Tools > Board > esp32 > AI Thinker ESP32-CAM**. Apply the settings below, then click **Verify**. Ensure the private local configuration is complete before an upload intended to provide video; the verified /28 network must remain configured.

| Setting | Value |
| --- | --- |
| Board | `AI Thinker ESP32-CAM` |
| FQBN | `esp32:esp32:esp32cam` |
| ESP32 board package | `2.0.17` |
| CPU Frequency | `240MHz (WiFi/BT)` |
| Flash Frequency | `40MHz` |
| Flash Mode | `DIO` |
| Partition Scheme | `Huge APP (3MB No OTA/1MB SPIFFS)` |
| Flash capacity | Board preset: `4MB` |
| PSRAM | Enabled by board preset; usually no separate PSRAM menu on this board |
| Core Debug Level | `None` |
| Erase All Flash Before Sketch Upload | `Disabled` |
| Upload speed | Board preset: `460800` |
| Port | The actual programming-base `COM` port discovered below |
| Serial Monitor | `115200` baud; no line ending needed |

These flash/CPU/partition settings match the existing PlatformIO camera environment. In stock 2.0.17 the AI Thinker entry does not expose an Upload Speed menu; do not confuse the fixed 460800 upload speed with the 115200 monitor baud. If a verified programmer is unreliable at that preset, a lower upload speed requires an explicit uploader override rather than an assumed IDE menu. Do not change the board type simply to obtain that menu.

## Detached programming base procedure

The board currently only appears to be AI-Thinker-style. Confirm its markings, OV2640-compatible sensor, PSRAM and matching base/orientation before upload. A red LED indicates a powered indicator circuit; it does not prove USB data enumeration, correct pin mapping, sufficient camera supply or successful boot.

1. Keep the camera and programming base physically detached from rover battery, main ESP32 and all external rover circuits. With USB unplugged, seat the camera correctly in its matching dock. Follow the actual base's documented single-source USB supply arrangement; use a known data-capable USB cable. Never parallel USB power with an external 5V supply or apply 5V UART logic.
2. Connect only this detached camera/base to the Dell. In **Device Manager > Ports (COM & LPT)**, identify the port that appears when it is connected and disappears when disconnected. Choose that `COMn` in Arduino IDE. Do not select the already programmed main ESP32. If there is no port, check the data cable and identify the base's USB-UART chip; install its maker's driver if needed. The base model/USB chip is not known, so no COM number or driver is assumed.
3. Close any Serial Monitor or other process holding that port. For a base with documented automatic download/reset, click **Upload** and let it perform the sequence. A red LED alone does not establish automatic reset support.
4. If the base requires manual boot selection, use its documented **BOOT/IO0** control to hold GPIO0 low, pulse **RST/EN**, then release BOOT once the bootloader connection is established. For a board/base without that control, a verified GPIO0-to-GND programming jumper may be fitted while USB is disconnected, then reset into download mode. Do not guess the dock's button functions or pin positions. GPIO0 is also the camera XCLK in normal operation.
5. Upload only after hardware identity/power arrangement are confirmed. If the uploader remains at `Connecting...`, perform the documented boot/reset sequence; check the correct COM port rather than changing camera GPIOs. After a successful upload, release BOOT/remove the programming jumper with power disconnected, restore power, and press RST to run with GPIO0 released. Do not leave GPIO0 grounded for normal camera operation.
6. Open Serial Monitor at **115200** and reset once to see startup output. Expect camera initialization diagnostics and PSRAM detection. `init=0x0` and `ready=1` indicate successful initialization. If credentials are empty or invalid, `FAULT configure secrets.h...` indicates that Wi-Fi was disabled. Close Serial Monitor again before another upload.

Boot reference: [Espressif ESP32 boot mode selection](https://docs.espressif.com/projects/esptool/en/latest/esp32/advanced-topics/boot-mode-selection.html). Permanent rover-camera power remains subject to the existing independent-branch qualification in [CAMERA_WIRING.md](CAMERA_WIRING.md); no external rover circuits were powered in this preparation.

## Find the camera and verify video

After entering credentials and a later manual upload, connect the camera, Dell and Mission Control Mac to the verified iPhone hotspot. Check client-to-client reachability and the actual subnet masks on both hosts. If the hotspot isolates clients, it must be resolved at the network level; do not broaden the firmware allowlist.

Serial Monitor prints `Camera IP <address>; trusted=1; /status /snapshot :81/stream`. Record that numeric camera address, or find its DHCP lease. `rover-camera.local` is a convenience name; Mission Control uses numeric IPv4. `trusted=0` means the acquired station IP is outside the configured allowlist and the HTTP servers will not start on that connection. Wi-Fi retries are bounded bursts of five attempts with cooldown; no open AP fallback exists.

From a host on the authorized network, replace `<camera-ip>` below with that actual numeric address:

| Check | URL / expected result |
| --- | --- |
| Status | `http://<camera-ip>/status`: JSON with `v:1`, `ready:true`, IP, PSRAM, width, quality and streaming |
| Still image | `http://<camera-ip>/snapshot`: a real JPEG |
| Live video | `http://<camera-ip>:81/stream`: MJPEG camera video |

An empty `/` homepage or 404 at `/` is not the status test. Initialization failure can still allow `/status` with `ready:false`; capture/stream then returns unavailable. Unauthorized peers receive 403. A busy camera can return 503. Only one live stream is accepted: close a direct browser stream before connecting Mission Control. Confirm decoded real images, not merely a successful HTTP connection.

In the existing Mission Control dashboard on the Mac, use its existing local URL (`http://127.0.0.1:8787` production, or the existing development setup at `http://127.0.0.1:5173`). Keep the working main-rover connection as configured. In **CAMERA IPv4 / HTTP URL**, enter the numeric camera IP or `http://<camera-ip>` and click **Connect camera**. The bridge checks `/status` then proxies the video; confirm **LIVE CAMERA** and a real image. Use **Snapshot** for a JPEG. Disconnect the stream before changing resolution/quality. Do not enter the Mac's IP as the camera address or expose the loopback bridge to the WLAN. The camera receives no motor-control authority.

## Validation record

| Check | Result |
| --- | --- |
| Original camera PlatformIO project, with verified /28 configuration | PASS |
| Camera policy/resource host tests | PASS |
| Actual HTTP-handler host tests, including IPv4-mapped peers and rejected native IPv6 | PASS |
| AddressSanitizer / UndefinedBehaviorSanitizer, both camera host suites | PASS |
| Selected Mission Control camera/bridge/dashboard tests | 61 PASS |
| Arduino CLI 1.2.0, existing Arduino-ESP32 core/SDK 2.0.17, all warnings enabled | PASS |
| Compiler warnings in both firmware builds | None observed |
| Local credentials validated without displaying values; trusted subnet preserved | PASS: `172.20.10.0/28` |
| Rebuilt ZIP: exact four-file inventory, matching source/configuration bytes and valid CRCs | PASS |

Current local build/test results, ZIP content validation and source-preservation evidence are stored under ignored `artifacts/camera-release/`. Credentialed compiler output is captured privately in memory; only build status, warning counts and memory-size summaries are recorded. No operator configuration, ZIP, compiled firmware or private verification logs belong in a source commit.

Arduino CLI verification uses the existing Arduino-ESP32 2.0.17 core/SDK and compiler through a temporary local adapter with the matching 2.0.17 Arduino build recipes. This avoids installing unused chip toolchains on a disk with limited free space. Windows should use the standard Espressif Boards Manager package 2.0.17 and the settings above. Click **Verify** on the Dell before a manual upload.

Hardware identity, base USB-UART identity/boot controls, detached power suitability and actual optical/Wi-Fi/video operation remain unverified. These remain upload/commissioning blockers even when the private Wi-Fi configuration is complete. The /28 network policy is now supported. No firmware upload or external sharing of the private archive was performed.
