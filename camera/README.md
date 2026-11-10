# Separate ESP32-CAM firmware

Supported configuration: AI-Thinker ESP32-CAM with OV2640-style camera mapping. Actual rover camera identity is **not verified**. Main ESP32 pins and firmware stay separate.

Copy `include/config.example.h` to ignored `include/secrets.h`; set the isolated trusted Wi-Fi SSID/password and private /24 subnet. Empty credentials disable Wi-Fi. Do not commit credentials. Configure the actual subnet, not an arbitrary example. No open AP fallback or public-internet endpoint is created.

From repository root:

```sh
.venv/bin/pio run -d camera -e ai_thinker_esp32cam
python3 scripts/build_simulator.py
```

Later, only after approved detached hardware/programmer setup, manually run `.venv/bin/pio run -d camera -e ai_thinker_esp32cam -t upload --upload-port YOUR_CAMERA_PROGRAMMER`. No upload has been performed. Serial monitor is 115200 baud and prints init errors, PSRAM, configured defaults, retries and acquired IP. mDNS advertises `rover-camera.local`; the dashboard accepts the numeric private IPv4 from serial/DHCP so DNS cannot redirect camera proxy access.

With PSRAM: JPEG VGA 640x480, quality 12, two PSRAM frame buffers. Without PSRAM: QVGA 320x240, quality 14, one DRAM frame buffer. Capture or initialization failure leaves explicit unavailable responses. Settings support QVGA and VGA only (VGA requires PSRAM); JPEG quality 10–40, lower number means higher quality. Disconnect stream before settings. No frame-rate guarantee or measured performance is claimed.

Endpoints: GET `:80/status` (JSON connection/readiness/streaming/IP/PSRAM/settings), GET `:80/snapshot` (JPEG), POST `:80/settings?width=320&quality=14`, GET `:81/stream` (MJPEG `roverframe` boundary). Separate HTTP servers keep status/snapshot responsive during a stream; a mutex protects frame capture/settings. Only one stream is accepted. Every captured framebuffer is returned even on failed send. Sockets have three-second send/receive timeouts; Wi-Fi loss exits streaming. Camera init failure requires inspection/reboot; no rapid endless init loop is used.

Wi-Fi retries use five 15s attempts, 2/4/8/16s delays and a 60s cooldown after the fifth failed attempt, then another bounded burst. Success resets the burst. No automatic alternative network. Peers and acquired station IP must be in the explicitly configured RFC1918 /24. Firmware validates credentials/subnet before enabling Wi-Fi. This is network isolation, **not per-user authentication or TLS**: any authorized WLAN peer can view/change settings. Keep this network private; do not port-forward, tunnel or expose camera endpoints publicly. The camera has no motor commands.

Host tests compile the actual HTTP handlers against explicit Wi-Fi/camera/HTTP mocks, plus policy/resource tests. They validate formats, permission/error paths and cleanup, not radio behavior, optics, DMA timing or real video. See [camera power and physical acceptance](../docs/CAMERA_WIRING.md), [laptop setup](../docs/LAPTOP_CONTROL_SETUP.md), and [Espressif driver](https://github.com/espressif/esp32-camera).
