export const COMMANDS = ['ARM','DISARM','RESET','AUTO','MANUAL','F','B','L','R','S','STOP','ESTOP','BRUSH ON','BRUSH OFF','CONVEYOR ON','CONVEYOR OFF','CLEAN ON','CLEAN OFF'] as const;
export type Command = typeof COMMANDS[number];
export type Direction = 'F'|'B'|'L'|'R';
export const MOTIONS = ['STOPPED','FORWARD','BACKWARD','LEFT','RIGHT'] as const;
export interface Telemetry {
 v:1; fw:string; ms:number; armed:boolean; auto:boolean; estop:boolean; healthy:boolean;
 requested:number; applied:number; en:boolean; brushReq:boolean; conveyorReq:boolean; brush:boolean; conveyor:boolean;
 nav:string; cm:[number,number,number]; age:[number,number,number];
 // Optional pair: older protocol-v1 firmware keeps its existing behavior.
 mode?:'PROTECTED_ROVER'|'USB_BENCH_DIAGNOSTIC'|'MOTOR_OPERATION'|'SIMULATION'; motorCapable?:boolean;
 simulated?:boolean;
 commissioningReady?:boolean; inhibit?:'NONE'|'COMMISSIONING_REQUIRED'|'PWM_FAULT'|'COMMAND_TIMEOUT';
}
export interface Log {at:number;kind:'TX'|'RX'|'ACK'|'ERROR'|'INFO';text:string}
export interface DiagnosticRecord {
 id:number; at:number; timestamp:string; session:string; source:'hardware'|'simulation'|'bridge'; port:string|null;
 event:'telemetry'|'emergency'|'connection'|'communication'|'command'|'ack'|'info'; kind:Log['kind']; message:string; telemetry:Telemetry|null;
}
export interface BridgeState {
 connected:boolean; connecting:boolean; protocolReady:boolean; simulation:boolean; port:string|null; telemetry:Telemetry|null;
 receivedAt:number|null; intent:Direction|null; logs:Log[]; error:string|null;
 disconnecting?:boolean;
 vision?:VisionState;
}
// Camera detections in normalized frame coordinates (0..1), box centre and size.
export interface VisionTarget {label:string; conf:number; cx:number; cy:number; w:number; h:number}
export const VISION_PHASES = ['OFF','WAITING','APPROACH','ALIGN_LEFT','ALIGN_RIGHT','EXPLORE','BLOCKED'] as const;
export interface VisionState {
 enabled:boolean; phase:typeof VISION_PHASES[number]; reason:string;
 detectedAt:number|null; detector:string|null; targets:VisionTarget[];
}
export const MAX_VISION_TARGETS = 6;
export function visionFrame(value:unknown):{detector:string;targets:VisionTarget[]} {
 if(!value||typeof value!=='object')throw Error('Invalid vision frame');
 const v=value as {detector?:unknown;targets?:unknown};
 if(typeof v.detector!=='string'||!/^[A-Za-z0-9 ._-]{1,32}$/.test(v.detector))throw Error('Invalid vision detector');
 if(!Array.isArray(v.targets)||v.targets.length>MAX_VISION_TARGETS)throw Error('Invalid vision targets');
 const unit=(n:unknown)=>typeof n==='number'&&Number.isFinite(n)&&n>=0&&n<=1;
 const targets=v.targets.map(raw=>{
  const t=raw as VisionTarget;
  if(!t||typeof t!=='object'||typeof t.label!=='string'||!/^[A-Za-z0-9 ._-]{1,32}$/.test(t.label)||![t.conf,t.cx,t.cy,t.w,t.h].every(unit))throw Error('Invalid vision target');
  return {label:t.label,conf:t.conf,cx:t.cx,cy:t.cy,w:t.w,h:t.h};
 });
 return {detector:v.detector,targets};
}
export const NAV = ['DISARMED','MANUAL','CRUISE','SETTLE','TURN_DEAD_TIME','TURNING','REASSESS','TURN_LIMIT','SENSOR_FAULT','ESTOP'];
export function isCommand(value:unknown):value is Command {return typeof value==='string' && (COMMANDS as readonly string[]).includes(value);}
export function isDirection(value:unknown):value is Direction {return typeof value==='string' && ['F','B','L','R'].includes(value);}
export function motorControlAvailable(t:Telemetry|null|undefined):boolean {
 return !!t&&t.motorCapable!==false&&(t.mode!=='MOTOR_OPERATION'||(t.commissioningReady===true&&t.inhibit==='NONE'));
}
export function feedbackAllowsControl(t:Telemetry|null|undefined):boolean {
 return !!t&&(t.mode==='MOTOR_OPERATION'||t.mode==='USB_BENCH_DIAGNOSTIC'||t.healthy);
}
export function motorOutputState(t:Telemetry):string {
 if(t.mode==='USB_BENCH_DIAGNOSTIC')return 'INHIBITED · USB BENCH';
 if(t.mode==='MOTOR_OPERATION'&&t.inhibit!=='NONE')return 'INHIBITED · '+(t.inhibit??'COMMISSIONING_REQUIRED').replaceAll('_',' ');
 if(t.estop)return 'INHIBITED · SOFTWARE ESTOP';
 if(!feedbackAllowsControl(t))return 'INHIBITED · PHYSICAL FEEDBACK';
 return t.en?'COMMANDED ACTIVE':t.armed?'ARMED':'DISARMED';
}
export function telemetry(value:unknown):Telemetry {
 if(!value || typeof value!=='object')throw Error('Invalid telemetry object');
 const t=value as Record<string,unknown>;
 const uint=(v:unknown)=>Number.isInteger(v)&&Number(v)>=0&&Number(v)<=0xffffffff;
 if(t.v!==1 || typeof t.fw!=='string' || (t.fw.length<1||t.fw.length>64) || !uint(t.ms) || typeof t.nav!=='string'||!NAV.includes(t.nav))throw Error('Unsupported firmware/protocol or navigation');
 for(const key of ['armed','auto','estop','healthy','en','brushReq','conveyorReq','brush','conveyor'])if(typeof t[key]!=='boolean')throw Error(`Invalid ${key}`);
 for(const key of ['requested','applied'])if(!Number.isInteger(t[key])||Number(t[key])<0||Number(t[key])>4)throw Error('Invalid motion');
 if(!Array.isArray(t.cm)||t.cm.length!==3||!t.cm.every(v=>Number.isInteger(v)&&(v===-1||(v>=2&&v<=400))))throw Error('Invalid ranges');
 if(!Array.isArray(t.age)||t.age.length!==3||!t.age.every(uint))throw Error('Invalid ages');
 if(t.mode!==undefined||t.motorCapable!==undefined){
  if(!['PROTECTED_ROVER','USB_BENCH_DIAGNOSTIC','MOTOR_OPERATION','SIMULATION'].includes(String(t.mode))||typeof t.motorCapable!=='boolean'||t.motorCapable!==(t.mode!=='USB_BENCH_DIAGNOSTIC'))throw Error('Invalid operating mode');
  if(!t.motorCapable&&(t.armed||t.auto||t.en||t.brushReq||t.conveyorReq||t.brush||t.conveyor||t.requested!==0||t.applied!==0))throw Error('Contradictory diagnostic telemetry');
 }
 const active=t.armed||t.auto||t.en||t.brushReq||t.conveyorReq||t.brush||t.conveyor||t.requested!==0||t.applied!==0;
 if(t.mode==='MOTOR_OPERATION'){
  if(typeof t.commissioningReady!=='boolean'||!['NONE','COMMISSIONING_REQUIRED','PWM_FAULT','COMMAND_TIMEOUT'].includes(String(t.inhibit)))throw Error('Invalid commissioning telemetry');
  if((!t.commissioningReady&&t.inhibit!=='COMMISSIONING_REQUIRED')||(t.commissioningReady&&t.inhibit==='COMMISSIONING_REQUIRED')||((!t.commissioningReady||t.inhibit!=='NONE')&&active))throw Error('Contradictory commissioning telemetry');
 }else if(t.commissioningReady!==undefined||t.inhibit!==undefined)throw Error('Unexpected commissioning telemetry');
 if(t.mode==='SIMULATION'){if(t.simulated!==true||t.fw!=='rover-sim-v1')throw Error('Simulation telemetry must be explicitly synthetic');}
 else if(t.simulated!==undefined)throw Error('Physical telemetry cannot claim simulated outputs');
 const physicalRequired=t.mode===undefined||t.mode==='PROTECTED_ROVER';
 if((t.en && (!t.armed||t.estop||(physicalRequired&&!t.healthy)||t.applied===0))||(!t.en&&t.applied!==0)||((t.brush||t.conveyor)&&(!t.en||t.applied!==1)))throw Error('Contradictory output telemetry');
 return t as unknown as Telemetry;
}
export function parseLine(line:string):{kind:'telemetry';data:Telemetry}|{kind:'ack';ok:boolean;command:string}|{kind:'raw'} {
 if(line.length>1024)throw Error('Serial line too long');
 if(line.startsWith('TEL '))return {kind:'telemetry',data:telemetry(JSON.parse(line.slice(4)))};
 if(/^(OK|ERR) /.test(line))return {kind:'ack',ok:line.startsWith('OK '),command:line.slice(line.indexOf(' ')+1)};
 return {kind:'raw'};
}
export function isState(value:unknown):value is BridgeState {
 if(!value||typeof value!=='object')return false;const s=value as BridgeState;
 if(typeof s.connected!=='boolean'||typeof s.connecting!=='boolean'||typeof s.protocolReady!=='boolean'||typeof s.simulation!=='boolean'||!(s.port===null||typeof s.port==='string')||!(s.error===null||typeof s.error==='string')||!Array.isArray(s.logs)||s.logs.length>200||!(s.receivedAt===null||Number.isFinite(s.receivedAt))||!(s.intent===null||isDirection(s.intent)))return false;
 if(s.disconnecting!==undefined&&typeof s.disconnecting!=='boolean')return false;
 if(s.vision!==undefined){const v=s.vision;if(!v||typeof v.enabled!=='boolean'||!(VISION_PHASES as readonly string[]).includes(v.phase)||typeof v.reason!=='string'||!(v.detectedAt===null||Number.isFinite(v.detectedAt))||!(v.detector===null||typeof v.detector==='string'))return false;try{visionFrame({detector:v.detector??'none',targets:v.targets});}catch{return false;}}
 if(s.telemetry&&((!s.simulation&&s.telemetry.mode==='SIMULATION')||(s.simulation&&['MOTOR_OPERATION','USB_BENCH_DIAGNOSTIC'].includes(s.telemetry.mode??''))))return false;
 try{if(s.telemetry!==null)telemetry(s.telemetry);return s.logs.every(l=>l&&Number.isFinite(l.at)&&['TX','RX','ACK','ERROR','INFO'].includes(l.kind)&&typeof l.text==='string');}catch{return false;}
}
