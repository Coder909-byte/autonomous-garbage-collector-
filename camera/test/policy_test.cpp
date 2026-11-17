#include "camera_policy.h"
#include <assert.h>
#include <string>
struct Mock {
  bool exists=true,works=true;int returned=0,errors=0,sent=0;
  int *get() { static int frame;return exists?&frame:nullptr; }
  void unavailable(){++errors;}
  bool send(int*,bool multipart){++sent;if(multipart){char b[120];int n=cam::partHeader(b,sizeof(b),123);assert(std::string(b,n).find("Content-Length: 123\r\n\r\n")!=std::string::npos);}return works;}
  void release(int*){++returned;}
};
static void networkTests() {
  cam::TrustedNetwork network;
  assert(!network.contains(cam::ipv4(172,20,10,3)));
  assert(network.configure("172.20.10.0","255.255.255.240"));
  // Exhaust all last-octet addresses: only the fourteen /28 hosts qualify.
  for (unsigned host=0;host<256;++host)
    assert(network.contains(cam::ipv4(172,20,10,host))==(host>=1 && host<=14));
  for (uint32_t address:{cam::ipv4(172,20,9,3),cam::ipv4(172,20,11,3),
       cam::ipv4(172,21,10,3),cam::ipv4(10,20,10,3),cam::ipv4(127,0,0,1),
       cam::ipv4(169,254,10,3),cam::ipv4(224,0,0,1),cam::ipv4(8,8,8,8),0u,0xffffffffu})
    assert(!network.contains(address));
  assert(network.configure("192.168.50.0","255.255.255.0"));
  for (unsigned host=0;host<256;++host)
    assert(network.contains(cam::ipv4(192,168,50,host))==(host>=1 && host<=254));
  assert(!network.contains(cam::ipv4(192,168,51,3)));
  // /28 networks need not end in .0; test both subnet edges and both RFC1918 edges.
  assert(network.configure("172.20.10.16","255.255.255.240"));
  for (unsigned host=0;host<256;++host)
    assert(network.contains(cam::ipv4(172,20,10,host))==(host>=17 && host<=30));
  for (const char *base:{"10.0.0.0","10.255.255.240","172.16.0.0","172.31.255.240","192.168.0.0","192.168.255.240"})
    assert(network.configure(base,"255.255.255.240"));
  for (const char *base:{"10.0.0.0","10.255.255.0","172.16.0.0","172.31.255.0","192.168.0.0","192.168.255.0"})
    assert(network.configure(base,"255.255.255.0"));
  for (const char *base:{"0.0.0.0","8.8.8.0","100.64.0.0","127.0.0.0","169.254.0.0","172.15.255.0","172.32.0.0","192.167.0.0","192.169.0.0","224.0.0.0","240.0.0.0","255.255.255.0"})
    for (const char *mask:{"255.255.255.0","255.255.255.240"})
      assert(!network.configure(base,mask));
  for (const char *mask:{"0.0.0.0","255.255.0.0","255.255.255.128","255.255.255.224","255.255.255.248","255.255.255.252","255.255.255.255","255.0.255.240","255.255.255.15","255.255.255.241","255.255.255.256","255.255.255","/28","28",""," 255.255.255.240","255.255.255.240 "}) {
    assert(network.configure("172.20.10.0","255.255.255.240"));
    assert(!network.configure("172.20.10.0",mask));
    assert(!network.contains(cam::ipv4(172,20,10,3))); // failed reconfigure fails closed
  }
  for (const char *base:{"172.20.10.1","172.20.10.15","172.20.10.17","172.20.10.255"})
    assert(!network.configure(base,"255.255.255.240"));
  assert(!network.configure("192.168.50.1","255.255.255.0"));
  for (const char *bad:{"","172.20.10","172.20.10.0.1","172.20..0","172.20.10.256","-1.20.10.0","+172.20.10.0","172.020.10.0","172.20.10.00"," 172.20.10.0","172.20.10.0 ","172.20.10.0/28","172.20.10.0junk","172.20.10.0\n","4294967296.0.0.0"}) {
    uint32_t address=123;
    assert(!cam::parseIPv4(bad,address));assert(address==123);
    assert(!network.configure(bad,"255.255.255.240"));
  }
  assert(!network.configure(nullptr,"255.255.255.240"));
  assert(!network.configure("172.20.10.0",nullptr));
  uint32_t address=0;assert(cam::parseIPv4("172.20.10.3",address));
  assert(address==0xac140a03u); // explicit network-order representation
}
int main() {
  networkTests();
  assert(cam::credentials("rover","12345678"));assert(!cam::credentials("","12345678"));assert(!cam::credentials("rover",""));
  assert(cam::settings(320,14,false));assert(!cam::settings(640,12,false));assert(cam::settings(640,12,true));assert(!cam::settings(800,12,true));assert(!cam::settings(320,9,true));assert(!cam::settings(320,41,true));
  cam::Retry r;uint32_t now=0;
  for(unsigned i=1;i<=5;++i){assert(r.tick(now,false));assert(r.attempts==i);assert(!r.tick(now+14999,false));now+=15000;assert(!r.tick(now,false));now+=i==5?60000:(2000u<<(i-1));}
  assert(r.tick(now,false));assert(r.attempts==1);assert(!r.tick(now+1,true));assert(r.attempts==0);assert(r.tick(now+2,false));
  Mock m;assert(cam::frame(m,false));assert(m.returned==1);assert(cam::frame(m,true));m.works=false;assert(!cam::frame(m,true));assert(m.returned==3);m.exists=false;assert(!cam::frame(m,false));assert(m.errors==1 && m.returned==3);
  puts("camera policy/resource mocks: PASS (strict private /24 and /28, exhaustive host boundaries, invalid masks/addresses, fail-closed reconfiguration, credentials, settings, reconnect, frame cleanup)");
}
