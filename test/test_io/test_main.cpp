#include <unity.h>
#include "../../firmware/rover.ino"
void setUp() {
  controller=rover::Controller(); parser=rover::LineParser(); gate=rover::MotionGate();
  hardwareTrip=false; pwmReady=true; lastPing=lastLog=0; sensorIndex=0;
  mockNow=0; mockPwmFailure=false; mockHazard=false; mockPulse=5800; mockEnableHighCount=0;
  std::fill(mockPins,mockPins+40,0); std::fill(mockDuty,mockDuty+4,0);
  mockPins[pins::ESTOP_OK]=HIGH; Serial.input.clear();
  applyOutputs(0); // also reset adapter's previous output state
}
void tearDown() {}
void stopped() {
  TEST_ASSERT_EQUAL(0,mockPins[pins::ENABLE]);
  for (unsigned d:mockDuty) TEST_ASSERT_EQUAL(0,d);
  for (int p:pins::AUX) TEST_ASSERT_EQUAL(0,mockPins[p]);
}
void send(const char *s) { Serial.input=s; loop(); }
void startForward() { setup(); send("ARM\nF\n"); mockNow=100; loop(); TEST_ASSERT_EQUAL(1,mockPins[pins::ENABLE]); }
void boot_outputs_disabled() { setup(); loop(); stopped(); TEST_ASSERT_EQUAL(0,mockEnableHighCount); }
void open_loop_at_boot_latches() { mockPins[pins::ESTOP_OK]=LOW; setup(); send("ARM\n"); stopped(); TEST_ASSERT_TRUE(controller.estop); }
void arm_no_pulse() { setup(); send("ARM\n"); stopped(); TEST_ASSERT_EQUAL(0,mockEnableHighCount); }
void forward_after_neutral() { setup(); send("ARM\nF\n"); stopped(); mockNow=99; loop(); stopped(); mockNow=100; loop(); TEST_ASSERT_EQUAL(1,mockPins[14]); TEST_ASSERT_EQUAL(150,mockDuty[0]); TEST_ASSERT_EQUAL(150,mockDuty[2]); TEST_ASSERT_EQUAL(0,mockDuty[1]); TEST_ASSERT_EQUAL(0,mockDuty[3]); }
void reverse_break_before_make() { startForward(); send("B\n"); stopped(); mockNow+=100; loop(); TEST_ASSERT_EQUAL(150,mockDuty[1]); TEST_ASSERT_EQUAL(150,mockDuty[3]); TEST_ASSERT_FALSE(mockHazard); }
void physical_isr_immediately_cuts_enable() { startForward(); TEST_ASSERT_NOT_NULL(mockInterrupt); mockPins[pins::ESTOP_OK]=LOW; mockInterrupt(); TEST_ASSERT_EQUAL(0,mockPins[14]); loop(); stopped(); TEST_ASSERT_TRUE(controller.estop); }
void release_requires_reset_and_rearm() { startForward(); mockPins[pins::ESTOP_OK]=LOW; mockInterrupt(); loop(); mockPins[pins::ESTOP_OK]=HIGH; send("ARM\nF\n"); stopped(); send("RESET\n"); stopped(); TEST_ASSERT_FALSE(controller.armed); send("ARM\nF\n"); mockNow+=100; loop(); TEST_ASSERT_EQUAL(1,mockPins[14]); }
void serial_estop_all_outputs() { startForward(); send("CLEAN ON\n"); TEST_ASSERT_EQUAL(1,mockPins[pins::BRUSH_IN1]); send("ESTOP\n"); stopped(); TEST_ASSERT_FALSE(controller.armed); }
void deadman_cuts_actual_enable() { startForward(); mockNow=1200; loop(); stopped(); }
void overflow_disarms_actual_outputs() { startForward(); Serial.input=std::string(70,'X')+"ARM\n"; loop(); stopped(); loop(); stopped(); TEST_ASSERT_FALSE(controller.armed); }
void pwm_failure_blocks_arming() { mockPwmFailure=true; setup(); send("ARM\nF\n"); mockNow=100; loop(); stopped(); TEST_ASSERT_FALSE(controller.armed); }
void timeout_disarms_auto_outputs() {
 setup(); for(unsigned i=0;i<3;++i) controller.sample(i,100,0);
 send("ARM\nAUTO\n"); mockNow=100; loop(); TEST_ASSERT_EQUAL(1,mockPins[14]);
 mockPulse=0; mockNow=165; loop(); stopped(); TEST_ASSERT_FALSE(controller.armed);
}
void one_l298n_independent_outputs() {
 startForward(); send("BRUSH ON\n");
 TEST_ASSERT_EQUAL(1,mockPins[pins::BRUSH_IN1]); TEST_ASSERT_EQUAL(0,mockPins[pins::BRUSH_IN2]); TEST_ASSERT_EQUAL(0,mockPins[pins::CONVEYOR_IN3]);
 send("CONVEYOR ON\nBRUSH OFF\n");
 TEST_ASSERT_EQUAL(0,mockPins[pins::BRUSH_IN1]); TEST_ASSERT_EQUAL(1,mockPins[pins::CONVEYOR_IN3]); TEST_ASSERT_EQUAL(0,mockPins[pins::CONVEYOR_IN4]);
 send("CONVEYOR OFF\n"); TEST_ASSERT_EQUAL(0,mockPins[pins::CONVEYOR_IN3]); TEST_ASSERT_EQUAL(1,mockPins[pins::ENABLE]);
}
void aux_suppressed_during_neutral_and_turns() {
 setup(); send("ARM\nCLEAN ON\nF\n"); stopped(); mockNow=100; loop();
 TEST_ASSERT_EQUAL(1,mockPins[pins::BRUSH_IN1]); TEST_ASSERT_EQUAL(1,mockPins[pins::CONVEYOR_IN3]);
 send("L\n"); stopped(); mockNow+=100; loop(); TEST_ASSERT_EQUAL(0,mockPins[pins::BRUSH_IN1]); TEST_ASSERT_EQUAL(0,mockPins[pins::CONVEYOR_IN3]);
 TEST_ASSERT_EQUAL(140,mockDuty[1]); TEST_ASSERT_EQUAL(140,mockDuty[2]); TEST_ASSERT_FALSE(mockHazard);
}
void right_turn_wheel_outputs() { startForward(); send("R\n"); stopped(); mockNow+=100; loop(); TEST_ASSERT_EQUAL(140,mockDuty[0]); TEST_ASSERT_EQUAL(140,mockDuty[3]); TEST_ASSERT_EQUAL(0,mockDuty[1]); TEST_ASSERT_EQUAL(0,mockDuty[2]); TEST_ASSERT_FALSE(mockHazard); }
void estop_input_has_internal_pulldown() { setup(); TEST_ASSERT_EQUAL(INPUT_PULLDOWN,mockModes[pins::ESTOP_OK]); TEST_ASSERT_EQUAL(27,pins::ESTOP_OK); }
void stop_disables_both_aux_channels() { startForward(); send("BRUSH ON\nCONVEYOR ON\nSTOP\n"); stopped(); TEST_ASSERT_TRUE(controller.estop); TEST_ASSERT_FALSE(controller.brushes); TEST_ASSERT_FALSE(controller.conveyor); }
void aux_channel_topology() { TEST_ASSERT_EQUAL(4,sizeof(pins::AUX)/sizeof(pins::AUX[0])); TEST_ASSERT_EQUAL(21,pins::BRUSH_IN1); TEST_ASSERT_EQUAL(22,pins::BRUSH_IN2); TEST_ASSERT_EQUAL(23,pins::CONVEYOR_IN3); TEST_ASSERT_EQUAL(25,pins::CONVEYOR_IN4); }
void autoStep(uint32_t at,int front=20) {
 mockNow=at; controller.sample(0,front,at); controller.sample(1,100,at); controller.sample(2,60,at);
 controller.tick(at,true); applyOutputs(at);
}
void startAutoTurn() {
 setup(); controller.sample(0,20,0); controller.sample(1,100,0); controller.sample(2,60,0);
 controller.command("ARM",0,true); controller.command("AUTO",0,true); autoStep(0); autoStep(180);
}
void adapter_times_turn_from_enable() {
 startAutoTurn(); stopped(); TEST_ASSERT_TRUE(controller.navigation()==rover::NavPhase::TurnPending);
 autoStep(279); stopped(); autoStep(280); TEST_ASSERT_EQUAL(1,mockPins[pins::ENABLE]);
 TEST_ASSERT_TRUE(controller.navigation()==rover::NavPhase::Turning); TEST_ASSERT_EQUAL(140,mockDuty[1]);
 autoStep(819); TEST_ASSERT_EQUAL(1,mockPins[pins::ENABLE]); autoStep(820); stopped();
 TEST_ASSERT_TRUE(controller.navigation()==rover::NavPhase::Reassess); TEST_ASSERT_FALSE(mockHazard);
}
void physical_estop_interrupts_auto_turn() {
 startAutoTurn(); autoStep(280); TEST_ASSERT_EQUAL(1,mockPins[pins::ENABLE]);
 mockPins[pins::ESTOP_OK]=LOW; mockInterrupt(); TEST_ASSERT_EQUAL(0,mockPins[pins::ENABLE]);
 loop(); stopped(); TEST_ASSERT_TRUE(controller.estop);
 mockPins[pins::ESTOP_OK]=HIGH; send("ARM\nAUTO\n"); stopped(); TEST_ASSERT_FALSE(controller.armed);
}
void reassessment_sensor_failure_keeps_adapter_disabled() {
 startAutoTurn(); autoStep(280); autoStep(820); stopped();
 controller.sample(1,-1,821); controller.tick(821,true); applyOutputs(821); stopped();
 TEST_ASSERT_FALSE(controller.armed); TEST_ASSERT_TRUE(controller.navigation()==rover::NavPhase::SensorFault);
}
int main() {
 UNITY_BEGIN();
 RUN_TEST(adapter_times_turn_from_enable); RUN_TEST(physical_estop_interrupts_auto_turn);
 RUN_TEST(reassessment_sensor_failure_keeps_adapter_disabled);
 RUN_TEST(one_l298n_independent_outputs); RUN_TEST(aux_suppressed_during_neutral_and_turns);
 RUN_TEST(right_turn_wheel_outputs); RUN_TEST(estop_input_has_internal_pulldown);
 RUN_TEST(stop_disables_both_aux_channels); RUN_TEST(aux_channel_topology); RUN_TEST(boot_outputs_disabled); RUN_TEST(open_loop_at_boot_latches);
 RUN_TEST(arm_no_pulse); RUN_TEST(forward_after_neutral); RUN_TEST(reverse_break_before_make);
 RUN_TEST(physical_isr_immediately_cuts_enable); RUN_TEST(release_requires_reset_and_rearm);
 RUN_TEST(serial_estop_all_outputs); RUN_TEST(deadman_cuts_actual_enable);
 RUN_TEST(overflow_disarms_actual_outputs); RUN_TEST(pwm_failure_blocks_arming); RUN_TEST(timeout_disarms_auto_outputs);
 return UNITY_END();
}
