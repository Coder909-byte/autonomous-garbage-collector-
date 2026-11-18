#pragma once
// Host-only Wi-Fi boundary model backed by loopback TCP. Never used by ESP32
// builds. ROVER_SIM_WIFI_PORT overrides the listening port for parallel tests.
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <stdlib.h>
#include <string>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>

#define WIFI_AP 2
struct MockIP { std::string toString() const { return "192.168.4.1"; } };
struct MockWiFi {
  bool apStarted = false;
  void mode(int) {}
  void setSleep(bool) {}
  bool softAP(const char *, const char *, int, int, int) { apStarted = true; return true; }
  MockIP softAPIP() const { return {}; }
};
static MockWiFi WiFi;

class WiFiClient {
 public:
  WiFiClient() = default;
  explicit WiFiClient(int fd) : socket(fd) {}
  explicit operator bool() const { return socket >= 0; }
  int fd() const { return socket; }
  bool connected() {
    if (socket < 0) return false;
    char probe;
    ssize_t n = recv(socket, &probe, 1, MSG_PEEK | MSG_DONTWAIT);
    return n > 0 || (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK));
  }
  int available() {
    int n = 0;
    return socket >= 0 && ioctl(socket, FIONREAD, &n) == 0 ? n : 0;
  }
  int read() {
    unsigned char c;
    return socket >= 0 && recv(socket, &c, 1, MSG_DONTWAIT) == 1 ? c : -1;
  }
  void setNoDelay(bool on) {
    int flag = on ? 1 : 0;
    if (socket >= 0) setsockopt(socket, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));
  }
  void stop() { if (socket >= 0) close(socket); socket = -1; }
 private:
  int socket = -1;
};

class WiFiServer {
 public:
  explicit WiFiServer(int port) : port(port) {}
  void begin() {
    const char *override = getenv("ROVER_SIM_WIFI_PORT");
    if (override) port = atoi(override);
    listener = socket(AF_INET, SOCK_STREAM, 0);
    int reuse = 1;
    setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(static_cast<uint16_t>(port));
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(listener, reinterpret_cast<sockaddr *>(&address), sizeof(address)) != 0 || listen(listener, 2) != 0) {
      close(listener); listener = -1; return;
    }
    fcntl(listener, F_SETFL, O_NONBLOCK);
  }
  void setNoDelay(bool) {}
  bool hasClient() {
    if (pending < 0 && listener >= 0) {
      pending = ::accept(listener, nullptr, nullptr);
      if (pending >= 0) fcntl(pending, F_SETFL, O_NONBLOCK);
    }
    return pending >= 0;
  }
  WiFiClient accept() { WiFiClient next(pending); pending = -1; return next; }
 private:
  int port, listener = -1, pending = -1;
};
