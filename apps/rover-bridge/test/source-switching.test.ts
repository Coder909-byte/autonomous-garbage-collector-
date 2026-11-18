import {afterEach,expect,it,vi} from 'vitest';
import {Bridge} from '../src/bridge';
import {Simulation} from '../src/simulator';
import {MockSerial,sample} from './fixtures';
import {isState,telemetry,type Telemetry} from '../../../packages/protocol/index';
const bridges:Bridge[]=[];
afterEach(async()=>{for(const b of bridges.splice(0))await b.dispose();vi.useRealTimers();});
const motor:Telemetry={...sample,mode:'MOTOR_OPERATION',motorCapable:true,commissioningReady:true,inhibit:'NONE',armed:false,healthy:false,nav:'DISARMED'};
const synthetic:Telemetry={...sample,fw:'rover-sim-v1',mode:'SIMULATION',motorCapable:true,simulated:true};
it('armed simulation never transfers commands or telemetry into a COM7 session',async()=>{
 vi.useFakeTimers();const b=new Bridge();bridges.push(b);const old=new Simulation('clear');
 await b.connect(async()=>old,true,'SIMULATION');await vi.advanceTimersByTimeAsync(200);expect(b.ready()).toBe(true);
 b.command('ARM');await vi.advanceTimersByTimeAsync(100);b.hold('F');await vi.advanceTimersByTimeAsync(200);expect(b.state.telemetry?.applied).toBe(1);
 await b.disconnect();const usb=new MockSerial();await b.connect(async()=>usb,false,'COM7');
 expect(usb.writes).toEqual(['S\n','DISARM\n']);expect(b.state).toMatchObject({intent:null,telemetry:null,protocolReady:false,simulation:false});
 old.emit('data','TEL '+JSON.stringify(synthetic)+'\n');expect(b.state.telemetry).toBe(null);
 expect(()=>b.hold('F')).toThrow();usb.ack();usb.telemetry(motor);expect(b.ready()).toBe(true);
 expect(b.state.telemetry?.armed).toBe(false);expect(usb.writes).not.toContain('ARM\n');expect(usb.writes).not.toContain('F\n');
 b.command('ARM');expect(usb.writes.at(-1)).toBe('ARM\n');usb.telemetry({...motor,armed:true,nav:'MANUAL'});
 for(const direction of ['F','B','L','R'] as const){b.hold(direction);expect(usb.writes.at(-1)).toBe(direction+'\n');b.stopHold();}
 usb.telemetry({...motor,commissioningReady:false,inhibit:'COMMISSIONING_REQUIRED'});
 expect(()=>b.command('ARM')).toThrow('COMMISSIONING_REQUIRED');expect(()=>b.hold('F')).toThrow();expect(b.state.telemetry?.en).toBe(false);
});
it('serial close completes before a new owner can connect',async()=>{
 const b=new Bridge();bridges.push(b);const usb=new MockSerial();let finish!:()=>void;
 usb.close=()=>new Promise<void>(resolve=>{finish=resolve;});await b.connect(async()=>usb,false,'COM7');
 const closing=b.disconnect();expect(b.state.disconnecting).toBe(true);
 await expect(b.connect(async()=>new MockSerial(),true,'SIMULATION')).rejects.toThrow('disconnect first');
 finish();await closing;expect(b.state.disconnecting).toBe(false);
});
it('synchronous acknowledgements and READY do not corrupt parsing or leave pending commands',async()=>{
 let now=1000;const b=new Bridge(()=>now);bridges.push(b);const usb=new MockSerial();
 usb.write=(value:string)=>{usb.writes.push(value);usb.emit('data','OK '+value);};
 await b.connect(async()=>usb,false,'COM7');usb.emit('data','READY DISARMED\n');usb.telemetry(motor);
 expect(b.ready()).toBe(true);now=3200;usb.telemetry(motor);b.watchdog();expect(b.state.connected).toBe(true);
 expect(b.state.logs.some(l=>l.kind==='ACK'&&l.text==='OK DISARM')).toBe(true);
 expect(b.state.logs.some(l=>l.kind==='ERROR')).toBe(false);
});
it.each([false,true])('source mismatch revokes drive readiness (simulation=%s)',async simulation=>{
 const b=new Bridge();bridges.push(b);const usb=new MockSerial();await b.connect(async()=>usb,simulation,simulation?'SIMULATION':'COM7');usb.ack();
 usb.telemetry(simulation?motor:synthetic);expect(b.ready()).toBe(false);expect(b.state.telemetry).toBe(null);
 expect(usb.writes).toContain('DISARM\n');expect(b.state.error).toContain('source mismatch');
 expect(isState({...b.state,telemetry:simulation?motor:synthetic})).toBe(false);
});
it('synthetic telemetry cannot impersonate a commissioned physical operating mode',()=>{
 expect(()=>telemetry({...motor,simulated:true})).toThrow();expect(()=>telemetry({...synthetic,simulated:false})).toThrow();
 expect(()=>telemetry({...synthetic,commissioningReady:true,inhibit:'NONE'})).toThrow();
});
