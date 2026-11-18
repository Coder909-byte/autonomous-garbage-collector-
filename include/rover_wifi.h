#pragma once
// Optional Wi-Fi command link for the main ESP32 (compiled only with ROVER_WIFI).
// The ESP32 hosts its own WPA2 access point and serves the same line protocol
// as USB on one TCP port. USB stays active. Losing the Wi-Fi client disarms;
// the 1200 ms command deadline still covers a silent radio dropout.
#include <WiFi.h>
#include <stdarg.h>
#include <stdio.h>
#if defined(ARDUINO)
#include <lwip/sockets.h>
#else
#include <sys/socket.h>
#endif

#ifndef ROVER_WIFI_SSID
#define ROVER_WIFI_SSID "ROVER-CTRL"
#endif
#ifndef ROVER_WIFI_PASSWORD
#define ROVER_WIFI_PASSWORD "rover-collector"
#endif
#ifndef ROVER_WIFI_PORT
#define ROVER_WIFI_PORT 3333
#endif
static_assert(sizeof(ROVER_WIFI_PASSWORD) - 1 >= 8, "WPA2 password needs at least 8 characters");
static_assert(sizeof(ROVER_WIFI_SSID) - 1 >= 1, "Wi-Fi SSID must not be empty");

namespace rover {
class WifiLink {
 public:
  bool begin() {
    WiFi.mode(WIFI_AP);
    WiFi.setSleep(false);
    // Channel 1, visible SSID, up to 4 stations (laptop plus ESP32-CAM).
    // Only one TCP client holds control at a time.
    up = WiFi.softAP(ROVER_WIFI_SSID, ROVER_WIFI_PASSWORD, 1, 0, 4);
    if (up) { server.begin(); server.setNoDelay(true); }
    return up;
  }
  bool ready() const { return up; }
  // Returns true when a controlling client was lost or replaced since the last call.
  bool service() {
    bool lost = failed;
    failed = false;
    if (client && !client.connected()) { client.stop(); lost = true; }
    if (up && server.hasClient()) {
      // The newest connection wins so a laptop can reconnect after a dropout
      // without waiting for the dead socket to time out.
      if (client) { client.stop(); lost = true; }
      client = server.accept();
      client.setNoDelay(true);
      fresh = true;
    }
    return lost;
  }
  // True once per new client, so the caller can discard any partial line.
  bool connectedNow() { bool value = fresh; fresh = false; return value; }
  WiFiClient &stream() { return client; }
  int available() { return client ? client.available() : 0; }
  int read() { return client.read(); }

  // Tee used for every protocol line: USB exactly as before, plus the client.
  void println(const char *text) { printf("%s\n", text); }
  void printf(const char *format, ...) __attribute__((format(printf, 2, 3))) {
    char line[600];
    va_list args;
    va_start(args, format);
    int length = vsnprintf(line, sizeof(line), format, args);
    va_end(args);
    if (length < 0) return;
    if (length >= static_cast<int>(sizeof(line))) length = sizeof(line) - 1;
    Serial.printf("%s", line);
    send(line, static_cast<size_t>(length));
  }

 private:
  void send(const char *data, size_t length) {
    if (!client || !length) return;
    // Never block the control loop on a stalled radio link. A partial or
    // refused write would corrupt the line stream, so the client is dropped
    // (which disarms) instead of queuing stale telemetry.
#ifdef MSG_NOSIGNAL
    const int flags = MSG_DONTWAIT | MSG_NOSIGNAL;
#else
    const int flags = MSG_DONTWAIT;
#endif
    ssize_t sent = ::send(client.fd(), data, length, flags);
    if (sent != static_cast<ssize_t>(length)) { client.stop(); failed = true; }
  }
  WiFiServer server{ROVER_WIFI_PORT};
  WiFiClient client;
  bool up = false, failed = false, fresh = false;
};
} // namespace rover
