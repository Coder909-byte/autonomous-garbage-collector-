import type {Telemetry} from '../../../packages/protocol/index';

// Display-only explanations of include/rover_control.h. Never issues commands.
export function navigationDetail(t:Telemetry|null,fresh:boolean):string {
 if(!fresh||!t)return 'No fresh firmware decision. Outputs and safety state are unknown.';
 if(t.mode==='USB_BENCH_DIAGNOSTIC')return t.estop?'USB bench diagnostic: software E-stop latched. RESET clears the latch while disarmed; motor outputs remain disabled.':'USB bench diagnostic: sensor and telemetry testing only. Motor outputs are disabled in this build; ARM and AUTO are unavailable.';
 if(t.mode==='MOTOR_OPERATION'){
  if(t.inhibit!=='NONE')return 'Motor outputs inhibited: '+(t.inhibit??'COMMISSIONING_REQUIRED').replaceAll('_',' ')+'. No physical movement is verified.';
  if(t.estop)return 'Software E-stop latched. RESET clears it only while disarmed; GPIO27 is not an interlock in MOTOR_OPERATION. Software stop does not isolate motor power.';
 }
 const details:Record<string,string>={
  DISARMED:'Outputs disabled. Explicit ARM is required; ARM alone does not start motion.',
  MANUAL:'Operator hold control. Sensor avoidance is not active in MANUAL; firmware manual timeout is 1200 ms.',
  CRUISE:'Forward unless front ≤35 cm or either side ≤20 cm. All three sensors must be valid and ≤500 ms old.',
  SETTLE:'Stopped for at least 180 ms. Recover only above 45 cm front and 20 cm both sides; otherwise choose the larger side above 45 cm (ties left), with both sides above 20 cm.',
  TURN_DEAD_TIME:'Turn requested; waiting for the output adapter’s 100 ms neutral interval. Turn timer starts only after applied output is reported.',
  TURNING:'Turn for at most 540 ms. Stop sooner if the turning side ≤45 cm or either side ≤20 cm; then reassess.',
  REASSESS:'Stopped for at least 180 ms and waiting for a new sample from every sensor. Recovery needs front >45 cm and both sides >20 cm. At most three turn attempts; attempt count is not telemetered.',
  TURN_LIMIT:'Three unsuccessful turn attempts: firmware disarmed. Clearing the obstacle does not rearm the rover.',
  SENSOR_FAULT:'AUTO found an invalid or stale sensor and disarmed. Fresh readings alone never restart movement.',
  ESTOP:'Firmware E-stop latched. Physical cutoff is still required; RESET needs healthy feedback and a disarmed rover.'
 };
 return details[t.nav]??'Unknown firmware navigation phase.';
}
export function sensorValid(t:Telemetry,index:number,receiptAge:number){return t.cm[index]>=2&&t.age[index]+Math.max(0,receiptAge)<=500;}
