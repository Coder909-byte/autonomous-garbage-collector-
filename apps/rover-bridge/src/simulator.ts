import {EventEmitter} from 'node:events';
import type {Telemetry} from '../../../packages/protocol/index.js';

// Portable, virtual-only counterpart of rover_control.h. No serial ports,
// native binaries, firmware build flags or commissioning records are read.
export class Simulation extends EventEmitter {
 private timer:ReturnType<typeof setInterval>;private startup:ReturnType<typeof setTimeout>;
 private closed=false;private input='';private discard=false;private started:number;
 private armed=false;private automatic=false;private estop=false;private brush=false;private conveyor=false;
 private motion=0;private applied=0;private manualAt=0;private phase='CRUISE';private phaseAt=0;private attempts=0;
 private gateTarget=0;private gateAt=0;private sequence=0;private reassessSequence=0;private emitted=0;
 private cm:[number,number,number]=[120,100,70];private healthy=true;
 constructor(private scenario:string,private clock=()=>Date.now()){
  super();if(!['clear','obstacle','sensor-fault','estop'].includes(scenario))throw Error('Invalid simulation scenario');
  this.started=clock();
  this.startup=setTimeout(()=>{if(!this.closed)this.emit('data','READY SIMULATION DISARMED\n');},0);
  this.timer=setInterval(()=>this.tick(),20);
 }
 private now(){return Math.max(0,this.clock()-this.started)>>>0;}
 private elapsed(now:number,then:number){return (now-then)>>>0;}
 private disarm(){this.armed=this.automatic=this.brush=this.conveyor=false;this.motion=0;this.phase='CRUISE';this.attempts=0;}
 private emergency(){this.estop=true;this.disarm();}
 private sensors(now:number){
  this.healthy=!(this.scenario==='estop'&&now>=3000);
  this.cm=[this.scenario==='sensor-fault'&&now>=3000?-1:this.scenario==='obstacle'&&now>=3000&&now<6000?25:120,100,70];
  ++this.sequence;
 }
 private command(command:string,now:number):boolean {
  if(!this.healthy)this.emergency();
  if(command==='STOP'||command==='ESTOP'){this.emergency();return true;}
  if(command==='DISARM'){this.disarm();return true;}
  if(command==='RESET'){if(!this.healthy||this.armed)return false;this.estop=false;this.disarm();return true;}
  if(command==='ARM'){if(!this.healthy||this.estop)return false;this.disarm();this.armed=true;return true;}
  if(command==='S'||command==='MANUAL'){this.automatic=false;this.motion=0;this.phase='CRUISE';this.attempts=0;return true;}
  if(command==='CLEAN OFF'){this.brush=this.conveyor=false;return true;}
  if(command==='BRUSH OFF'){this.brush=false;return true;}
  if(command==='CONVEYOR OFF'){this.conveyor=false;return true;}
  if(!this.armed||this.estop)return false;
  if(command==='CLEAN ON'){this.brush=this.conveyor=true;return true;}
  if(command==='BRUSH ON'){this.brush=true;return true;}
  if(command==='CONVEYOR ON'){this.conveyor=true;return true;}
  if(command==='AUTO'){if(this.cm.some(v=>v<2||v>400))return false;this.automatic=true;this.motion=0;this.phase='CRUISE';this.attempts=0;return true;}
  if(this.automatic)return false;
  const motion=({F:1,B:2,L:3,R:4} as Record<string,number>)[command];
  if(motion===undefined)return false;this.motion=motion;this.manualAt=now;return true;
 }
 write(data:string){
  if(this.closed)throw Error('Simulator closed');
  // ACKs arrive asynchronously, like USB, after Bridge has registered a command.
  queueMicrotask(()=>{
   if(this.closed)return;this.sensors(this.now());
   for(const ch of data){
    if(ch==='\n'||ch==='\r'){
     if(this.discard){this.discard=false;this.input='';continue;}
     const command=this.input.trim().toUpperCase();this.input='';
     if(command)this.emit('data',(this.command(command,this.now())?'OK ':'ERR ')+command+'\n');
    }else if(!this.discard){
     if(this.input.length>=48||(ch.charCodeAt(0)<32&&ch!=='\t')){this.discard=true;this.input='';this.disarm();this.emit('data','ERR line overflow; DISARMED\n');}
     else this.input+=ch;
    }
   }
  });
 }
 private navigate(now:number){
  if(!this.healthy)this.emergency();
  if(!this.armed||this.estop){this.motion=0;return;}
  if(!this.automatic){if(this.motion!==0&&this.elapsed(now,this.manualAt)>=1200)this.motion=0;return;}
  if(this.cm.some(v=>v<2||v>400)){this.disarm();this.phase='SENSOR_FAULT';return;}
  const [front,left,right]=this.cm;
  if(this.phase==='TURN_DEAD_TIME'||this.phase==='TURNING'){
   if((this.phase==='TURNING'&&this.elapsed(now,this.phaseAt)>=540)||(this.motion===3?left:right)<=45||left<=20||right<=20){
    this.motion=0;this.phase='REASSESS';this.phaseAt=now;this.reassessSequence=this.sequence;
   }return;
  }
  if(this.phase==='SETTLE'||this.phase==='REASSESS'){
   this.motion=0;if(this.elapsed(now,this.phaseAt)<180)return;
   if(this.phase==='REASSESS'&&this.sequence===this.reassessSequence)return;
   if(front>45&&left>20&&right>20){this.phase='CRUISE';this.motion=1;this.attempts=0;return;}
   if(this.attempts>=3){this.disarm();this.phase='TURN_LIMIT';return;}
   if(left>20&&right>20&&(left>45||right>45)){this.motion=left>=right?3:4;this.phase='TURN_DEAD_TIME';++this.attempts;}
   return;
  }
  if(front<=35||left<=20||right<=20){this.motion=0;this.phase='SETTLE';this.phaseAt=now;}
  else this.motion=1;
 }
 private tick(){
  if(this.closed)return;const now=this.now();this.sensors(now);this.navigate(now);
  const requested=this.armed&&!this.estop?this.motion:0;
  if(requested!==this.gateTarget){this.gateTarget=requested;this.gateAt=now;this.applied=0;}
  this.applied=requested!==0&&this.elapsed(now,this.gateAt)>=100?requested:0;
  if(this.phase==='TURN_DEAD_TIME'&&this.applied===this.motion&&this.applied!==0){this.phase='TURNING';this.phaseAt=now;}
  if(this.elapsed(now,this.emitted)<100)return;this.emitted=now;
  const enabled=this.applied!==0&&this.armed&&!this.estop&&this.healthy;
  const nav=this.estop?'ESTOP':['SENSOR_FAULT','TURN_LIMIT'].includes(this.phase)?this.phase:!this.armed?'DISARMED':this.automatic?this.phase:'MANUAL';
  const telemetry:Telemetry={v:1,fw:'rover-sim-v1',ms:now,armed:this.armed,auto:this.automatic,estop:this.estop,healthy:this.healthy,requested:this.motion,applied:enabled?this.applied:0,en:enabled,brushReq:this.brush,conveyorReq:this.conveyor,brush:enabled&&this.applied===1&&this.brush,conveyor:enabled&&this.applied===1&&this.conveyor,nav,cm:[...this.cm],age:[0,0,0],mode:'SIMULATION',motorCapable:true,simulated:true};
  this.emit('data','TEL '+JSON.stringify(telemetry)+'\n');
 }
 async close(){if(this.closed)return;this.closed=true;this.disarm();clearTimeout(this.startup);clearInterval(this.timer);}
}
