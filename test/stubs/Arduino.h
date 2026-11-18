#pragma once
// Host-only Arduino boundary model. Never used by ESP32 builds.
#include <stdint.h>
#include <stdio.h>
#include <string>
#include <algorithm>
#define IRAM_ATTR
#define HIGH 1
#define LOW 0
#define INPUT 0
#define INPUT_PULLDOWN 2
#define OUTPUT 1
#define FALLING 2
using portMUX_TYPE = int;
#define portMUX_INITIALIZER_UNLOCKED 0
#define portENTER_CRITICAL(x) ((void)(x))
#define portEXIT_CRITICAL(x) ((void)(x))
#define portENTER_CRITICAL_ISR(x) ((void)(x))
#define portEXIT_CRITICAL_ISR(x) ((void)(x))
static uint32_t mockNow=0;
static int mockPins[40]={}, mockModes[40]={};
static unsigned mockDuty[4]={};
static bool mockPwmFailure=false, mockHazard=false;
static unsigned mockEnableHighCount=0;
static unsigned mockMotorHighCount=0, mockNonzeroDutyCount=0, mockPwmSetupCount=0, mockPwmAttachCount=0;
static unsigned long mockPulse=5800;
static void (*mockInterrupt)()=nullptr;
static uint32_t millis() { return mockNow; }
static void pinMode(int p,int mode) { mockModes[p]=mode; }
static void digitalWrite(int p,int v) {
  mockPins[p]=v;
  if (p==14 && v) ++mockEnableHighCount;
  if (v && (p==14 || (p>=16 && p<=19) || p==21 || p==22 || p==23 || p==25)) ++mockMotorHighCount;
}
static int digitalRead(int p) { return mockPins[p]; }
static void delayMicroseconds(unsigned) {}
static unsigned long pulseIn(int,int,unsigned long) { return mockPulse; }
static inline int digitalPinToInterrupt(int p) { return p; }
static inline void attachInterrupt(int,void (*fn)(),int) { mockInterrupt=fn; }
static inline double ledcSetup(unsigned,int,int) { ++mockPwmSetupCount; return mockPwmFailure ? 0 : 1200; }
static inline void ledcAttachPin(int,unsigned) { ++mockPwmAttachCount; }
static inline void ledcWrite(unsigned channel,unsigned duty) {
  if (duty) ++mockNonzeroDutyCount;
  mockDuty[channel]=duty;
  if (mockPins[14] && ((mockDuty[0] && mockDuty[1]) || (mockDuty[2] && mockDuty[3]))) mockHazard=true;
}
struct MockSerial {
  std::string input, output;
  void begin(int) {}
  void println(const char *s) { output += std::string(s)+"\n"; }
  template<typename... T> void printf(const char *format,T... args) { char b[1024]; snprintf(b,sizeof(b),format,args...); output+=b; }
  int availableForWrite() { return 128; }
  int available() { return static_cast<int>(input.size()); }
  int read() { char c=input[0]; input.erase(0,1); return c; }
};
static MockSerial Serial;
