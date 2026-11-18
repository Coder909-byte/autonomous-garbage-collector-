// Actual USB bench firmware adapter with host GPIO/serial mocks and synthetic
// ultrasonic echoes. Never opens a device or generates physical outputs.
#include "../../firmware/rover.ino"
#include <chrono>
#include <iostream>
#include <unistd.h>
#include <sys/select.h>
static_assert(!rover::MOTOR_CAPABLE,"Compile this harness in bench mode only");
int main() {
  const auto start=std::chrono::steady_clock::now();
  setup();
  while (true) {
    fd_set fds; FD_ZERO(&fds); FD_SET(STDIN_FILENO,&fds); timeval wait{0,10000};
    if (select(1,&fds,nullptr,nullptr,&wait)>0) {
      char data[64]; const ssize_t n=read(STDIN_FILENO,data,sizeof(data));
      if (n<=0) break;
      Serial.input.append(data,n);
    }
    mockNow=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-start).count();
    const unsigned distances[]={120,100,70}; mockPulse=58*distances[sensorIndex];
    loop();
    if (mockMotorHighCount || mockNonzeroDutyCount || mockPwmAttachCount) return 1;
    std::cout<<Serial.output<<std::flush; Serial.output.clear();
  }
}
