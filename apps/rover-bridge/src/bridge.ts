import { EventEmitter } from 'node:events';
import { isCommand,isDirection,parseLine,type BridgeState,type Command,type Direction } from '../../../packages/protocol/index.js';
import type { Transport } from './transports.js';
export class Bridge extends EventEmitter {
 state:BridgeState={connected:false,connecting:false,protocolReady:false,simulation:false,port:null,telemetry:null,receivedAt:null,intent:null,logs:[],error:null};
 private device:Transport|null=null;private buffer='';private discard=false;private leaseAt=0;private sentAt=0;
 private pending=new Map<string,number>();private timer;private generation=0;private closing=false;private disarmAck=false;
 constructor(private now=()=>Date.now()){super();this.timer=setInterval(()=>{try{this.watchdog();}catch(e){this.log('ERROR',String(e));void this.disconnect();}},25);}
 log(kind:BridgeState['logs'][number]['kind'],text:string){this.state.logs.push({at:this.now(),kind,text:text.slice(0,1024)});this.state.logs=this.state.logs.slice(-150);if(kind==='ERROR')this.state.error=text;this.publish();}
 publish(){this.emit('state',this.state);}
 async connect(open:()=>Promise<Transport>,simulation:boolean,port:string){
  if(this.device||this.state.connecting||this.closing)throw Error('One serial owner permitted; disconnect first');
  const generation=++this.generation;this.disarmAck=false;this.state.protocolReady=false;this.state={...this.state,connecting:true,error:null,telemetry:null,receivedAt:null,intent:null,simulation,port};this.publish();
  try{
   const device=await open();if(generation!==this.generation){await device.close();return;}
   this.device=device;this.buffer='';this.discard=false;this.state.connected=true;this.state.connecting=false;
   device.on('data',(s:string)=>{if(this.device===device)this.receive(s);});
   device.on('fault',(e:Error)=>{if(this.device===device){this.log('ERROR',e.message);void this.disconnect();}});
   device.on('lost',()=>{if(this.device===device){this.log('ERROR','Serial device disconnected; STOP delivery not confirmed');void this.disconnect();}});
   // Best effort, repeated at READY to cover USB-induced board reset. No rearm.
   this.send('S');this.send('DISARM');this.log('INFO',simulation?'SIMULATION MODE · C++ controller, no hardware':'USB open · waiting for versioned telemetry');
  }catch(e){this.state.connecting=false;this.state.connected=false;this.state.port=null;this.log('ERROR',String(e));await this.disconnect();throw e;}
 }
 private send(command:Command){
  if(!this.device)throw Error('No serial connection');
  this.device.write(command+'\n');if(!this.pending.has(command))this.pending.set(command,this.now());this.log('TX',command);
 }
 ready(){const t=this.state.telemetry;return !!(this.device&&this.state.protocolReady&&t&&this.state.receivedAt!==null&&this.now()-this.state.receivedAt<1200);}
 command(value:unknown){
  if(!isCommand(value))throw Error('Command rejected by allowlist');
  if(isDirection(value))throw Error('Movement requires a live hold lease');
  if(['S','STOP','ESTOP','DISARM','MANUAL','AUTO','RESET','ARM'].includes(value))this.stopHold(false);
  if(!['S','STOP','ESTOP','DISARM','MANUAL','CLEAN OFF','BRUSH OFF','CONVEYOR OFF'].includes(value)&&!this.ready())throw Error('Fresh protocol v1 telemetry required');
  const t=this.state.telemetry;
  if(value==='RESET'&&(!t?.healthy||t.armed))throw Error('RESET requires healthy feedback and disarmed state');
  this.send(value);
 }
 hold(value:unknown){
  if(!isDirection(value))throw Error('Invalid direction');
  const t=this.state.telemetry;
  if(!this.ready()||!t?.armed||t.auto||t.estop||!t.healthy)throw Error('Manual hold requires fresh armed MANUAL healthy telemetry');
  this.leaseAt=this.now();
  if(this.state.intent!==value){this.state.intent=value;this.send(value);this.sentAt=this.now();}
 }
 stopHold(send=true){this.state.intent=null;if(send&&this.device){try{this.send('S');}catch(e){this.log('ERROR',`STOP write failed: ${String(e)}`);void this.disconnect();}}this.publish();}
 watchdog(){
  if(!this.device)return;
  if(this.state.intent){
   if(this.now()-this.leaseAt>300||!this.ready()){this.stopHold();}
   else if(this.now()-this.sentAt>=200){this.send(this.state.intent);this.sentAt=this.now();}
  }
  if(this.state.receivedAt!==null&&this.now()-this.state.receivedAt>=1500){this.log('ERROR','Telemetry stale; attempting stop and disconnect');void this.disconnect();return;}
  for(const [cmd,at] of this.pending){if(this.now()-at>2000){this.log('ERROR',`No acknowledgement: ${cmd}; stopping, delivery unconfirmed`);void this.disconnect();break;}}
 }
 receive(chunk:string){
  // Bound memory even if a serial peer never sends a newline.
  for(const ch of chunk){
   if(ch==='\n') {if(!this.discard&&this.buffer.trim())this.line(this.buffer.trim());this.buffer='';this.discard=false;}
   else if(!this.discard){if(this.buffer.length>=1024){this.buffer='';this.discard=true;this.log('ERROR','Discarded overlong serial line');this.stopHold();}else this.buffer+=ch;}
  }
 }
 private line(line:string){
  try{
   const p=parseLine(line);
   if(p.kind==='telemetry'){if(this.disarmAck&&!p.data.armed&&!p.data.en)this.state.protocolReady=true;this.state.telemetry=p.data;this.state.receivedAt=this.now();this.log('RX',line);if(this.state.intent&&(!p.data.armed||p.data.auto||p.data.estop||!p.data.healthy))this.stopHold();this.publish();}
   else if(p.kind==='ack'){if(p.ok&&p.command==='DISARM')this.disarmAck=true;this.pending.delete(p.command);this.log(p.ok?'ACK':'ERROR',line);if(!p.ok&&this.state.intent)this.stopHold();}
   else {this.log('RX',line);if(line.startsWith('READY')){this.disarmAck=false;this.state.protocolReady=false;this.stopHold(false);this.send('S');this.send('DISARM');}}
  }catch(e){this.log('ERROR',`Malformed telemetry: ${String(e)}`);this.stopHold();}
 }
 async disconnect(){
  ++this.generation;if(this.closing)return;
  this.closing=true;this.stopHold(false);const device=this.device;
  if(device){try{this.send('S');this.send('DISARM');}catch{this.log('ERROR','STOP write failed; delivery unconfirmed');}}
  this.device=null;this.pending.clear();this.state.connected=false;this.state.connecting=false;this.state.protocolReady=false;this.state.telemetry=null;this.state.receivedAt=null;this.state.port=null;this.publish();
  try{if(device)await device.close();}finally{this.closing=false;}
 }
 async dispose(){clearInterval(this.timer);await this.disconnect();}
}
