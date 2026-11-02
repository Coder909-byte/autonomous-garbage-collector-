#pragma once
#include <stdint.h>
#include <string.h>
#include <ctype.h>

namespace rover {
constexpr uint32_t MANUAL_MS = 1200, FRESH_MS = 500;
constexpr uint32_t SETTLE_MS = 180, TURN_MS = 540, NEUTRAL_MS = 100;
constexpr unsigned MAX_TURN_ATTEMPTS = 3;
constexpr int BLOCK_CM = 35, CLEAR_CM = 45, SIDE_STOP_CM = 20;
enum class Motion { Stop, Forward, Backward, Left, Right };
enum class NavPhase { Disarmed, Manual, Cruise, Settle, TurnPending, Turning, Reassess, Blocked, SensorFault, Emergency };
struct Range {
  int cm = -1;
  uint32_t at = 0;
  uint32_t sequence = 0;
  bool fresh(uint32_t now) const { return cm >= 2 && cm <= 400 && uint32_t(now-at) <= FRESH_MS; }
};
class Controller {
 public:
  bool armed = false, automatic = false, brushes = false, conveyor = false, estop = false;
  Motion motion = Motion::Stop;
  Range ranges[3]; // front, left, right
  void emergency() { estop = true; disarm(); }
  void disarm() {
    armed = automatic = brushes = conveyor = false;
    motion = Motion::Stop; phase = NavPhase::Cruise; turnAttempts = 0;
  }
  bool command(const char *cmd, uint32_t now, bool healthy) {
    if (!healthy) emergency();
    if (!strcmp(cmd,"ESTOP") || !strcmp(cmd,"STOP")) { emergency(); return true; }
    if (!strcmp(cmd,"DISARM")) { disarm(); return true; }
    if (!strcmp(cmd,"RESET")) {
      if (!healthy || armed) return false;
      estop = false; disarm(); return true;
    }
    if (!strcmp(cmd,"ARM")) {
      if (estop || !healthy) return false;
      disarm(); armed = true; return true;
    }
    if (!strcmp(cmd,"S")) {
      // Stop always exits AUTO, so it cannot resume on the next tick.
      automatic = false; motion = Motion::Stop; phase = NavPhase::Cruise; turnAttempts = 0; return true;
    }
    if (!strcmp(cmd,"MANUAL")) {
      automatic = false; motion = Motion::Stop; phase = NavPhase::Cruise; turnAttempts = 0; return true;
    }
    if (!strcmp(cmd,"CLEAN OFF")) { brushes = conveyor = false; return true; }
    if (!strcmp(cmd,"BRUSH OFF")) { brushes = false; return true; }
    if (!strcmp(cmd,"CONVEYOR OFF")) { conveyor = false; return true; }
    if (!armed || estop) return false;
    if (!strcmp(cmd,"CLEAN ON")) { brushes = conveyor = true; return true; }
    if (!strcmp(cmd,"BRUSH ON")) { brushes = true; return true; }
    if (!strcmp(cmd,"CONVEYOR ON")) { conveyor = true; return true; }
    if (!strcmp(cmd,"AUTO")) {
      if (!valid(now)) return false;
      automatic = true; motion = Motion::Stop; phase = NavPhase::Cruise; turnAttempts = 0; return true;
    }
    if (automatic) return false;
    Motion next;
    if (!strcmp(cmd,"F")) next = Motion::Forward;
    else if (!strcmp(cmd,"B")) next = Motion::Backward;
    else if (!strcmp(cmd,"L")) next = Motion::Left;
    else if (!strcmp(cmd,"R")) next = Motion::Right;
    else return false;
    motion = next; manualAt = now; return true;
  }
  void sample(unsigned sensor, int cm, uint32_t now) {
    if (sensor < 3) {
      ranges[sensor].cm = cm; ranges[sensor].at = now; ++ranges[sensor].sequence;
    }
  }
  bool valid(uint32_t now) const {
    return ranges[0].fresh(now) && ranges[1].fresh(now) && ranges[2].fresh(now);
  }
  bool brushOutput() const { return armed && !estop && brushes && motion == Motion::Forward; }
  bool conveyorOutput() const { return armed && !estop && conveyor && motion == Motion::Forward; }
  bool cleanOutput() const { return brushOutput() && conveyorOutput(); }
  NavPhase navigation() const {
    if (estop) return NavPhase::Emergency;
    if (phase == NavPhase::Blocked || phase == NavPhase::SensorFault) return phase;
    if (!armed) return NavPhase::Disarmed;
    return automatic ? phase : NavPhase::Manual;
  }
  const char *navigationName() const {
    switch (navigation()) {
      case NavPhase::Disarmed: return "DISARMED";
      case NavPhase::Manual: return "MANUAL";
      case NavPhase::Cruise: return "CRUISE";
      case NavPhase::Settle: return "SETTLE";
      case NavPhase::TurnPending: return "TURN_DEAD_TIME";
      case NavPhase::Turning: return "TURNING";
      case NavPhase::Reassess: return "REASSESS";
      case NavPhase::Blocked: return "TURN_LIMIT";
      case NavPhase::SensorFault: return "SENSOR_FAULT";
      default: return "ESTOP";
    }
  }
  // Called only after the adapter has applied PWM and permitted EN. This is
  // software output feedback, not an encoder or proof of physical movement.
  void reportApplied(Motion applied, uint32_t now) {
    if (armed && automatic && !estop && phase == NavPhase::TurnPending && applied == motion) {
      phase = NavPhase::Turning; phaseAt = now;
    }
  }
  void tick(uint32_t now, bool healthy) {
    if (!healthy) emergency();
    if (!armed || estop) { motion = Motion::Stop; return; }
    if (!automatic) {
      if (motion != Motion::Stop && uint32_t(now-manualAt) >= MANUAL_MS) motion = Motion::Stop;
      return;
    }
    // A missing/stale sensor latches a disarm; fresh readings alone never restart.
    if (!valid(now)) { disarm(); phase = NavPhase::SensorFault; return; }
    const int front = ranges[0].cm, left = ranges[1].cm, right = ranges[2].cm;
    if (phase == NavPhase::TurnPending || phase == NavPhase::Turning) {
      const int turningSide = motion == Motion::Left ? left : right;
      if ((phase == NavPhase::Turning && uint32_t(now-phaseAt) >= TURN_MS) || turningSide <= CLEAR_CM ||
          left <= SIDE_STOP_CM || right <= SIDE_STOP_CM) {
        beginReassessment(now);
      }
      return;
    }
    if (phase == NavPhase::Settle || phase == NavPhase::Reassess) {
      motion = Motion::Stop;
      if (uint32_t(now-phaseAt) < SETTLE_MS) return;
      // After a turn, never use the same pre-stop readings for another turn
      // or for forward recovery. Versions also work at millis() rollover.
      if (phase == NavPhase::Reassess) {
        for (unsigned i=0;i<3;++i) if (ranges[i].sequence == reassessSequence[i]) return;
      }
      // Hysteresis: enter avoidance at 35 cm, leave it only above 45 cm.
      if (front > CLEAR_CM && left > SIDE_STOP_CM && right > SIDE_STOP_CM) {
        phase = NavPhase::Cruise; motion = Motion::Forward; turnAttempts = 0; return;
      }
      if (turnAttempts >= MAX_TURN_ATTEMPTS) {
        disarm(); phase = NavPhase::Blocked; return;
      }
      if (left > SIDE_STOP_CM && right > SIDE_STOP_CM && (left > CLEAR_CM || right > CLEAR_CM)) {
        motion = left >= right ? Motion::Left : Motion::Right;
        phase = NavPhase::TurnPending; ++turnAttempts;
      }
      return;
    }
    if (front <= BLOCK_CM || left <= SIDE_STOP_CM || right <= SIDE_STOP_CM) {
      motion = Motion::Stop; phase = NavPhase::Settle; phaseAt = now;
    } else motion = Motion::Forward;
  }
 private:
  void beginReassessment(uint32_t now) {
    motion = Motion::Stop; phase = NavPhase::Reassess; phaseAt = now;
    for (unsigned i=0;i<3;++i) reassessSequence[i] = ranges[i].sequence;
  }
  NavPhase phase = NavPhase::Cruise;
  uint32_t phaseAt = 0, manualAt = 0;
  uint32_t reassessSequence[3] = {};
  unsigned turnAttempts = 0;
};

// A bounded line parser; an overlong line is discarded in full, never truncated
// into a valid command. The caller must disarm on overflow.
class LineParser {
 public:
  enum Result { None, Ready, Overflow };
  Result feed(char ch) {
    if (ch == '\r' || ch == '\n') {
      if (discard) { discard = false; used = 0; return None; }
      buffer[used] = 0;
      while (used && isspace(static_cast<unsigned char>(buffer[used-1]))) buffer[--used] = 0;
      unsigned start = 0;
      while (buffer[start] && isspace(static_cast<unsigned char>(buffer[start]))) ++start;
      if (start) memmove(buffer,buffer+start,used-start+1);
      bool hasText = buffer[0] != 0; used = 0;
      return hasText ? Ready : None;
    }
    if (discard) return None;
    if (used == sizeof(buffer)-1 || (static_cast<unsigned char>(ch) < 32 && ch != '\t')) {
      discard = true; used = 0; return Overflow;
    }
    buffer[used++] = static_cast<char>(toupper(static_cast<unsigned char>(ch)));
    return None;
  }
  const char *line() const { return buffer; }
 private:
  char buffer[49] = {};
  unsigned used = 0;
  bool discard = false;
};

// Disable every driver for a neutral interval before any new motion. This is
// electrical interlocking, not proof that a loaded motor has stopped rotating.
class MotionGate {
 public:
  Motion update(Motion requested, uint32_t now) {
    if (requested != target) { target = requested; at = now; actual = Motion::Stop; }
    if (target == Motion::Stop) actual = Motion::Stop;
    else if (uint32_t(now-at) >= NEUTRAL_MS) actual = target;
    return actual;
  }
 private:
  Motion target = Motion::Stop, actual = Motion::Stop;
  uint32_t at = 0;
};
} // namespace rover
