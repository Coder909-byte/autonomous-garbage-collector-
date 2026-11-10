#pragma once
// SUPPORTED CONFIGURATION ONLY: physical module identity remains unverified.
// Espressif Arduino 2.0.17 CameraWebServer/camera_pins.h, AI_THINKER section.
#ifndef CAMERA_BOARD_AI_THINKER
#error Select a reviewed camera-board configuration explicitly
#endif
namespace camera_board {
constexpr int PWDN=32, RESET=-1, XCLK=0, SIOD=26, SIOC=27;
constexpr int D0=5, D1=18, D2=19, D3=21, D4=36, D5=39, D6=34, D7=35;
constexpr int VSYNC=25, HREF=23, PCLK=22;
}
