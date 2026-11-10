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
int main() {
  assert(cam::credentials("rover","12345678"));assert(!cam::credentials("","12345678"));assert(!cam::credentials("rover",""));
  assert(cam::settings(320,14,false));assert(!cam::settings(640,12,false));assert(cam::settings(640,12,true));assert(!cam::settings(800,12,true));assert(!cam::settings(320,9,true));assert(!cam::settings(320,41,true));
  cam::Retry r;uint32_t now=0;
  for(unsigned i=1;i<=5;++i){assert(r.tick(now,false));assert(r.attempts==i);assert(!r.tick(now+14999,false));now+=15000;assert(!r.tick(now,false));now+=i==5?60000:(2000u<<(i-1));}
  assert(r.tick(now,false));assert(r.attempts==1);assert(!r.tick(now+1,true));assert(r.attempts==0);assert(r.tick(now+2,false));
  Mock m;assert(cam::frame(m,false));assert(m.returned==1);assert(cam::frame(m,true));m.works=false;assert(!cam::frame(m,true));assert(m.returned==3);m.exists=false;assert(!cam::frame(m,false));assert(m.errors==1 && m.returned==3);
  puts("camera policy/resource mocks: PASS (credentials, settings, reconnect burst/cooldown, snapshot, MJPEG framing, send/capture failures)");
}
