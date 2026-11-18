import {spawn} from 'node:child_process';
import {EventEmitter} from 'node:events';
import {afterEach,it,expect} from 'vitest';
import {Bridge} from '../src/bridge';
import type {Transport} from '../src/transports';

class MotorFirmware extends EventEmitter implements Transport {
 private child;dropHeartbeat=false;
 constructor(kind:'pending'|'qualified-test'|'bench-release'){
  super();this.child=spawn('build/rover-motor-'+kind+'-sim');
  this.child.stdout.on('data',b=>this.emit('data',b.toString()));
  this.child.on('error',e=>this.emit('fault',e));this.child.on('exit',()=>this.emit('lost'));
 }
 write(data:string){if(!(this.dropHeartbeat&&data==='HEARTBEAT\n'))this.child.stdin.write(data);}
 async close(){this.child.stdin.end();this.child.kill();}
}
const bridges:Bridge[]=[];
afterEach(async()=>{for(const b of bridges.splice(0))await b.dispose();});
async function waitFor(test:()=>boolean){const start=Date.now();while(!test()){if(Date.now()-start>4000)throw Error('Motor host-firmware condition timed out');await new Promise(r=>setTimeout(r,20));}}
it('real pending adapter → TEL → bridge preserves sensors and blocks drive',async()=>{
 const b=new Bridge();bridges.push(b);await b.connect(async()=>new MotorFirmware('pending'),false,'HOST-MOTOR-PENDING');
 await waitFor(()=>b.ready());expect(b.state.telemetry).toMatchObject({mode:'MOTOR_OPERATION',healthy:false,commissioningReady:false,inhibit:'COMMISSIONING_REQUIRED',cm:[120,100,70]});
 expect(()=>b.command('ARM')).toThrow('COMMISSIONING_REQUIRED');b.command('ESTOP');await waitFor(()=>!!b.state.telemetry?.estop);
 b.command('RESET');await waitFor(()=>b.state.telemetry?.estop===false);expect(b.state.telemetry?.en).toBe(false);
});
it('host-only released adapter drives/cleans/AUTO with heartbeats, then disarms when commands stop',async()=>{
 const b=new Bridge();bridges.push(b);const device=new MotorFirmware('qualified-test');await b.connect(async()=>device,false,'HOST-QUALIFICATION-FIXTURE');
 await waitFor(()=>b.ready());b.command('ARM');await waitFor(()=>!!b.state.telemetry?.armed);b.command('CLEAN ON');b.command('AUTO');
 await waitFor(()=>b.state.telemetry?.applied===1);expect(b.state.telemetry).toMatchObject({healthy:false,en:true,brush:true,conveyor:true});
 await new Promise(r=>setTimeout(r,1500));expect(b.state.telemetry?.en).toBe(true);
 device.dropHeartbeat=true;await waitFor(()=>b.state.telemetry?.inhibit==='COMMAND_TIMEOUT');
 expect(b.state.telemetry).toMatchObject({armed:false,en:false,applied:0,brush:false,conveyor:false,auto:false});
},15000);
it('bench-release firmware is unlocked: ARM, hold forward, release stops, command loss disarms',async()=>{
 const b=new Bridge();bridges.push(b);const device=new MotorFirmware('bench-release');await b.connect(async()=>device,false,'HOST-BENCH-RELEASE');
 await waitFor(()=>b.ready());expect(b.state.telemetry).toMatchObject({mode:'MOTOR_OPERATION',commissioningReady:true,inhibit:'NONE',armed:false,en:false});
 b.command('ARM');await waitFor(()=>!!b.state.telemetry?.armed);
 b.hold('F');const held=setInterval(()=>b.hold('F'),100);
 try{await waitFor(()=>b.state.telemetry?.applied===1);expect(b.state.telemetry).toMatchObject({en:true,inhibit:'NONE'});}finally{clearInterval(held);}
 b.stopHold();await waitFor(()=>b.state.telemetry?.applied===0);expect(b.state.telemetry).toMatchObject({armed:true,en:false});
 device.dropHeartbeat=true;await waitFor(()=>b.state.telemetry?.inhibit==='COMMAND_TIMEOUT');expect(b.state.telemetry?.armed).toBe(false);
},15000);
