#pragma once
#include <stdint.h>
#include <stdio.h>
#include <string.h>
namespace cam {
constexpr const char *BOUNDARY="roverframe";
constexpr const char *STREAM_TYPE="multipart/x-mixed-replace;boundary=roverframe";
inline bool settings(int size,int quality,bool psram) {
  return (size==320 || (size==640 && psram)) && quality>=10 && quality<=40;
}
inline bool credentials(const char *ssid,const char *password) {
  return strlen(ssid)>0 && strlen(ssid)<=32 && strlen(password)>=8 && strlen(password)<=63;
}
// Bounded bursts: five 15-second connection attempts, capped exponential delays,
// then 60-second cooldown. Retry after cooldown without reboot or AP fallback.
struct Retry {
  unsigned attempts=0; bool connecting=false, cooldown=false; uint32_t at=0, delay=0;
  bool tick(uint32_t now,bool connected) {
    if (connected) { attempts=0;connecting=false;cooldown=false;at=now;delay=0;return false; }
    if (connecting) {
      if (uint32_t(now-at)<15000) return false;
      connecting=false;at=now;delay=2000u<<(attempts-1);
      if (attempts>=5) { cooldown=true;delay=60000; }
    }
    if (uint32_t(now-at)<delay) return false;
    if (cooldown) { attempts=0;cooldown=false; }
    ++attempts;connecting=true;at=now;return true;
  }
};
inline int partHeader(char *buffer,unsigned cap,unsigned length) {
  return snprintf(buffer,cap,"\r\n--roverframe\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n",length);
}
// Used by actual HTTP handlers and host mocks; returns every captured resource
// even after failed transmission. Allocation/capture failure is explicit.
template<class IO> bool frame(IO &io,bool multipart) {
  auto fb=io.get();
  if (!fb) { io.unavailable();return false; }
  bool ok=io.send(fb,multipart);
  io.release(fb);
  return ok;
}
}
