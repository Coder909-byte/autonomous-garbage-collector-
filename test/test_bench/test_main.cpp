#include <unity.h>
#include "../../firmware/rover.ino"
static_assert(!rover::MOTOR_CAPABLE,"Bench tests must use USB_BENCH_DIAGNOSTIC");

void setUp() {
  controller=rover::Controller(); parser=rover::LineParser(); gate=rover::MotionGate();
  hardwareTrip=false; pwmReady=true; lastPing=lastLog=0; sensorIndex=0;
  mockNow=0; mockPulse=5800; mockPwmFailure=false; mockHazard=false;
  mockEnableHighCount=mockMotorHighCount=mockNonzeroDutyCount=mockPwmSetupCount=mockPwmAttachCount=0;
  mockInterrupt=nullptr;
  std::fill(mockPins,mockPins+40,0); std::fill(mockDuty,mockDuty+4,0);
  Serial.input.clear(); Serial.output.clear();
  applyOutputs(0);
}
void tearDown() {}
void stopped() {
  TEST_ASSERT_FALSE(appliedEnable); TEST_ASSERT_FALSE(appliedBrush); TEST_ASSERT_FALSE(appliedConveyor);
  TEST_ASSERT_TRUE(appliedMotion==rover::Motion::Stop);
  TEST_ASSERT_EQUAL(LOW,mockPins[pins::ENABLE]);
  for (int p:pins::PWM) TEST_ASSERT_EQUAL(LOW,mockPins[p]);
  for (int p:pins::AUX) TEST_ASSERT_EQUAL(LOW,mockPins[p]);
  for (unsigned duty:mockDuty) TEST_ASSERT_EQUAL(0,duty);
  TEST_ASSERT_EQUAL(0,mockEnableHighCount); TEST_ASSERT_EQUAL(0,mockMotorHighCount);
  TEST_ASSERT_EQUAL(0,mockNonzeroDutyCount); TEST_ASSERT_EQUAL(0,mockPwmAttachCount); TEST_ASSERT_EQUAL(0,mockPwmSetupCount);
}
void send(const char *command) { Serial.input=std::string(command)+"\n"; loop(); stopped(); }
void bench_boot_disarmed_without_protection() {
  setup(); loop(); stopped();
  TEST_ASSERT_FALSE(controller.armed); TEST_ASSERT_FALSE(controller.estop);
  TEST_ASSERT_FALSE(healthy()); TEST_ASSERT_FALSE(hardwareTrip); TEST_ASSERT_NULL(mockInterrupt);
  TEST_ASSERT_EQUAL(INPUT_PULLDOWN,mockModes[pins::ESTOP_OK]);
  TEST_ASSERT_NOT_NULL(strstr(Serial.output.c_str(),"READY USB_BENCH_DIAGNOSTIC DISARMED; NO MOTOR POWER"));
  for (int p:pins::PWM) TEST_ASSERT_EQUAL(OUTPUT,mockModes[p]);
}
void bench_rejects_every_motor_command() {
  setup();
  for (const char *command:{"ARM","AUTO","F","B","L","R","BRUSH ON","CONVEYOR ON","CLEAN ON","FORWARD"}) {
    send(command); TEST_ASSERT_NOT_NULL(strstr(Serial.output.c_str(),(std::string("ERR ")+command+"\n").c_str()));
    mockNow+=200; loop(); stopped(); TEST_ASSERT_FALSE(controller.armed); TEST_ASSERT_FALSE(controller.automatic);
  }
}
void bench_software_estop_latches_until_reset() {
  setup(); send("ESTOP"); TEST_ASSERT_TRUE(controller.estop);
  for (const char *command:{"DISARM","S","MANUAL","ARM","AUTO","CLEAN OFF"}) {
    send(command); TEST_ASSERT_TRUE(controller.estop);
  }
  mockNow=10000; loop(); stopped(); TEST_ASSERT_TRUE(controller.estop);
  send("RESET"); TEST_ASSERT_FALSE(controller.estop); TEST_ASSERT_FALSE(controller.armed); TEST_ASSERT_FALSE(healthy());
  send("ARM"); TEST_ASSERT_FALSE(controller.armed);
}
void bench_stop_alias_latches() { setup(); send("STOP"); TEST_ASSERT_TRUE(controller.estop); send("RESET"); TEST_ASSERT_FALSE(controller.estop); }
void bench_gpio27_cannot_unlock_motors() {
  setup();
  for (int value:{HIGH,LOW,HIGH,LOW}) {
    mockPins[pins::ESTOP_OK]=value; send("RESET"); send("ARM"); send("F");
    TEST_ASSERT_EQUAL(value==HIGH,healthy()); TEST_ASSERT_FALSE(controller.armed);
  }
}
void bench_adapter_rejects_forced_controller_state() {
  setup();
  for (auto motion:{rover::Motion::Forward,rover::Motion::Backward,rover::Motion::Left,rover::Motion::Right}) {
    controller.armed=true; controller.motion=motion; controller.brushes=controller.conveyor=true;
    mockPins[pins::ESTOP_OK]=HIGH;
    applyOutputs(mockNow); mockNow+=1000; applyOutputs(mockNow); stopped();
    loop(); TEST_ASSERT_FALSE(controller.armed); stopped();
  }
}
void bench_pwm_helper_never_drives_high() { setup(); for (unsigned i=0;i<4;++i) pwmWrite(i,255); stopped(); }
void bench_usb_loss_and_rollover_keep_outputs_disabled() {
  setup(); send("ARM"); send("AUTO"); send("F");
  for (uint32_t now:{1200u,10000u,0xfffffff0u,20u}) { mockNow=now; loop(); stopped(); TEST_ASSERT_FALSE(controller.armed); }
}
void bench_sensors_and_tel_are_live_with_feedback_low() {
  setup();
  mockNow=65; mockPulse=6960; loop();
  mockNow=130; mockPulse=5800; loop();
  mockNow=195; mockPulse=4060; loop();
  mockNow=500; mockPulse=6960; loop(); stopped();
  TEST_ASSERT_EQUAL(120,controller.ranges[0].cm); TEST_ASSERT_EQUAL(100,controller.ranges[1].cm); TEST_ASSERT_EQUAL(70,controller.ranges[2].cm);
  const char *out=Serial.output.c_str();
  for (const char *field:{"TEL {\"v\":1","\"fw\":\"rover-usb-v1\"","\"healthy\":false","\"estop\":false","\"armed\":false","\"en\":false","\"mode\":\"USB_BENCH_DIAGNOSTIC\"","\"motorCapable\":false","\"cm\":[120,100,70]","\"age\":[0,370,305]"})
    TEST_ASSERT_NOT_NULL(strstr(out,field));
}
void bench_parser_overflow_cannot_arm() {
  setup(); Serial.input=std::string(70,'X')+"ARM\nF\n"; loop(); loop(); stopped();
  TEST_ASSERT_FALSE(controller.armed); TEST_ASSERT_NOT_NULL(strstr(Serial.output.c_str(),"ERR line overflow; DISARMED"));
}
void bench_telemetry_fits_buffer_at_maximum_ages() {
  setup(); char out[512];
  int n=rover::telemetry(out,sizeof(out),controller,0xffffffffu,appliedMotion,appliedEnable,appliedBrush,appliedConveyor,healthy());
  TEST_ASSERT_TRUE(n>0 && n<512); TEST_ASSERT_NOT_NULL(strstr(out,"\"age\":[4294967295,4294967295,4294967295]"));
}
int main() {
  UNITY_BEGIN();
  RUN_TEST(bench_boot_disarmed_without_protection); RUN_TEST(bench_rejects_every_motor_command);
  RUN_TEST(bench_software_estop_latches_until_reset); RUN_TEST(bench_stop_alias_latches);
  RUN_TEST(bench_gpio27_cannot_unlock_motors); RUN_TEST(bench_adapter_rejects_forced_controller_state);
  RUN_TEST(bench_pwm_helper_never_drives_high); RUN_TEST(bench_usb_loss_and_rollover_keep_outputs_disabled);
  RUN_TEST(bench_sensors_and_tel_are_live_with_feedback_low); RUN_TEST(bench_parser_overflow_cannot_arm);
  RUN_TEST(bench_telemetry_fits_buffer_at_maximum_ages);
  return UNITY_END();
}
