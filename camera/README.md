# Separate ESP32-CAM firmware

Supported configuration: AI-Thinker ESP32-CAM with OV2640-style camera mapping. Actual rover camera identity is **not verified**. Main ESP32 pins and firmware stay separate.

Copy `include/config.example.h` to ignored `include/secrets.h` only if it does not already exist; set the isolated trusted Wi-Fi SSID/password and private /24 or /28 subnet. Empty credentials disable Wi-Fi. Do not commit credentials. Configure the actual subnet, not an arbitrary example. No open AP fallback or public-internet endpoint is created.

The verified iPhone hotspot uses `CAMERA_TRUSTED_NETWORK "172.20.10.0"` and `CAMERA_TRUSTED_MASK "255.255.255.240"`. Its usable hosts are `172.20.10.1` through `.14`; `.0` is the network and `.15` is broadcast. The Mac is `.3`; discover the camera's own DHCP address via serial. See the [Dell G15 Arduino IDE guide](../docs/ESP32_CAM_ARDUINO_WINDOWS.md) for the separately packaged sketch and upload procedure.

From repository root:

```sh
.venv/bin/pio run -d camera -e ai_thinker_esp32cam
python3 scripts/build_simulator.py
```

Later, only after approved detached hardware/programmer setup, manually run `.venv/bin/pio run -d camera -e ai_thinker_esp32cam -t upload --upload-port YOUR_CAMERA_PROGRAMMER`. No upload has been performed. Serial monitor is 115200 baud and prints init errors, PSRAM, configured defaults, retries and acquired IP. mDNS advertises `rover-camera.local`; the dashboard accepts the numeric private IPv4 from serial/DHCP so DNS cannot redirect camera proxy access.

With PSRAM: JPEG VGA 640x480, quality 12, two PSRAM frame buffers. Without PSRAM: QVGA 320x240, quality 14, one DRAM frame buffer. Capture or initialization failure leaves explicit unavailable responses. Settings support QVGA and VGA only (VGA requires PSRAM); JPEG quality 10–40, lower number means higher quality. Disconnect stream before settings. No frame-rate guarantee or measured performance is claimed.

Endpoints: GET `:80/status` (JSON connection/readiness/streaming/IP/PSRAM/settings), GET `:80/snapshot` (JPEG), POST `:80/settings?width=320&quality=14`, GET `:81/stream` (MJPEG `roverframe` boundary). Separate HTTP servers keep status/snapshot responsive during a stream; a mutex protects frame capture/settings. Only one stream is accepted. Every captured framebuffer is returned even on failed send. Sockets have three-second send/receive timeouts; Wi-Fi loss exits streaming. Camera init failure requires inspection/reboot; no rapid endless init loop is used.

Wi-Fi retries use five 15s attempts, 2/4/8/16s delays and a 60s cooldown after the fifth failed attempt, then another bounded burst. Success resets the burst. No automatic alternative network. Peers and acquired station IP must be usable hosts in the explicitly configured RFC1918 /24 or /28. The production `cam::TrustedNetwork` policy accepts only masks `255.255.255.0` and `255.255.255.240`, canonical network bases and strict dotted-decimal addresses. It rejects host bits in a network base, malformed/noncontiguous/unsupported masks, public/reserved ranges and network/broadcast host addresses. Integer arithmetic packs IPv4 octets explicitly. Every HTTP handler validates Wi-Fi connection, the camera address and the IPv4 peer (including IPv4-mapped peers from the SDK's dual-stack listener; native IPv6 is rejected); Wi-Fi loss or station subnet loss terminates a stream. The configured allowlist does not assign a static address or change DHCP's subnet mask. Firmware validates credentials/subnet before enabling station-only Wi-Fi. This is network isolation, **not per-user authentication or TLS**: any authorized WLAN peer can view/change settings. Keep this network private; do not port-forward, tunnel or expose camera endpoints publicly. The camera has no motor commands.

Host tests compile the actual HTTP handlers against explicit Wi-Fi/camera/HTTP mocks, plus policy/resource tests. The deterministic `test/stubs/camera_test_config.h`, selected only by `CAMERA_HOST_TEST`, contains empty/synthetic values, so host tests never read local Wi-Fi credentials. Every file named `secrets.h` remains Git-ignored. Tests exhaust /24 and /28 host boundaries and cover shifted /28 networks, malformed configuration, rejected peers/station addresses on all four endpoints, station-only setup, disconnects, stream cleanup and the existing camera functionality. They validate formats, permission/error paths and cleanup, not radio behavior, optics, DMA timing or real video. See [camera power and physical acceptance](../docs/CAMERA_WIRING.md), [laptop setup](../docs/LAPTOP_CONTROL_SETUP.md), and [Espressif driver](https://github.com/espressif/esp32-camera).
