// Canonical ESP32 firmware. No motor/battery power is needed for software tests.
#include <Arduino.h>
#include <esp_arduino_version.h>
#include <soc/soc.h>
#include <soc/gpio_reg.h>
#include "rover_control.h"
#include "rover_pins.h"
#include "rover_telemetry.h"

rover::Controller controller;
rover::LineParser parser;
rover::MotionGate gate;
volatile bool hardwareTrip = false;
portMUX_TYPE safetyMux = portMUX_INITIALIZER_UNLOCKED;
bool pwmReady = true;
uint32_t lastPing = 0, lastLog = 0;
unsigned sensorIndex = 0;
rover::Motion appliedMotion = rover::Motion::Stop;
bool appliedEnable = false, appliedBrush = false, appliedConveyor = false;

void IRAM_ATTR stopInterrupt() {
  // GPIO14 is below 32. Cut EN even during pulseIn; the physical power cutoff
  // remains mandatory. Main-loop EN writes use the same critical section.
  portENTER_CRITICAL_ISR(&safetyMux);
  REG_WRITE(GPIO_OUT_W1TC_REG, 1UL << pins::ENABLE);
  hardwareTrip = true;
  portEXIT_CRITICAL_ISR(&safetyMux);
}
bool healthy() { return digitalRead(pins::ESTOP_OK) == HIGH; }
void pwmWrite(unsigned channel, unsigned duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pins::PWM[channel], duty);
#else
  ledcWrite(channel, duty);
#endif
}
void zeroOutputs() {
  digitalWrite(pins::ENABLE, LOW);
  for (unsigned i=0;i<4;++i) pwmWrite(i,0);
  for (int p : pins::AUX) digitalWrite(p,LOW);
}
void applyOutputs(uint32_t now) {
  rover::Motion request = controller.armed && !controller.estop && pwmReady ? controller.motion : rover::Motion::Stop;
  rover::Motion actual = gate.update(request,now);
  // Only rewrite direction channels on a change: avoid transient opposite
  // bridge states and unnecessary PWM resets on every loop iteration.
  static rover::Motion previous = rover::Motion::Stop;
  if (actual != previous || actual == rover::Motion::Stop) {
    zeroOutputs();
    if (actual == rover::Motion::Forward) { pwmWrite(0,150); pwmWrite(2,150); }
    if (actual == rover::Motion::Backward) { pwmWrite(1,150); pwmWrite(3,150); }
    if (actual == rover::Motion::Left) { pwmWrite(1,140); pwmWrite(2,140); }
    if (actual == rover::Motion::Right) { pwmWrite(0,140); pwmWrite(3,140); }
    previous = actual;
  }
  bool brush = actual == rover::Motion::Forward && controller.brushOutput();
  bool conveyor = actual == rover::Motion::Forward && controller.conveyorOutput();
  digitalWrite(pins::BRUSH_IN1,brush); digitalWrite(pins::BRUSH_IN2,LOW);
  digitalWrite(pins::CONVEYOR_IN3,conveyor); digitalWrite(pins::CONVEYOR_IN4,LOW);
  portENTER_CRITICAL(&safetyMux);
  bool permit = actual != rover::Motion::Stop && !hardwareTrip && healthy() && pwmReady;
  digitalWrite(pins::ENABLE,permit ? HIGH : LOW);
  portEXIT_CRITICAL(&safetyMux);
  if (!permit) zeroOutputs();
  // Event telemetry exposes applied outputs, including the neutral interval,
  // so short turns and independently requested auxiliaries can be inspected.
  rover::Motion reported = permit ? actual : rover::Motion::Stop;
  controller.reportApplied(reported,now);
  appliedMotion = reported; appliedEnable = permit;
  appliedBrush = permit && brush; appliedConveyor = permit && conveyor;
  int outputs = static_cast<int>(reported)*4 + (permit && brush ? 2 : 0) + (permit && conveyor ? 1 : 0);
  int state = outputs*16 + static_cast<int>(controller.navigation());
  static int previousState = -1;
  if (state != previousState) {
    previousState = state;
    const char *names[] = {"STOPPED","FORWARD","BACKWARD","LEFT","RIGHT"};
    Serial.printf("STATE motion=%s en=%d brush=%d conveyor=%d nav=%s ms=%lu\n",names[static_cast<int>(reported)],
      permit,permit && brush,permit && conveyor,controller.navigationName(),static_cast<unsigned long>(now));
  }
}
int measure(unsigned index) {
  digitalWrite(pins::TRIG[index],LOW); delayMicroseconds(2);
  digitalWrite(pins::TRIG[index],HIGH); delayMicroseconds(10);
  digitalWrite(pins::TRIG[index],LOW);
  unsigned long us = pulseIn(pins::ECHO[index],HIGH,25000);
  int cm = static_cast<int>(us/58UL);
  return cm>=2 && cm<=400 ? cm : -1;
}
void setup() {
  // Firmware holds EN low after setup begins. Reset/power-ramp safety still
  // requires verified driver input defaults or external pulls (not on hand).
  digitalWrite(pins::ENABLE,LOW); pinMode(pins::ENABLE,OUTPUT);
  for (int p : pins::AUX) { digitalWrite(p,LOW); pinMode(p,OUTPUT); }
  for (int p : pins::TRIG) { digitalWrite(p,LOW); pinMode(p,OUTPUT); }
  for (int p : pins::ECHO) pinMode(p,INPUT);
  // GPIO27 supports an internal pull-down: an open NC contact reads unsafe.
  pinMode(pins::ESTOP_OK,INPUT_PULLDOWN);
  attachInterrupt(digitalPinToInterrupt(pins::ESTOP_OK),stopInterrupt,FALLING);
  if (!healthy()) { hardwareTrip = true; controller.emergency(); }
  for (unsigned i=0;i<4;++i) {
    digitalWrite(pins::PWM[i],LOW); pinMode(pins::PWM[i],OUTPUT);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
    if (!ledcAttach(pins::PWM[i],1200,8)) pwmReady = false;
#else
    if (ledcSetup(i,1200,8) == 0) pwmReady = false;
    ledcAttachPin(pins::PWM[i],i);
#endif
  }
  zeroOutputs();
  Serial.begin(115200);
  Serial.println("READY DISARMED; RESET after ESTOP, then ARM. Motor power stays disconnected for software tests.");
  if (!pwmReady) Serial.println("FAULT PWM setup; arming disabled");
}
void loop() {
  if (hardwareTrip || !healthy()) controller.emergency();
  controller.tick(millis(),healthy());
  applyOutputs(millis());
  // Bounded serial work prevents input flooding from starving the deadman.
  for (unsigned count=0;count<64 && Serial.available();++count) {
    rover::LineParser::Result result = parser.feed(static_cast<char>(Serial.read()));
    if (result == rover::LineParser::Overflow) {
      controller.disarm(); applyOutputs(millis()); Serial.println("ERR line overflow; DISARMED");
    } else if (result == rover::LineParser::Ready) {
      bool accepted;
      portENTER_CRITICAL(&safetyMux);
      if (hardwareTrip) controller.emergency();
      accepted = controller.command(parser.line(),millis(),healthy() && pwmReady);
      if (accepted && !strcmp(parser.line(),"RESET")) hardwareTrip = false;
      portEXIT_CRITICAL(&safetyMux);
      applyOutputs(millis());
      Serial.printf("%s %s\n",accepted ? "OK" : "ERR",parser.line());
    }
  }
  // One ping every 65 ms; no 45/180 ms blocking delays. Serial stop latency
  // can still be up to one 25 ms pulseIn timeout plus loop/serial overhead.
  uint32_t now = millis();
  if (uint32_t(now-lastPing) >= 65) {
    lastPing = now;
    int cm = measure(sensorIndex);
    controller.sample(sensorIndex,cm,millis());
    sensorIndex = (sensorIndex+1)%3;
  }
  if (hardwareTrip) controller.emergency();
  controller.tick(millis(),healthy());
  applyOutputs(millis());
  now = millis();
  if (uint32_t(now-lastLog) >= 500 && Serial.availableForWrite() >= 100) {
    lastLog = now;
    char message[512];
    int length = rover::telemetry(message,sizeof(message),controller,now,appliedMotion,
      appliedEnable,appliedBrush,appliedConveyor,healthy());
    if (length > 0 && length < static_cast<int>(sizeof(message))) Serial.println(message);
    Serial.printf("DIST %d %d %d armed=%d auto=%d estop=%d motion=%d en=%d\n",
      controller.ranges[0].cm,controller.ranges[1].cm,controller.ranges[2].cm,
      controller.armed,controller.automatic,controller.estop,static_cast<int>(controller.motion),digitalRead(pins::ENABLE));
  }
}
