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
// Explicit octet packing avoids IPAddress/socket integer byte-order assumptions.
inline uint32_t ipv4(uint8_t a,uint8_t b,uint8_t c,uint8_t d) {
  return (uint32_t(a)<<24)|(uint32_t(b)<<16)|(uint32_t(c)<<8)|uint32_t(d);
}
inline bool parseIPv4(const char *text,uint32_t &address) {
  if (!text) return false;
  uint32_t value=0;
  for (unsigned octet=0;octet<4;++octet) {
    const char *start=text;unsigned number=0,digits=0;
    while (*text>='0' && *text<='9') {
      number=number*10+unsigned(*text++-'0');
      if (++digits>3 || number>255) return false;
    }
    if (!digits || (digits>1 && *start=='0')) return false;
    value=(value<<8)|number;
    if (octet<3) { if (*text++!='.') return false; }
    else if (*text) return false;
  }
  address=value;return true;
}
class TrustedNetwork {
  uint32_t network_=0,mask_=0;
  bool valid_=false;
public:
  bool configure(const char *network,const char *mask) {
    valid_=false;
    uint32_t n=0,m=0;
    if (!parseIPv4(network,n) || !parseIPv4(mask,m) ||
        (m!=0xffffff00u && m!=0xfffffff0u) || (n&m)!=n) return false;
    const bool privateRange=(n>>24)==10 || (n>>16)==0xc0a8 || (n>>20)==0xac1;
    if (!privateRange) return false;
    network_=n;mask_=m;valid_=true;return true;
  }
  bool contains(uint32_t address) const {
    return valid_ && (address&mask_)==network_ &&
      address!=network_ && address!=(network_|~mask_);
  }
};
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
