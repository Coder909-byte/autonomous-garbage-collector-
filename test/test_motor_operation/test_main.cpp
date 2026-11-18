#include <unity.h>
#include "../../firmware/rover.ino"
static_assert(rover::MOTOR_OPERATION_MODE,"Select MOTOR_OPERATION for this suite");
static_assert(!rover::PHYSICAL_FEEDBACK_REQUIRED,"This mode must not require GPIO27");

void setUp() {
  controller=rover::Controller(); parser=rover::LineParser(); gate=rover::MotionGate();
  hardwareTrip=false; pwmReady=true; lastPing=lastLog=lastMotorCommand=0; sensorIndex=0; motorCommandTimeout=false;
  mockNow=0; mockPulse=5800; mockPwmFailure=false; mockHazard=false; mockInterrupt=nullptr;
  mockEnableHighCount=mockMotorHighCount=mockNonzeroDutyCount=mockPwmSetupCount=mockPwmAttachCount=0;
  std::fill(mockPins,mockPins+40,0); std::fill(mockModes,mockModes+40,0); std::fill(mockDuty,mockDuty+4,0);
  Serial.input.clear(); Serial.output.clear(); mockMotorEvents.clear(); applyOutputs(0); mockMotorEvents.clear();
}
void tearDown() {}
void stopped() {
  TEST_ASSERT_EQUAL(LOW,mockPins[pins::ENABLE]);
  for (unsigned duty:mockDuty) TEST_ASSERT_EQUAL(0,duty);
  for (int p:pins::AUX) TEST_ASSERT_EQUAL(LOW,mockPins[p]);
  TEST_ASSERT_FALSE(appliedEnable); TEST_ASSERT_FALSE(appliedBrush); TEST_ASSERT_FALSE(appliedConveyor);
}
void send(const char *command) { Serial.input=std::string(command)+"\n"; loop(); }
void sampleAll(int front=100,int left=100,int right=70) {
  controller.sample(0,front,mockNow);controller.sample(1,left,mockNow);controller.sample(2,right,mockNow);
}
void step(uint32_t now) { mockNow=now;sampleAll();loop(); }
void fixed_gpio_map() {
  const int actual[]={pins::L_FWD,pins::L_REV,pins::R_FWD,pins::R_REV,pins::BRUSH_IN1,pins::BRUSH_IN2,pins::CONVEYOR_IN3,pins::CONVEYOR_IN4,pins::ENABLE,pins::ESTOP_OK,pins::TF,pins::EF,pins::TL,pins::EL,pins::TR,pins::ER};
  const int expected[]={16,17,18,19,21,22,23,25,14,27,32,34,33,35,13,36};
  TEST_ASSERT_EQUAL_INT_ARRAY(expected,actual,16);
}
void commissioning_requires_all_six_conditions_and_record() {
  for (unsigned mask=0;mask<64;++mask) {
    const rover::Commissioning c={bool(mask&1),bool(mask&2),bool(mask&4),bool(mask&8),bool(mask&16),bool(mask&32),"HOST EVIDENCE"};
    TEST_ASSERT_EQUAL(mask==63,c.ready());
  }
  const rover::Commissioning noRecord={true,true,true,true,true,true,""};TEST_ASSERT_FALSE(noRecord.ready());
}
void boot_disarmed_with_real_gpio27_low() {
  setup();loop();stopped();TEST_ASSERT_FALSE(controller.armed);TEST_ASSERT_FALSE(controller.estop);
  TEST_ASSERT_FALSE(healthy());TEST_ASSERT_NULL(mockInterrupt);TEST_ASSERT_EQUAL(INPUT_PULLDOWN,mockModes[27]);
  TEST_ASSERT_EQUAL(4,mockPwmSetupCount);TEST_ASSERT_EQUAL(4,mockPwmAttachCount);TEST_ASSERT_EQUAL(0,mockEnableHighCount);
  TEST_ASSERT_NOT_NULL(strstr(Serial.output.c_str(),"READY MOTOR_OPERATION DISARMED"));
}
void software_stop_latches_with_gpio27_low() {
  setup();send("ESTOP");TEST_ASSERT_TRUE(controller.estop);stopped();
  for (const char *c:{"S","DISARM","MANUAL","CLEAN OFF"}){send(c);TEST_ASSERT_TRUE(controller.estop);stopped();}
  send("RESET");TEST_ASSERT_FALSE(controller.estop);TEST_ASSERT_FALSE(controller.armed);TEST_ASSERT_FALSE(healthy());stopped();
  send("STOP");TEST_ASSERT_TRUE(controller.estop);stopped();
}
void sensor_polling_and_compatible_tel() {
  setup();mockNow=65;mockPulse=6960;loop();mockNow=130;mockPulse=5800;loop();mockNow=195;mockPulse=4060;loop();mockNow=500;mockPulse=6960;loop();
  for (const char *field:{"TEL {\"v\":1","\"fw\":\"rover-usb-v1\"","\"healthy\":false","\"cm\":[120,100,70]","\"mode\":\"MOTOR_OPERATION\"","\"motorCapable\":true","\"commissioningReady\":"})
    TEST_ASSERT_NOT_NULL(strstr(Serial.output.c_str(),field));
  stopped();
}
void telemetry_fits_with_maximum_ages_and_inhibit() {
  setup();char message[512];for (unsigned i=0;i<3;++i)controller.sample(i,400,0);
  int n=rover::telemetry(message,sizeof(message),controller,0xffffffffu,appliedMotion,appliedEnable,appliedBrush,appliedConveyor,healthy(),motorInhibit());
  TEST_ASSERT_TRUE(n>0 && n<512);TEST_ASSERT_NOT_NULL(strstr(message,"\"age\":[4294967295,4294967295,4294967295]"));
}

#if defined(ROVER_COMMISSIONING_TEST_FIXTURE)
void forward() { setup();send("ARM");stopped();send("F");stopped();step(mockNow+100);TEST_ASSERT_TRUE(appliedEnable); }
void all_direction_pwm_and_neutral_intervals() {
  setup();send("ARM");
  const char *commands[]={"F","B","L","R"};const unsigned duties[][4]={{150,0,150,0},{0,150,0,150},{0,140,140,0},{140,0,0,140}};
  for (unsigned i=0;i<4;++i){send(commands[i]);stopped();step(mockNow+99);stopped();step(mockNow+1);
    TEST_ASSERT_EQUAL_UINT_ARRAY(duties[i],mockDuty,4);TEST_ASSERT_TRUE(appliedEnable);TEST_ASSERT_FALSE(healthy());}
  TEST_ASSERT_FALSE(mockHazard);
}
void pwm_is_prepared_with_enable_low_then_enable_asserted() {
  forward();bool nonzero=false,enabled=false;
  for (const auto &e:mockMotorEvents){
    if(e.pwm&&e.value){TEST_ASSERT_FALSE(e.enabled);nonzero=true;}
    if(!e.pwm&&e.output==14&&e.value){TEST_ASSERT_TRUE(nonzero);enabled=true;}
  }
  TEST_ASSERT_TRUE(enabled);send("B");stopped();step(mockNow+100);TEST_ASSERT_FALSE(mockHazard);
}
void normal_stop_disarm_and_rearm() {
  forward();send("S");stopped();TEST_ASSERT_TRUE(controller.armed);TEST_ASSERT_FALSE(controller.estop);
  send("F");step(mockNow+100);TEST_ASSERT_TRUE(appliedEnable);send("DISARM");stopped();TEST_ASSERT_FALSE(controller.armed);
  send("F");stopped();send("ARM");stopped();
}
void independent_cleaning_and_forward_gating() {
  forward();send("BRUSH ON");TEST_ASSERT_TRUE(appliedBrush);TEST_ASSERT_FALSE(appliedConveyor);
  send("CONVEYOR ON");send("BRUSH OFF");TEST_ASSERT_FALSE(appliedBrush);TEST_ASSERT_TRUE(appliedConveyor);
  send("BRUSH ON");send("L");stopped();step(mockNow+100);TEST_ASSERT_FALSE(appliedBrush);TEST_ASSERT_FALSE(appliedConveyor);
  send("F");step(mockNow+100);TEST_ASSERT_TRUE(appliedBrush);TEST_ASSERT_TRUE(appliedConveyor);
  TEST_ASSERT_EQUAL(LOW,mockPins[22]);TEST_ASSERT_EQUAL(LOW,mockPins[25]);send("CLEAN OFF");TEST_ASSERT_FALSE(appliedBrush);TEST_ASSERT_FALSE(appliedConveyor);
}
void estop_disables_wheels_and_cleaning_until_reset_and_arm() {
  forward();send("CLEAN ON");send("ESTOP");stopped();TEST_ASSERT_TRUE(controller.estop);
  send("ARM");send("F");stopped();send("RESET");stopped();TEST_ASSERT_FALSE(controller.armed);
  send("ARM");send("F");step(mockNow+100);TEST_ASSERT_TRUE(appliedEnable);TEST_ASSERT_FALSE(appliedBrush);TEST_ASSERT_FALSE(appliedConveyor);
}
void command_silence_disarms_manual_and_clears_cleaning() {
  forward();send("CLEAN ON");step(lastMotorCommand+1200);stopped();TEST_ASSERT_FALSE(controller.armed);
  TEST_ASSERT_EQUAL_STRING("COMMAND_TIMEOUT",motorInhibit());send("HEARTBEAT");stopped();TEST_ASSERT_FALSE(controller.armed);
}
void invalid_commands_do_not_renew_the_motor_lease() {
  forward();const uint32_t last=lastMotorCommand;mockNow=last+1100;send("BOGUS");TEST_ASSERT_EQUAL(last,lastMotorCommand);
  step(last+1200);stopped();TEST_ASSERT_FALSE(controller.armed);
}
void heartbeat_keeps_auto_live_but_loss_still_disarms() {
  setup();sampleAll();send("ARM");send("AUTO");step(100);TEST_ASSERT_TRUE(appliedEnable);
  for (uint32_t now=200;now<=1400;now+=200){mockNow=now;sampleAll();send("HEARTBEAT");TEST_ASSERT_TRUE(appliedEnable);}
  step(lastMotorCommand+1200);stopped();TEST_ASSERT_FALSE(controller.armed);TEST_ASSERT_FALSE(controller.automatic);
  send("HEARTBEAT");stopped();TEST_ASSERT_FALSE(controller.armed);
}
void unchanged_auto_avoidance_reaches_applied_turn() {
  setup();sampleAll(20,100,60);mockPulse=1160;send("ARM");send("AUTO");
  for(uint32_t now:{180u,280u}){mockNow=now;sampleAll(20,100,60);controller.tick(now,controllerHealthy());applyOutputs(now);}
  TEST_ASSERT_TRUE(controller.navigation()==rover::NavPhase::Turning);TEST_ASSERT_EQUAL(140,mockDuty[1]);TEST_ASSERT_EQUAL(140,mockDuty[2]);TEST_ASSERT_TRUE(appliedEnable);
  mockNow=820;sampleAll(20,100,60);controller.tick(mockNow,controllerHealthy());applyOutputs(mockNow);stopped();TEST_ASSERT_TRUE(controller.navigation()==rover::NavPhase::Reassess);
}
void stale_sensor_disarms_auto() {
  setup();sampleAll();send("ARM");send("AUTO");step(100);controller.sample(1,-1,mockNow);loop();stopped();TEST_ASSERT_FALSE(controller.armed);
}
void pwm_failure_cannot_be_ignored_with_gpio27_high() {
  mockPwmFailure=true;mockPins[27]=HIGH;setup();send("ARM");send("F");step(100);stopped();TEST_ASSERT_FALSE(controller.armed);TEST_ASSERT_EQUAL_STRING("PWM_FAULT",motorInhibit());
}
void command_timeout_handles_millis_rollover() {
  setup();mockNow=0xffffff00u;send("ARM");send("F");step(0xffffff64u);TEST_ASSERT_TRUE(appliedEnable);
  step(0x100u);TEST_ASSERT_TRUE(appliedEnable);step(0x500u);stopped();TEST_ASSERT_FALSE(controller.armed);
}
void serial_overflow_disarms_applied_outputs() {
  forward();Serial.input=std::string(70,'X')+"ARM\n";loop();loop();stopped();TEST_ASSERT_FALSE(controller.armed);
}
#else
void pending_commissioning_rejects_all_motor_commands() {
  setup();for(const char *c:{"ARM","AUTO","F","B","L","R","CLEAN ON","BRUSH ON","CONVEYOR ON"}){send(c);stopped();TEST_ASSERT_FALSE(controller.armed);}
  TEST_ASSERT_EQUAL(0,mockEnableHighCount);TEST_ASSERT_EQUAL(0,mockNonzeroDutyCount);TEST_ASSERT_EQUAL_STRING("COMMISSIONING_REQUIRED",motorInhibit());
}
void gpio27_high_cannot_substitute_for_commissioning() {
  setup();mockPins[27]=HIGH;send("ARM");send("F");step(100);stopped();TEST_ASSERT_TRUE(healthy());TEST_ASSERT_FALSE(controller.armed);
}
void pending_adapter_and_pwm_reject_forced_requests() {
  setup();controller.armed=true;controller.motion=rover::Motion::Forward;controller.brushes=controller.conveyor=true;
  applyOutputs(0);applyOutputs(100);stopped();for(unsigned i=0;i<4;++i)pwmWrite(i,255);stopped();
  TEST_ASSERT_EQUAL(0,mockNonzeroDutyCount);TEST_ASSERT_EQUAL(0,mockEnableHighCount);
}
void heartbeat_and_reset_do_not_satisfy_commissioning() {
  setup();send("HEARTBEAT");send("RESET");send("ARM");stopped();TEST_ASSERT_FALSE(controller.armed);TEST_ASSERT_FALSE(rover::COMMISSIONING_READY);
}
#endif
int main() {
  UNITY_BEGIN();RUN_TEST(fixed_gpio_map);RUN_TEST(commissioning_requires_all_six_conditions_and_record);
  RUN_TEST(boot_disarmed_with_real_gpio27_low);RUN_TEST(software_stop_latches_with_gpio27_low);
  RUN_TEST(sensor_polling_and_compatible_tel);RUN_TEST(telemetry_fits_with_maximum_ages_and_inhibit);
#if defined(ROVER_COMMISSIONING_TEST_FIXTURE)
  RUN_TEST(all_direction_pwm_and_neutral_intervals);RUN_TEST(pwm_is_prepared_with_enable_low_then_enable_asserted);
  RUN_TEST(normal_stop_disarm_and_rearm);RUN_TEST(independent_cleaning_and_forward_gating);
  RUN_TEST(estop_disables_wheels_and_cleaning_until_reset_and_arm);RUN_TEST(command_silence_disarms_manual_and_clears_cleaning);
  RUN_TEST(invalid_commands_do_not_renew_the_motor_lease);RUN_TEST(heartbeat_keeps_auto_live_but_loss_still_disarms);
  RUN_TEST(unchanged_auto_avoidance_reaches_applied_turn);RUN_TEST(stale_sensor_disarms_auto);
  RUN_TEST(pwm_failure_cannot_be_ignored_with_gpio27_high);RUN_TEST(command_timeout_handles_millis_rollover);
  RUN_TEST(serial_overflow_disarms_applied_outputs);
#else
  RUN_TEST(pending_commissioning_rejects_all_motor_commands);RUN_TEST(gpio27_high_cannot_substitute_for_commissioning);
  RUN_TEST(pending_adapter_and_pwm_reject_forced_requests);RUN_TEST(heartbeat_and_reset_do_not_satisfy_commissioning);
#endif
  return UNITY_END();
}
