#pragma once
struct MDNSMock{void begin(const char*){}void addService(const char*,const char*,int){}void end(){}};static MDNSMock MDNS;
