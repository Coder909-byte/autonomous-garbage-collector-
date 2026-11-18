import {afterEach,it,expect} from 'vitest';
import {telemetry,motorControlAvailable,motorOutputState,feedbackAllowsControl,type Telemetry,type Command} from '../../../packages/protocol/index';
import {Bridge} from '../src/bridge';
import {MockSerial,sample} from './fixtures';

const pending:Telemetry={...sample,armed:false,healthy:false,nav:'DISARMED',mode:'MOTOR_OPERATION',motorCapable:true,commissioningReady:false,inhibit:'COMMISSIONING_REQUIRED'};
const qualified:Telemetry={...pending,commissioningReady:true,inhibit:'NONE'};
const bridges:Bridge[]=[];
afterEach(async()=>{for(const b of bridges.splice(0))await b.dispose();});
async function connect(t:Telemetry=pending){
 let now=1000;const b=new Bridge(()=>now);bridges.push(b);const d=new MockSerial();
 await b.connect(async()=>d,false,'HOST-MOTOR-MOCK');d.ack();d.telemetry(t);
 return {b,d,setNow:(value:number)=>{now=value;}};
}
it('accepts explicit inhibited motor mode with raw GPIO27 LOW and live sensors',()=>{
 expect(telemetry(pending)).toEqual(pending);expect(motorControlAvailable(pending)).toBe(false);
 expect(feedbackAllowsControl(pending)).toBe(true);expect(motorOutputState(pending)).toContain('COMMISSIONING REQUIRED');
});
it.each([{commissioningReady:undefined},{inhibit:undefined},{inhibit:'BYPASS'},{commissioningReady:false,inhibit:'NONE'},{commissioningReady:true,inhibit:'COMMISSIONING_REQUIRED'},{armed:true},{auto:true},{requested:1},{en:true,applied:1},{brushReq:true}])('rejects inconsistent commissioning metadata %j',change=>{
 expect(()=>telemetry({...pending,...change})).toThrow();
});
it('accepts commanded outputs with real feedback LOW only in released MOTOR_OPERATION',()=>{
 const moving={...qualified,armed:true,en:true,requested:1,applied:1,nav:'MANUAL'};
 expect(telemetry(moving).healthy).toBe(false);expect(motorOutputState(moving)).toBe('COMMANDED ACTIVE');
 expect(()=>telemetry({...sample,...moving,mode:'PROTECTED_ROVER',commissioningReady:undefined,inhibit:undefined})).toThrow();
});
it.each(['ARM','AUTO','CLEAN ON','BRUSH ON','CONVEYOR ON'] as Command[])('inhibits %s until commissioning is complete',async command=>{
 const {b,d}=await connect();expect(()=>b.command(command)).toThrow('COMMISSIONING_REQUIRED');expect(d.writes).not.toContain(command+'\n');
 expect(()=>b.hold('F')).toThrow();
});
it('allows ARM/hold and explicit software reset with LOW GPIO27 in released mode',async()=>{
 const {b,d}=await connect(qualified);b.command('ARM');expect(d.writes.at(-1)).toBe('ARM\n');
 d.telemetry({...qualified,armed:true,nav:'MANUAL'});b.hold('F');expect(d.writes.at(-1)).toBe('F\n');
 b.command('ESTOP');d.telemetry({...qualified,estop:true,nav:'ESTOP'});b.command('RESET');expect(d.writes.at(-1)).toBe('RESET\n');
});
it('renews the motor command lease at 200 ms intervals only for fresh MOTOR_OPERATION',async()=>{
 const {b,d,setNow}=await connect(qualified);b.watchdog();expect(d.writes.at(-1)).toBe('HEARTBEAT\n');
 const count=d.writes.length;setNow(1199);b.watchdog();expect(d.writes.length).toBe(count);
 setNow(1200);b.watchdog();expect(d.writes.length).toBe(count+1);setNow(2300);b.watchdog();expect(d.writes.length).toBe(count+1);
 expect(()=>b.command('HEARTBEAT')).toThrow('allowlist');
});
it('never sends new heartbeat commands to protected, bench or legacy firmware',async()=>{
 for(const t of [sample,{...sample,mode:'PROTECTED_ROVER',motorCapable:true} as Telemetry,{...pending,mode:'USB_BENCH_DIAGNOSTIC',motorCapable:false,commissioningReady:undefined,inhibit:undefined} as Telemetry]){
  const {b,d}=await connect({...t,armed:false,nav:'DISARMED'});b.watchdog();expect(d.writes).not.toContain('HEARTBEAT\n');
 }
});
it('rejects output claims during timeout or PWM faults',()=>{
 for(const inhibit of ['COMMAND_TIMEOUT','PWM_FAULT'] as const){
  expect(motorControlAvailable({...qualified,inhibit})).toBe(false);
  expect(()=>telemetry({...qualified,inhibit,armed:true})).toThrow();
 }
});
