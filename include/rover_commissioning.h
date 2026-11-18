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
#elif defined(ROVER_BENCH_RELEASE)
// Owner-supervised bench release. Selected only by the motor_bench_release
// build or the --bench-release Arduino package; the default build stays locked.
#ifndef ROVER_BENCH_RECORD
#error ROVER_BENCH_RELEASE requires ROVER_BENCH_RECORD, a non-empty operator record string
#endif
constexpr Commissioning COMMISSIONING = {true,true,true,true,true,true,ROVER_BENCH_RECORD};
static_assert(COMMISSIONING.ready(), "ROVER_BENCH_RECORD must not be empty");
#else
// Available hardware has not met these requirements. No serial/UI bypass.
constexpr Commissioning COMMISSIONING = {true,true,true,true,true,true,""};
#endif
constexpr bool COMMISSIONING_READY = COMMISSIONING.ready();
}
