import {afterEach,expect,it,vi} from 'vitest';
import {Simulation} from '../src/simulator';
import {parseLine,type Telemetry} from '../../../packages/protocol/index';

const devices:Simulation[]=[];
afterEach(async()=>{for(const d of devices.splice(0))await d.close();vi.useRealTimers();});
it('portable simulator boots independently, arms explicitly and applies all four manual directions',async()=>{
 vi.useFakeTimers();const device=new Simulation('clear');devices.push(device);let t:Telemetry|undefined;
 device.on('data',(line:string)=>{const p=parseLine(line.trim());if(p.kind==='telemetry')t=p.data;});
 await vi.advanceTimersByTimeAsync(100);
 expect(t).toMatchObject({mode:'SIMULATION',simulated:true,fw:'rover-sim-v1',armed:false,en:false});
 expect(t).not.toHaveProperty('commissioningReady');expect(t).not.toHaveProperty('inhibit');
 device.write('F\n');await vi.advanceTimersByTimeAsync(100);expect(t?.applied).toBe(0);
 device.write('ARM\n');await vi.advanceTimersByTimeAsync(100);expect(t).toMatchObject({armed:true,en:false,applied:0});
 for(const [command,motion] of [['F',1],['B',2],['L',3],['R',4]] as const){
  device.write(command+'\n');await vi.advanceTimersByTimeAsync(200);expect(t).toMatchObject({requested:motion,applied:motion,en:true});
  device.write('S\n');await vi.advanceTimersByTimeAsync(100);expect(t).toMatchObject({requested:0,applied:0,en:false});
 }
 device.write('F\n');await vi.advanceTimersByTimeAsync(1400);expect(t?.applied).toBe(0);
 device.write('ESTOP\nARM\n');await vi.advanceTimersByTimeAsync(100);expect(t).toMatchObject({armed:false,estop:true,en:false});
 device.write('RESET\nARM\n');await vi.advanceTimersByTimeAsync(100);expect(t).toMatchObject({armed:true,estop:false,en:false});
 await device.close();const next=new Simulation('clear');devices.push(next);
 next.on('data',(line:string)=>{const p=parseLine(line.trim());if(p.kind==='telemetry')t=p.data;});
 await vi.advanceTimersByTimeAsync(100);expect(t).toMatchObject({armed:false,applied:0,simulated:true});
});
