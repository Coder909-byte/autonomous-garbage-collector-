// POSIX mock serial device; same controller, interlock and serializer as ESP32.
// No GPIO, PWM or physical safety feedback is measured here.
#include "rover_telemetry.h"
#include <chrono>
#include <iostream>
#include <unistd.h>
#include <sys/select.h>
int main(int argc,char **argv) {
 std::string scene=argc>1?argv[1]:"clear";
 rover::Controller c;rover::MotionGate gate;rover::LineParser parser;
 auto start=std::chrono::steady_clock::now();uint32_t last=0;
 std::cout<<"READY SIMULATION DISARMED\n"<<std::flush;
 while(true) {
  uint32_t now=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-start).count();
  bool healthy=!(scene=="estop" && now>=3000);
  int front=scene=="obstacle" && now>=3000 && now<6000?25:120;
  for(unsigned i=0;i<3;++i)c.sample(i,scene=="sensor-fault"&&now>=3000&&i==0?-1:(i==0?front:(i==1?100:70)),now);
  fd_set fds;FD_ZERO(&fds);FD_SET(STDIN_FILENO,&fds);timeval wait{0,20000};
  int available=select(1,&fds,nullptr,nullptr,&wait);
  if(available>0) {
   char bytes[64];ssize_t n=read(STDIN_FILENO,bytes,sizeof(bytes));if(n<=0)break;
   for(ssize_t i=0;i<n;++i) {
    auto r=parser.feed(bytes[i]);
    if(r==rover::LineParser::Overflow){c.disarm();std::cout<<"ERR line overflow; DISARMED\n";}
    if(r==rover::LineParser::Ready)std::cout<<(c.command(parser.line(),now,healthy)?"OK ":"ERR ")<<parser.line()<<"\n";
   }
  }
  c.tick(now,healthy);auto applied=gate.update(c.armed&&!c.estop?c.motion:rover::Motion::Stop,now);
  bool enabled=applied!=rover::Motion::Stop && healthy && c.armed&&!c.estop;
  if(!enabled)applied=rover::Motion::Stop;c.reportApplied(applied,now);
  if(now-last>=100) {
   last=now;char b[512];rover::telemetry(b,sizeof(b),c,now,applied,enabled,enabled&&applied==rover::Motion::Forward&&c.brushOutput(),enabled&&applied==rover::Motion::Forward&&c.conveyorOutput(),healthy);
   std::cout<<b<<"\n"<<std::flush;
  }
 }
}
