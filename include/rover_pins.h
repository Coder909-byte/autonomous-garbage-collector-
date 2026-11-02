#pragma once
namespace pins {
constexpr int L_FWD=16, L_REV=17, R_FWD=18, R_REV=19;
constexpr int TF=32, EF=34, TL=33, EL=35, TR=13, ER=36;
// One L298N: channel A drives both brushes; channel B drives the conveyor.
constexpr int BRUSH_IN1=21, BRUSH_IN2=22, CONVEYOR_IN3=23, CONVEYOR_IN4=25;
constexpr int ENABLE=14, ESTOP_OK=27;
constexpr int PWM[] = {L_FWD,L_REV,R_FWD,R_REV};
constexpr int AUX[] = {BRUSH_IN1,BRUSH_IN2,CONVEYOR_IN3,CONVEYOR_IN4};
constexpr int TRIG[] = {TF,TL,TR};
constexpr int ECHO[] = {EF,EL,ER};
}
