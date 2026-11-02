#include <unity.h>
#include <vector>
#include "rover_control.h"
using namespace rover;
void setUp() {}
void tearDown() {}
void frame(Controller &c,uint32_t now,int f=20,int l=100,int r=60) {
  c.sample(0,f,now); c.sample(1,l,now); c.sample(2,r,now);
}
struct Event { uint32_t at; Motion motion; };
struct Rover {
  Controller c;
  MotionGate gate;
  Motion actual = Motion::Stop;
  std::vector<Event> events;
  uint32_t base;
  int front=20,left=100,right=60;
  explicit Rover(uint32_t start=0):base(start) {
    frame(c,base,front,left,right); c.command("ARM",base,true); c.command("AUTO",base,true);
  }
  void apply(uint32_t at) {
    Motion next=gate.update(c.motion,at);
    if (next!=actual) events.push_back({at,next});
    actual=next; c.reportApplied(actual,at);
  }
  void step(uint32_t elapsed,bool fresh=true) {
    uint32_t at=base+elapsed;
    if(fresh) frame(c,at,front,left,right);
    c.tick(at,true); apply(at);
    c.tick(at,true); apply(at); // both tick/apply passes used by firmware loop
  }
  void advance(uint32_t from,uint32_t through) { for(uint32_t t=from;t<=through;t+=10) step(t); }
};
void left_turn_is_continuous() {
  Rover h; h.advance(0,280); TEST_ASSERT_TRUE(h.actual==Motion::Left);
  for(uint32_t t=281;t<820;++t) { h.step(t); TEST_ASSERT_TRUE(h.actual==Motion::Left); }
  h.step(820); TEST_ASSERT_TRUE(h.actual==Motion::Stop); TEST_ASSERT_TRUE(h.c.navigation()==NavPhase::Reassess);
}
void right_turn_is_continuous() {
  Rover h; h.left=60; h.right=100; h.advance(0,280); TEST_ASSERT_TRUE(h.actual==Motion::Right);
  for(uint32_t t=281;t<820;++t) { h.step(t); TEST_ASSERT_TRUE(h.actual==Motion::Right); }
  h.step(820); TEST_ASSERT_TRUE(h.actual==Motion::Stop);
}
void dead_time_does_not_consume_turn_duration() {
  Rover h; h.advance(0,180); TEST_ASSERT_TRUE(h.c.navigation()==NavPhase::TurnPending); TEST_ASSERT_TRUE(h.actual==Motion::Stop);
  h.step(279); TEST_ASSERT_TRUE(h.actual==Motion::Stop); h.step(280); TEST_ASSERT_TRUE(h.c.navigation()==NavPhase::Turning);
  h.step(819); TEST_ASSERT_TRUE(h.actual==Motion::Left); h.step(820); TEST_ASSERT_TRUE(h.actual==Motion::Stop);
}
void repeated_applied_feedback_does_not_extend_turn() {
  Rover h; h.advance(0,810); TEST_ASSERT_TRUE(h.actual==Motion::Left);
  h.c.reportApplied(Motion::Left,819); h.step(820); TEST_ASSERT_TRUE(h.actual==Motion::Stop);
}
void reassessment_requires_every_new_sensor() {
  Rover h; h.advance(0,820); h.step(1000,false); TEST_ASSERT_TRUE(h.actual==Motion::Stop);
  h.c.sample(0,100,1000); h.c.sample(1,100,1000); h.step(1000,false);
  TEST_ASSERT_TRUE(h.actual==Motion::Stop); TEST_ASSERT_TRUE(h.c.navigation()==NavPhase::Reassess);
  h.c.sample(2,60,1000); h.step(1000,false); TEST_ASSERT_TRUE(h.c.motion==Motion::Forward);
}
void reassessment_minimum_settle_time() {
  Rover h; h.advance(0,820); h.front=100; h.step(821); h.step(999);
  TEST_ASSERT_TRUE(h.c.motion==Motion::Stop); h.step(1000); TEST_ASSERT_TRUE(h.c.motion==Motion::Forward);
}
void fresh_clear_path_exits_avoidance() {
  Rover h; h.advance(0,820); h.front=100; h.advance(830,1100);
  TEST_ASSERT_TRUE(h.actual==Motion::Forward); TEST_ASSERT_TRUE(h.c.navigation()==NavPhase::Cruise);
  TEST_ASSERT_EQUAL(3,h.events.size()); // one turn on, one stop, forward on
}
void hysteresis_prevents_front_threshold_chatter() {
  Rover h; h.advance(0,820); h.front=36; h.step(1000);
  TEST_ASSERT_TRUE(h.c.motion==Motion::Left); TEST_ASSERT_FALSE(h.c.motion==Motion::Forward);
  h.front=45; h.step(1100); TEST_ASSERT_TRUE(h.actual==Motion::Left);
}
void bounded_retries(Motion direction) {
  Rover h; if(direction==Motion::Right) {h.left=60;h.right=100;}
  h.advance(0,4000); TEST_ASSERT_FALSE(h.c.armed); TEST_ASSERT_TRUE(h.c.navigation()==NavPhase::Blocked);
  TEST_ASSERT_EQUAL(2*MAX_TURN_ATTEMPTS,h.events.size());
  for(unsigned i=0;i<h.events.size();i+=2) {
    TEST_ASSERT_TRUE(h.events[i].motion==direction); TEST_ASSERT_TRUE(h.events[i+1].motion==Motion::Stop);
    TEST_ASSERT_EQUAL_UINT32(TURN_MS,uint32_t(h.events[i+1].at-h.events[i].at));
    if(i) TEST_ASSERT_GREATER_OR_EQUAL(SETTLE_MS+NEUTRAL_MS,uint32_t(h.events[i].at-h.events[i-1].at));
  }
  h.front=200; h.advance(4010,5000); TEST_ASSERT_TRUE(h.actual==Motion::Stop); TEST_ASSERT_FALSE(h.c.armed);
  TEST_ASSERT_FALSE(h.c.command("AUTO",5000,true));
  TEST_ASSERT_TRUE(h.c.command("ARM",5000,true)); TEST_ASSERT_TRUE(h.c.command("AUTO",5000,true));
  h.step(5000); h.step(5100); TEST_ASSERT_TRUE(h.actual==Motion::Forward);
}
void persistent_left_obstacle_is_bounded() { bounded_retries(Motion::Left); }
void persistent_right_obstacle_is_bounded() { bounded_retries(Motion::Right); }
void reassessment_selects_updated_direction() {
  Rover h; h.advance(0,820); h.left=60; h.right=120; h.step(1000);
  TEST_ASSERT_TRUE(h.c.motion==Motion::Right); TEST_ASSERT_TRUE(h.actual==Motion::Stop);
  h.step(1100); TEST_ASSERT_TRUE(h.actual==Motion::Right);
}
void estop_preempts_every_phase() {
  const uint32_t points[]={0,180,280,820};
  for(uint32_t point:points) {
    Rover h; h.advance(0,point); h.c.tick(point,false); h.apply(point); TEST_ASSERT_TRUE(h.actual==Motion::Stop);
    TEST_ASSERT_TRUE(h.c.estop); h.front=200; h.step(point+1);
    TEST_ASSERT_FALSE(h.c.command("ARM",point+1,true)); TEST_ASSERT_FALSE(h.c.armed);
  }
}
void invalid_sensor_preempts_every_phase() {
  const uint32_t points[]={0,180,280,820};
  for(uint32_t point:points) for(unsigned sensor=0;sensor<3;++sensor) {
    Rover h; h.advance(0,point); h.c.sample(sensor,-1,point); h.c.tick(point,true); h.apply(point);
    TEST_ASSERT_TRUE(h.actual==Motion::Stop); TEST_ASSERT_FALSE(h.c.armed);
    TEST_ASSERT_TRUE(h.c.navigation()==NavPhase::SensorFault);
    h.front=200; h.step(point+1); TEST_ASSERT_FALSE(h.c.armed);
  }
}
void stale_sensor_preempts_every_phase() {
  const uint32_t points[]={0,180,280,820};
  for(uint32_t point:points) {
    Rover h; h.advance(0,point); h.c.sample(0,100,point+501); h.c.sample(1,100,point+501);
    h.c.tick(point+501,true); h.apply(point+501); TEST_ASSERT_TRUE(h.actual==Motion::Stop);
    TEST_ASSERT_TRUE(h.c.navigation()==NavPhase::SensorFault); TEST_ASSERT_FALSE(h.c.armed);
  }
}
void timer_and_reassessment_survive_rollover() {
  Rover h(UINT32_MAX-300); h.advance(0,820); TEST_ASSERT_EQUAL(2,h.events.size());
  TEST_ASSERT_EQUAL_UINT32(TURN_MS,uint32_t(h.events[1].at-h.events[0].at));
  h.front=100; h.step(1000); h.step(1100); TEST_ASSERT_TRUE(h.actual==Motion::Forward);
}
void side_clearance_loss_stops_without_immediate_retry() {
  Rover h; h.advance(0,280); h.left=45; h.step(300); TEST_ASSERT_TRUE(h.actual==Motion::Stop);
  h.left=100; h.step(301); h.step(479); TEST_ASSERT_TRUE(h.c.motion==Motion::Stop);
  h.step(480); TEST_ASSERT_TRUE(h.c.navigation()==NavPhase::TurnPending); TEST_ASSERT_TRUE(h.actual==Motion::Stop);
}
void final_attempt_may_recover_with_fresh_clear_path() {
  Rover h; h.advance(0,2460); TEST_ASSERT_EQUAL(2*MAX_TURN_ATTEMPTS,h.events.size());
  h.front=100; h.step(2640); h.step(2740);
  TEST_ASSERT_TRUE(h.c.armed); TEST_ASSERT_TRUE(h.actual==Motion::Forward);
}
void obstacle_cleared_during_initial_settle_needs_no_turn() {
  Rover h; h.step(0); h.front=100; h.step(180); h.step(280);
  TEST_ASSERT_TRUE(h.actual==Motion::Forward); TEST_ASSERT_EQUAL(1,h.events.size());
}
void pending_turn_safety_clearance_is_checked() {
  Rover h; h.advance(0,180); h.left=20; h.step(200); TEST_ASSERT_TRUE(h.actual==Motion::Stop);
  TEST_ASSERT_TRUE(h.c.navigation()==NavPhase::Reassess); TEST_ASSERT_TRUE(h.events.empty());
}
void stop_command_cancels_reassessment_and_future_turns() {
  Rover h; h.advance(0,820); h.c.command("STOP",820,true); h.advance(830,2000);
  TEST_ASSERT_TRUE(h.c.estop); TEST_ASSERT_TRUE(h.actual==Motion::Stop); TEST_ASSERT_EQUAL(2,h.events.size());
}
int main() {
 UNITY_BEGIN();
 RUN_TEST(left_turn_is_continuous); RUN_TEST(right_turn_is_continuous);
 RUN_TEST(dead_time_does_not_consume_turn_duration); RUN_TEST(repeated_applied_feedback_does_not_extend_turn);
 RUN_TEST(reassessment_requires_every_new_sensor); RUN_TEST(reassessment_minimum_settle_time);
 RUN_TEST(fresh_clear_path_exits_avoidance); RUN_TEST(hysteresis_prevents_front_threshold_chatter);
 RUN_TEST(persistent_left_obstacle_is_bounded); RUN_TEST(persistent_right_obstacle_is_bounded);
 RUN_TEST(reassessment_selects_updated_direction); RUN_TEST(estop_preempts_every_phase);
 RUN_TEST(invalid_sensor_preempts_every_phase); RUN_TEST(stale_sensor_preempts_every_phase);
 RUN_TEST(timer_and_reassessment_survive_rollover); RUN_TEST(side_clearance_loss_stops_without_immediate_retry);
 RUN_TEST(final_attempt_may_recover_with_fresh_clear_path); RUN_TEST(obstacle_cleared_during_initial_settle_needs_no_turn);
 RUN_TEST(pending_turn_safety_clearance_is_checked); RUN_TEST(stop_command_cancels_reassessment_and_future_turns);
 return UNITY_END();
}
