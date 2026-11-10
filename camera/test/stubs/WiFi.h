#pragma once
#include "Arduino.h"
#include <arpa/inet.h>
class IPAddress {
 uint32_t value=0;
 public:
 IPAddress()=default;IPAddress(uint32_t v):value(v){}IPAddress(int a,int b,int c,int d){value=static_cast<uint32_t>(a|(b<<8)|(c<<16)|(d<<24));}
 uint8_t operator[](unsigned i)const{return static_cast<uint8_t>(value>>(8*i));}
 operator uint32_t()const{return value;}
 bool fromString(const char*s){return inet_pton(AF_INET,s,&value)==1;}
 std::string toString()const{char b[40];inet_ntop(AF_INET,&value,b,sizeof(b));return b;}
};
constexpr int WL_CONNECTED=3,WIFI_STA=1;
struct WiFiMock{int state=WL_CONNECTED,attempts=0;IPAddress ip{192,168,50,10};int status(){return state;}IPAddress localIP(){return ip;}void mode(int){}void setAutoReconnect(bool){}void setHostname(const char*){}void disconnect(){state=0;}void begin(const char*,const char*){++attempts;}};
static WiFiMock WiFi;
