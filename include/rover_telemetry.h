#pragma once
#include "rover_control.h"
#include <stdio.h>
namespace rover {
constexpr const char *FIRMWARE_ID="rover-usb-v1";
// Adapter-supplied output state: never claims encoders or physical movement.
inline int telemetry(char *out,unsigned capacity,const Controller &c,uint32_t now,
                     Motion applied,bool enabled,bool brush,bool conveyor,bool healthy) {
  return snprintf(out,capacity,
    "TEL {\"v\":1,\"fw\":\"%s\",\"ms\":%lu,\"armed\":%s,\"auto\":%s,\"estop\":%s,\"healthy\":%s,"
    "\"requested\":%d,\"applied\":%d,\"en\":%s,\"brushReq\":%s,\"conveyorReq\":%s,\"brush\":%s,\"conveyor\":%s,"
    "\"nav\":\"%s\",\"cm\":[%d,%d,%d],\"age\":[%lu,%lu,%lu]}",
    FIRMWARE_ID,static_cast<unsigned long>(now),c.armed?"true":"false",c.automatic?"true":"false",c.estop?"true":"false",healthy?"true":"false",
    static_cast<int>(c.motion),static_cast<int>(applied),enabled?"true":"false",c.brushes?"true":"false",c.conveyor?"true":"false",brush?"true":"false",conveyor?"true":"false",c.navigationName(),
    c.ranges[0].cm,c.ranges[1].cm,c.ranges[2].cm,
    static_cast<unsigned long>(uint32_t(now-c.ranges[0].at)),static_cast<unsigned long>(uint32_t(now-c.ranges[1].at)),static_cast<unsigned long>(uint32_t(now-c.ranges[2].at)));
}
}
