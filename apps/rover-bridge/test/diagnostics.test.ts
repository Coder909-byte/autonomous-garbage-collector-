import {it,expect} from 'vitest';
import {Diagnostics} from '../src/diagnostics';
import {Bridge} from '../src/bridge';
import {sample,MockSerial} from './fixtures';

it('retains distinct hardware/simulation sessions and immutable telemetry after disconnect',async()=>{
 const b=new Bridge(()=>1700000000000);const hardware=new MockSerial();
 try{
  await b.connect(async()=>hardware,false,'/dev/mock');hardware.ack();hardware.telemetry({armed:false,nav:'DISARMED'});
  hardware.telemetry({armed:false,estop:true,healthy:false,nav:'ESTOP'});hardware.emit('lost');await Promise.resolve();
  const simulation=new MockSerial();await b.connect(async()=>simulation,true,'SIMULATION');simulation.ack();simulation.telemetry({armed:false,nav:'DISARMED'});
  const records=b.diagnostics.snapshot().records,telemetry=records.filter(r=>r.event==='telemetry');
  expect(telemetry.map(r=>r.source)).toEqual(['hardware','hardware','simulation']);expect(telemetry[0].session).not.toBe(telemetry[2].session);
  expect(records.some(r=>r.event==='emergency'&&r.telemetry?.estop&&r.source==='hardware')).toBe(true);
  expect(records.some(r=>r.event==='communication'&&r.message.includes('disconnected'))).toBe(true);
  expect(records.some(r=>r.event==='connection'&&r.message.includes('closed'))).toBe(true);
  expect(telemetry[0].timestamp).toBe('2023-11-14T22:13:20.000Z');
 }finally{await b.dispose();}
});
it('bounds recording and reports evictions without mixing recent chart sessions',()=>{
 const d=new Diagnostics(3);d.begin(true,'SIMULATION');for(let i=0;i<5;i++)d.record(i,'RX','sample',{...sample,ms:i});
 expect(d.snapshot()).toMatchObject({count:3,capacity:3,dropped:2});expect(d.recent().samples.map(r=>r.telemetry?.ms)).toEqual([2,3,4]);
});
it('exports CSV with named applied/requested outputs, invalid ranges, escaping and formula protection',()=>{
 const d=new Diagnostics();d.begin(true,'SIMULATION');const t={...sample,requested:1,cm:[-1,20,30] as [number,number,number]};
 d.record(0,'RX','line, "quoted"\nnext',t);t.cm[0]=120;d.record(1,'ERROR','=HYPERLINK("bad")');
 const csv=d.csv();expect(csv).toContain('"timestamp_utc"');expect(csv).toContain('"requested","applied"');expect(csv).toContain('"FORWARD","STOPPED"');expect(csv).toContain('"-1","20","30"');expect(csv).toContain('"line, ""quoted""\nnext"');expect(csv).toContain('"\'=HYPERLINK(""bad"")"');
 expect(d.snapshot().records[0].telemetry?.cm[0]).toBe(-1);expect(JSON.parse(JSON.stringify(d.snapshot())).records[0].source).toBe('simulation');
});
