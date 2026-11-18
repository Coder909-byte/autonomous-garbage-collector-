#pragma once

namespace rover {
// Release evidence, not hardware detection. Set these only after the actual
// installation is qualified and its measurement/review record is retained.
struct Commissioning {
  bool driverInterface, motorPowerProtection, independentDisconnect;
  bool failOff, supplyAndGround, motorCurrentAndThermal;
  const char *record;
  constexpr bool ready() const {
    return driverInterface && motorPowerProtection && independentDisconnect &&
      failOff && supplyAndGround && motorCurrentAndThermal && record && record[0];
  }
};
#if defined(ROVER_COMMISSIONING_TEST_FIXTURE)
#if defined(ARDUINO) || defined(ARDUINO_ARCH_ESP32) || defined(ESP_PLATFORM)
#error Commissioning test fixture is forbidden in hardware firmware
#endif
// Host-only branch coverage; never a physical commissioning/release claim.
constexpr Commissioning COMMISSIONING = {true,true,true,true,true,true,"HOST TEST ONLY"};
#else
// Available hardware has not met these requirements. No serial/UI bypass.
constexpr Commissioning COMMISSIONING = {true,true,true,true,true,true,""};
#endif
constexpr bool COMMISSIONING_READY = COMMISSIONING.ready();
}
