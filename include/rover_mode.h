#pragma once

// Compile-time selection only. No serial/dashboard command can change this.
#define PROTECTED_ROVER 1
#define USB_BENCH_DIAGNOSTIC 2
#ifndef ROVER_OPERATING_MODE
#define ROVER_OPERATING_MODE PROTECTED_ROVER
#endif
#if ROVER_OPERATING_MODE != PROTECTED_ROVER && ROVER_OPERATING_MODE != USB_BENCH_DIAGNOSTIC
#error Unknown ROVER_OPERATING_MODE
#endif

namespace rover {
constexpr bool MOTOR_CAPABLE = ROVER_OPERATING_MODE == PROTECTED_ROVER;
constexpr const char *OPERATING_MODE = MOTOR_CAPABLE ? "PROTECTED_ROVER" : "USB_BENCH_DIAGNOSTIC";
}
