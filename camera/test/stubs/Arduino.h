#pragma once
#include <stdint.h>
#include <stdio.h>
#include <string>
#include <cstring>
static uint32_t fakeNow=0;
static bool fakeMutexFail=false,fakeLockAvailable=true;
using SemaphoreHandle_t=int*;
constexpr int pdTRUE=1;
#define pdMS_TO_TICKS(n) (n)
static SemaphoreHandle_t xSemaphoreCreateMutex(){static int mutex;return fakeMutexFail?nullptr:&mutex;}
static int xSemaphoreTake(SemaphoreHandle_t lock,int){if(!lock||!fakeLockAvailable)return 0;fakeLockAvailable=false;return pdTRUE;}
static void xSemaphoreGive(SemaphoreHandle_t){fakeLockAvailable=true;}
static void delay(unsigned n){fakeNow+=n;}
static void vTaskDelay(unsigned n){fakeNow+=n;}
static uint32_t millis(){return fakeNow;}
static bool fakePSRAM=true;
static bool psramFound(){return fakePSRAM;}
struct SerialMock{std::string output;void begin(int){}void println(const char*s){output+=s;output+='\n';}template<class... T>void printf(const char*s,T...args){char b[512];snprintf(b,sizeof(b),s,args...);output+=b;}};
static SerialMock Serial;
struct ESPMock{unsigned getFreeHeap(){return 123456;}};static ESPMock ESP;
