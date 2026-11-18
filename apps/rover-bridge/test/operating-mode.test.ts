import {afterEach,it,expect} from 'vitest';
import {telemetry,parseLine,motorControlAvailable,type Telemetry,type Command} from '../../../packages/protocol/index';
import {Bridge} from '../src/bridge';
import {MockSerial,sample} from './fixtures';

const bench:Telemetry={...sample,armed:false,healthy:false,nav:'DISARMED',mode:'USB_BENCH_DIAGNOSTIC',motorCapable:false};
const bridges:Bridge[]=[];
afterEach(async()=>{for(const b of bridges.splice(0))await b.dispose();});
async function connect(){
 const bridge=new Bridge();bridges.push(bridge);const device=new MockSerial();
 await bridge.connect(async()=>device,false,'USB-BENCH-MOCK');device.ack();device.telemetry(bench);
 return {bridge,device};
}
it('accepts legacy v1, protected and diagnostic TEL without changing existing fields',()=>{
 expect(telemetry(sample)).toEqual(sample);
 expect(telemetry({...sample,mode:'PROTECTED_ROVER',motorCapable:true})).toMatchObject(sample);
 expect(parseLine('TEL '+JSON.stringify(bench))).toEqual({kind:'telemetry',data:bench});
 expect(motorControlAvailable(sample)).toBe(true);expect(motorControlAvailable(bench)).toBe(false);
});
it.each([{mode:'UNKNOWN',motorCapable:false},{mode:'USB_BENCH_DIAGNOSTIC',motorCapable:true},{mode:'PROTECTED_ROVER',motorCapable:false},{mode:'USB_BENCH_DIAGNOSTIC'},{motorCapable:false},{mode:null,motorCapable:false}])('rejects malformed mode metadata %j',change=>{
 expect(()=>telemetry({...sample,armed:false,...change})).toThrow();
});
it.each([{armed:true},{auto:true},{requested:1},{brushReq:true},{conveyorReq:true},{en:true,applied:1},{brush:true},{conveyor:true}])('rejects diagnostic motor authorization/output claims %j',change=>{
 expect(()=>telemetry({...bench,...change})).toThrow();
});
it('completes USB readiness with real LOW feedback, sensor data and no motor authority',async()=>{
 const {bridge}=await connect();expect(bridge.ready()).toBe(true);
 expect(bridge.state.telemetry).toMatchObject({cm:[120,100,70],healthy:false,armed:false,en:false,mode:'USB_BENCH_DIAGNOSTIC'});
});
it.each(['ARM','AUTO','BRUSH ON','CONVEYOR ON','CLEAN ON'] as Command[])('blocks %s at the bridge for diagnostic firmware',async command=>{
 const {bridge,device}=await connect();expect(()=>bridge.command(command)).toThrow('motor control disabled');
 expect(device.writes).not.toContain(command+'\n');expect(()=>bridge.hold('F')).toThrow();
});
it('delivers software ESTOP and explicit RESET with feedback LOW, retaining disabled mode',async()=>{
 const {bridge,device}=await connect();bridge.command('ESTOP');expect(device.writes.at(-1)).toBe('ESTOP\n');
 device.telemetry({...bench,estop:true,nav:'ESTOP'});bridge.command('RESET');expect(device.writes.at(-1)).toBe('RESET\n');
 device.telemetry(bench);expect(bridge.state.telemetry?.healthy).toBe(false);expect(motorControlAvailable(bridge.state.telemetry)).toBe(false);
 bridge.command('DISARM');bridge.command('CLEAN OFF');expect(device.writes.slice(-2)).toEqual(['DISARM\n','CLEAN OFF\n']);
});
it('still refuses RESET with LOW physical feedback in protected firmware',async()=>{
 const {bridge,device}=await connect();device.telemetry({...sample,armed:false,estop:true,healthy:false,nav:'ESTOP',mode:'PROTECTED_ROVER',motorCapable:true});
 expect(()=>bridge.command('RESET')).toThrow('healthy feedback');
});
