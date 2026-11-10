export const COMMANDS = ['ARM','DISARM','RESET','AUTO','MANUAL','F','B','L','R','S','STOP','ESTOP','BRUSH ON','BRUSH OFF','CONVEYOR ON','CONVEYOR OFF','CLEAN ON','CLEAN OFF'] as const;
export type Command = typeof COMMANDS[number];
export type Direction = 'F'|'B'|'L'|'R';
export const MOTIONS = ['STOPPED','FORWARD','BACKWARD','LEFT','RIGHT'] as const;
export interface Telemetry {
 v:1; fw:string; ms:number; armed:boolean; auto:boolean; estop:boolean; healthy:boolean;
 requested:number; applied:number; en:boolean; brushReq:boolean; conveyorReq:boolean; brush:boolean; conveyor:boolean;
 nav:string; cm:[number,number,number]; age:[number,number,number];
}
export interface Log {at:number;kind:'TX'|'RX'|'ACK'|'ERROR'|'INFO';text:string}
export interface BridgeState {
 connected:boolean; connecting:boolean; protocolReady:boolean; simulation:boolean; port:string|null; telemetry:Telemetry|null;
 receivedAt:number|null; intent:Direction|null; logs:Log[]; error:string|null;
}
export const NAV = ['DISARMED','MANUAL','CRUISE','SETTLE','TURN_DEAD_TIME','TURNING','REASSESS','TURN_LIMIT','SENSOR_FAULT','ESTOP'];
export function isCommand(value:unknown):value is Command {return typeof value==='string' && (COMMANDS as readonly string[]).includes(value);}
export function isDirection(value:unknown):value is Direction {return typeof value==='string' && ['F','B','L','R'].includes(value);}
export function telemetry(value:unknown):Telemetry {
 if(!value || typeof value!=='object')throw Error('Invalid telemetry object');
 const t=value as Record<string,unknown>;
 const uint=(v:unknown)=>Number.isInteger(v)&&Number(v)>=0&&Number(v)<=0xffffffff;
 if(t.v!==1 || typeof t.fw!=='string' || (t.fw.length<1||t.fw.length>64) || !uint(t.ms) || typeof t.nav!=='string'||!NAV.includes(t.nav))throw Error('Unsupported firmware/protocol or navigation');
 for(const key of ['armed','auto','estop','healthy','en','brushReq','conveyorReq','brush','conveyor'])if(typeof t[key]!=='boolean')throw Error(`Invalid ${key}`);
 for(const key of ['requested','applied'])if(!Number.isInteger(t[key])||Number(t[key])<0||Number(t[key])>4)throw Error('Invalid motion');
 if(!Array.isArray(t.cm)||t.cm.length!==3||!t.cm.every(v=>Number.isInteger(v)&&(v===-1||(v>=2&&v<=400))))throw Error('Invalid ranges');
 if(!Array.isArray(t.age)||t.age.length!==3||!t.age.every(uint))throw Error('Invalid ages');
 if((t.en && (!t.armed||t.estop||!t.healthy||t.applied===0))||(!t.en&&t.applied!==0)||((t.brush||t.conveyor)&&(!t.en||t.applied!==1)))throw Error('Contradictory output telemetry');
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
 if(typeof s.connected!=='boolean'||typeof s.connecting!=='boolean'||typeof s.protocolReady!=='boolean'||typeof s.simulation!=='boolean'||!Array.isArray(s.logs)||s.logs.length>200||!(s.receivedAt===null||Number.isFinite(s.receivedAt))||!(s.intent===null||isDirection(s.intent)))return false;
 try{if(s.telemetry!==null)telemetry(s.telemetry);return s.logs.every(l=>l&&Number.isFinite(l.at)&&['TX','RX','ACK','ERROR','INFO'].includes(l.kind)&&typeof l.text==='string');}catch{return false;}
}
