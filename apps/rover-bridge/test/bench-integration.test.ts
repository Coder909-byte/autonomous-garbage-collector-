import {spawn} from 'node:child_process';
import {EventEmitter} from 'node:events';
import {afterEach,it,expect} from 'vitest';
import {Bridge} from '../src/bridge';
import type {Transport} from '../src/transports';

class BenchFirmware extends EventEmitter implements Transport {
 private child=spawn('build/rover-bench-sim');
 constructor(){
  super();this.child.stdout.on('data',b=>this.emit('data',b.toString()));
  this.child.on('error',e=>this.emit('fault',e));this.child.on('exit',()=>this.emit('lost'));
 }
 write(data:string){this.child.stdin.write(data);}
 async close(){this.child.stdin.end();this.child.kill();}
}
const bridges:Bridge[]=[];
afterEach(async()=>{for(const b of bridges.splice(0))await b.dispose();});
async function waitFor(test:()=>boolean){
 const start=Date.now();while(!test()){if(Date.now()-start>2500)throw Error('Bench firmware telemetry timed out');await new Promise(r=>setTimeout(r,20));}
}
it('actual bench firmware → TEL → USB bridge readiness, real LOW feedback, sensors, ESTOP and RESET',async()=>{
 const bridge=new Bridge();bridges.push(bridge);await bridge.connect(async()=>new BenchFirmware(),false,'HOST-FIRMWARE-MOCK');
 await waitFor(()=>bridge.ready());
 expect(bridge.state.telemetry).toMatchObject({mode:'USB_BENCH_DIAGNOSTIC',motorCapable:false,healthy:false,armed:false,en:false,nav:'DISARMED',cm:[120,100,70]});
 expect(()=>bridge.command('ARM')).toThrow('motor control disabled');expect(()=>bridge.hold('F')).toThrow();
 bridge.command('ESTOP');await waitFor(()=>!!bridge.state.telemetry?.estop);
 expect(bridge.state.telemetry).toMatchObject({armed:false,en:false,applied:0,nav:'ESTOP'});
 bridge.command('RESET');await waitFor(()=>bridge.state.telemetry?.estop===false);
 expect(bridge.state.telemetry).toMatchObject({healthy:false,armed:false,en:false,applied:0});
});
