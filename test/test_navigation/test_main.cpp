#include <initializer_list>
#include <unity.h>
#include "rover_control.h"
using namespace rover;
void setUp() {}
void tearDown() {}
void ranges(Controller &c,uint32_t t,int f=100,int l=100,int r=100) {
  c.sample(0,f,t); c.sample(1,l,t); c.sample(2,r,t);
}
void autoStart(Controller &c,uint32_t t=0,int f=100,int l=100,int r=100) {
  ranges(c,t,f,l,r); TEST_ASSERT_TRUE(c.command("ARM",t,true));
  TEST_ASSERT_TRUE(c.command("AUTO",t,true)); c.tick(t,true);
}
void boot_safe() { Controller c; c.tick(0,true); TEST_ASSERT_FALSE(c.armed); TEST_ASSERT_TRUE(c.motion==Motion::Stop); TEST_ASSERT_FALSE(c.cleanOutput()); }
void arm_stays_stopped() { Controller c; c.command("ARM",0,true); c.tick(100,true); TEST_ASSERT_TRUE(c.armed); TEST_ASSERT_TRUE(c.motion==Motion::Stop); }
void auto_requires_arm_and_ranges() { Controller c; TEST_ASSERT_FALSE(c.command("AUTO",0,true)); c.command("ARM",0,true); TEST_ASSERT_FALSE(c.command("AUTO",0,true)); TEST_ASSERT_TRUE(c.motion==Motion::Stop); }
void clear_forward() { Controller c; autoStart(c); TEST_ASSERT_TRUE(c.motion==Motion::Forward); TEST_ASSERT_FALSE(c.cleanOutput()); }
void obstacle_settles_then_left() { Controller c; autoStart(c,0,35,100,60); TEST_ASSERT_TRUE(c.motion==Motion::Stop); c.tick(179,true); TEST_ASSERT_TRUE(c.motion==Motion::Stop); c.tick(180,true); TEST_ASSERT_TRUE(c.motion==Motion::Left); }
void clearer_right() { Controller c; autoStart(c,0,20,50,120); c.tick(180,true); TEST_ASSERT_TRUE(c.motion==Motion::Right); }
void ties_left() { Controller c; autoStart(c,0,20,100,100); c.tick(180,true); TEST_ASSERT_TRUE(c.motion==Motion::Left); }
void all_blocked() { Controller c; autoStart(c,0,20,45,45); for (uint32_t t=0;t<2000;t+=100) { ranges(c,t,20,45,45); c.tick(t,true); TEST_ASSERT_TRUE(c.motion==Motion::Stop); } }
void side_too_close() { Controller c; autoStart(c,0,100,20,100); c.tick(180,true); TEST_ASSERT_TRUE(c.motion==Motion::Stop); }
void turn_stops_on_side_obstacle() { Controller c; autoStart(c,0,20,100,60); c.tick(180,true); ranges(c,200,20,45,60); c.tick(200,true); TEST_ASSERT_TRUE(c.motion==Motion::Stop); }
void turn_time_bounded() { Controller c; autoStart(c,0,20,100,60); c.tick(180,true); c.reportApplied(Motion::Left,280); ranges(c,819,20,100,60); c.tick(819,true); TEST_ASSERT_TRUE(c.motion==Motion::Left); c.tick(820,true); TEST_ASSERT_TRUE(c.motion==Motion::Stop); }
void missing_disarms_no_restart() { Controller c; autoStart(c); c.sample(1,-1,100); c.tick(100,true); TEST_ASSERT_FALSE(c.armed); ranges(c,150); c.tick(150,true); TEST_ASSERT_TRUE(c.motion==Motion::Stop); }
void out_of_range() { for (int cm : {0,1,401}) { Controller c; ranges(c,0,cm); c.command("ARM",0,true); TEST_ASSERT_FALSE(c.command("AUTO",0,true)); } }
void stale_individual_sensor() { Controller c; autoStart(c); c.sample(0,100,501); c.sample(1,100,501); c.tick(501,true); TEST_ASSERT_FALSE(c.armed); }
void freshness_boundary() { Controller c; autoStart(c); c.tick(500,true); TEST_ASSERT_TRUE(c.armed); c.tick(501,true); TEST_ASSERT_FALSE(c.armed); }
void manual_deadman() { Controller c; c.command("ARM",0,true); c.command("F",0,true); c.tick(1199,true); TEST_ASSERT_TRUE(c.motion==Motion::Forward); c.tick(1200,true); TEST_ASSERT_TRUE(c.motion==Motion::Stop); }
void unknown_does_not_refresh() { Controller c; c.command("ARM",0,true); c.command("F",0,true); TEST_ASSERT_FALSE(c.command("BOGUS",1199,true)); c.tick(1200,true); TEST_ASSERT_TRUE(c.motion==Motion::Stop); }
void repeat_manual_refreshes() { Controller c; c.command("ARM",0,true); c.command("B",0,true); c.command("B",1100,true); c.tick(1200,true); TEST_ASSERT_TRUE(c.motion==Motion::Backward); }
void manual_rollover() { Controller c; uint32_t t=UINT32_MAX-500; c.command("ARM",t,true); c.command("F",t,true); c.tick(t+1199,true); TEST_ASSERT_TRUE(c.motion==Motion::Forward); c.tick(t+1200,true); TEST_ASSERT_TRUE(c.motion==Motion::Stop); }
void turn_rollover() { Controller c; uint32_t t=UINT32_MAX-200; autoStart(c,t,20,100,60); c.tick(t+180,true); TEST_ASSERT_TRUE(c.motion==Motion::Left); c.reportApplied(Motion::Left,t+280); ranges(c,t+819,20,100,60); c.tick(t+819,true); TEST_ASSERT_TRUE(c.motion==Motion::Left); c.tick(t+820,true); TEST_ASSERT_TRUE(c.motion==Motion::Stop); }
void estop_latches() { Controller c; autoStart(c); c.command("ESTOP",0,true); TEST_ASSERT_FALSE(c.armed); TEST_ASSERT_TRUE(c.estop); TEST_ASSERT_FALSE(c.command("ARM",1,true)); TEST_ASSERT_TRUE(c.command("RESET",2,true)); TEST_ASSERT_FALSE(c.armed); TEST_ASSERT_TRUE(c.command("ARM",3,true)); }
void switch_open_cannot_reset() { Controller c; c.tick(0,false); TEST_ASSERT_TRUE(c.estop); TEST_ASSERT_FALSE(c.command("RESET",1,false)); TEST_ASSERT_FALSE(c.command("ARM",1,false)); c.tick(2,true); TEST_ASSERT_TRUE(c.estop); }
void hardware_stop_from_manual() { Controller c; c.command("ARM",0,true); c.command("B",0,true); c.tick(1,false); TEST_ASSERT_TRUE(c.motion==Motion::Stop); TEST_ASSERT_TRUE(c.estop); }
void s_exits_auto() { Controller c; autoStart(c); c.command("S",1,true); c.tick(2,true); TEST_ASSERT_FALSE(c.automatic); TEST_ASSERT_TRUE(c.motion==Motion::Stop); }
void mode_clears_turn() { Controller c; autoStart(c,0,20,100,60); c.tick(180,true); c.command("MANUAL",181,true); ranges(c,182); c.command("AUTO",182,true); c.tick(182,true); TEST_ASSERT_TRUE(c.motion==Motion::Forward); }
void arm_clears_modes() { Controller c; autoStart(c); c.command("CLEAN ON",0,true); c.command("ARM",1,true); TEST_ASSERT_FALSE(c.automatic); TEST_ASSERT_FALSE(c.brushes); TEST_ASSERT_FALSE(c.conveyor); TEST_ASSERT_TRUE(c.motion==Motion::Stop); }
void cleaning_forward_only() { Controller c; c.command("ARM",0,true); c.command("CLEAN ON",0,true); c.command("F",0,true); TEST_ASSERT_TRUE(c.cleanOutput()); for (const char *cmd : {"B","L","R","S"}) { c.command(cmd,1,true); TEST_ASSERT_FALSE(c.cleanOutput()); } }
void clean_off_and_disarm() { Controller c; autoStart(c); c.command("CLEAN ON",0,true); TEST_ASSERT_TRUE(c.cleanOutput()); c.command("CLEAN OFF",1,true); TEST_ASSERT_FALSE(c.cleanOutput()); c.command("DISARM",2,true); TEST_ASSERT_FALSE(c.armed); }
void parser_normalization() { LineParser p; for (char ch : {' ','a','r','m',' ','\r'}) { auto r=p.feed(ch); if (ch=='\r') { TEST_ASSERT_EQUAL(LineParser::Ready,r); TEST_ASSERT_EQUAL_STRING("ARM",p.line()); } } TEST_ASSERT_EQUAL(LineParser::None,p.feed('\n')); }
void parser_overflow_discards() { LineParser p; for(int i=0;i<48;++i) TEST_ASSERT_EQUAL(LineParser::None,p.feed(' ')); TEST_ASSERT_EQUAL(LineParser::Overflow,p.feed('A')); for(char ch : {'R','M','\n'}) TEST_ASSERT_EQUAL(LineParser::None,p.feed(ch)); p.feed('S'); TEST_ASSERT_EQUAL(LineParser::Ready,p.feed('\n')); TEST_ASSERT_EQUAL_STRING("S",p.line()); }
void gate_neutral_and_reverse() { MotionGate g; TEST_ASSERT_TRUE(g.update(Motion::Forward,0)==Motion::Stop); TEST_ASSERT_TRUE(g.update(Motion::Forward,99)==Motion::Stop); TEST_ASSERT_TRUE(g.update(Motion::Forward,100)==Motion::Forward); TEST_ASSERT_TRUE(g.update(Motion::Backward,101)==Motion::Stop); TEST_ASSERT_TRUE(g.update(Motion::Backward,201)==Motion::Backward); TEST_ASSERT_TRUE(g.update(Motion::Stop,202)==Motion::Stop); }
void gate_rollover() { MotionGate g; uint32_t t=UINT32_MAX-50; g.update(Motion::Left,t); TEST_ASSERT_TRUE(g.update(Motion::Left,t+99)==Motion::Stop); TEST_ASSERT_TRUE(g.update(Motion::Left,t+100)==Motion::Left); }
void independent_aux_requests() {
 Controller c; c.command("ARM",0,true); c.command("F",0,true);
 TEST_ASSERT_TRUE(c.command("BRUSH ON",1,true)); TEST_ASSERT_TRUE(c.brushOutput()); TEST_ASSERT_FALSE(c.conveyorOutput());
 TEST_ASSERT_TRUE(c.command("CONVEYOR ON",2,true)); TEST_ASSERT_TRUE(c.conveyorOutput());
 c.command("BRUSH OFF",3,true); TEST_ASSERT_FALSE(c.brushOutput()); TEST_ASSERT_TRUE(c.conveyorOutput());
 c.command("CONVEYOR OFF",4,true); TEST_ASSERT_FALSE(c.conveyorOutput());
}
void aux_require_arm() { Controller c; TEST_ASSERT_FALSE(c.command("BRUSH ON",0,true)); TEST_ASSERT_FALSE(c.command("CONVEYOR ON",0,true)); TEST_ASSERT_FALSE(c.brushOutput()); TEST_ASSERT_FALSE(c.conveyorOutput()); }
void aux_requests_do_not_refresh_deadman() {
 Controller c; c.command("ARM",0,true); c.command("F",0,true);
 c.command("BRUSH ON",1199,true); c.command("CONVEYOR ON",1199,true); c.tick(1200,true);
 TEST_ASSERT_TRUE(c.motion==Motion::Stop); TEST_ASSERT_FALSE(c.brushOutput()); TEST_ASSERT_FALSE(c.conveyorOutput());
}
void stop_alias_latches_and_clears_aux() {
 Controller c; autoStart(c); c.command("CLEAN ON",0,true); c.command("STOP",1,true);
 TEST_ASSERT_TRUE(c.estop); TEST_ASSERT_FALSE(c.armed); TEST_ASSERT_FALSE(c.brushes); TEST_ASSERT_FALSE(c.conveyor);
 TEST_ASSERT_FALSE(c.command("ARM",2,true)); c.command("RESET",3,true); TEST_ASSERT_FALSE(c.armed);
}
void sensor_fault_clears_independent_aux() {
 Controller c; autoStart(c); c.command("BRUSH ON",0,true); c.command("CONVEYOR ON",0,true);
 c.sample(0,-1,1); c.tick(1,true); TEST_ASSERT_FALSE(c.armed); TEST_ASSERT_FALSE(c.brushes); TEST_ASSERT_FALSE(c.conveyor);
}
void cleaning_aliases_control_both() {
 Controller c; c.command("ARM",0,true); c.command("F",0,true); c.command("CLEAN ON",0,true);
 TEST_ASSERT_TRUE(c.brushOutput()); TEST_ASSERT_TRUE(c.conveyorOutput());
 c.command("CLEAN OFF",1,true); TEST_ASSERT_FALSE(c.brushOutput()); TEST_ASSERT_FALSE(c.conveyorOutput());
}
int main() {
 UNITY_BEGIN();
 RUN_TEST(independent_aux_requests); RUN_TEST(aux_require_arm); RUN_TEST(aux_requests_do_not_refresh_deadman);
 RUN_TEST(stop_alias_latches_and_clears_aux); RUN_TEST(sensor_fault_clears_independent_aux); RUN_TEST(cleaning_aliases_control_both);
 RUN_TEST(boot_safe); RUN_TEST(arm_stays_stopped); RUN_TEST(auto_requires_arm_and_ranges);
 RUN_TEST(clear_forward); RUN_TEST(obstacle_settles_then_left); RUN_TEST(clearer_right); RUN_TEST(ties_left);
 RUN_TEST(all_blocked); RUN_TEST(side_too_close); RUN_TEST(turn_stops_on_side_obstacle); RUN_TEST(turn_time_bounded);
 RUN_TEST(missing_disarms_no_restart); RUN_TEST(out_of_range); RUN_TEST(stale_individual_sensor); RUN_TEST(freshness_boundary);
 RUN_TEST(manual_deadman); RUN_TEST(unknown_does_not_refresh); RUN_TEST(repeat_manual_refreshes); RUN_TEST(manual_rollover);
 RUN_TEST(turn_rollover); RUN_TEST(estop_latches); RUN_TEST(switch_open_cannot_reset); RUN_TEST(hardware_stop_from_manual);
 RUN_TEST(s_exits_auto); RUN_TEST(mode_clears_turn); RUN_TEST(arm_clears_modes); RUN_TEST(cleaning_forward_only);
 RUN_TEST(clean_off_and_disarm); RUN_TEST(parser_normalization); RUN_TEST(parser_overflow_discards);
 RUN_TEST(gate_neutral_and_reverse); RUN_TEST(gate_rollover);
 return UNITY_END();
}
