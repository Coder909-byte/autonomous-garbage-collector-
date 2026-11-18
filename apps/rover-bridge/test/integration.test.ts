import {afterEach,it,expect} from 'vitest';
import {WebSocket} from 'ws';
import http from 'node:http';
import {vi} from 'vitest';
import {makeServer} from '../src/server';
import {Hardware} from '../src/transports';
import {MockSerial,sample} from './fixtures';
import type {BridgeState} from '../../../packages/protocol/index';
const runtimes:ReturnType<typeof makeServer>[]=[];
afterEach(async()=>{for(const r of runtimes.splice(0))await r.close();});
const waitFor=async(test:()=>boolean,ms=4000)=>{const start=Date.now();while(!test()){if(Date.now()-start>ms)throw Error('Condition timed out');await new Promise(r=>setTimeout(r,25));}};
it('full WebSocket → bridge → portable virtual controller → telemetry path',async()=>{
 const r=makeServer();runtimes.push(r);await new Promise<void>(ok=>r.server.listen(0,'127.0.0.1',ok));const port=(r.server.address() as {port:number}).port;
 const physicalOpen=vi.spyOn(Hardware,'open').mockRejectedValue(Error('Physical serial forbidden in simulator test'));
 const socket=new WebSocket(`ws://127.0.0.1:${port}/api/control`,{origin:`http://127.0.0.1:${port}`});let state:BridgeState|null=null;
 socket.on('message',b=>{state=JSON.parse(b.toString());});await new Promise<void>(ok=>socket.on('open',ok));
 const send=(value:unknown)=>socket.send(JSON.stringify(value));send({type:'connect',simulation:true,scenario:'clear'});
 await waitFor(()=>!!state?.protocolReady&&!!state.telemetry&&!state.telemetry.armed);send({type:'command',command:'ARM'});await waitFor(()=>!!state?.telemetry?.armed);
 send({type:'command',command:'CLEAN ON'});await waitFor(()=>!!state?.telemetry?.brushReq);expect(state!.telemetry?.brush).toBe(false);
 send({type:'hold',direction:'F'});const timer=setInterval(()=>send({type:'hold',direction:'F'}),80);
 await waitFor(()=>state?.telemetry?.applied===1);expect(state!.telemetry?.brush).toBe(true);clearInterval(timer);
 await waitFor(()=>state?.telemetry?.applied===0);expect(state!.intent).toBe(null);
 send({type:'command',command:'ESTOP'});await waitFor(()=>!!state?.telemetry?.estop);expect(state!.telemetry?.armed).toBe(false);
 socket.close();await waitFor(()=>!r.bridge.state.connected);
 expect(physicalOpen).not.toHaveBeenCalled();physicalOpen.mockRestore();
 const url=`http://127.0.0.1:${port}/api/diagnostics`;
 const recent=await (await fetch(url)).json();expect(recent.count).toBeGreaterThan(0);expect(recent.samples.every((r:{source:string})=>r.source==='simulation')).toBe(true);
 const json=await fetch(url+'/export?format=json');expect(json.headers.get('content-disposition')).toContain('.json');const exported=await json.json();expect(exported.schema).toBe(1);expect(exported.records.some((r:{event:string;telemetry?:{estop:boolean}})=>r.event==='emergency'&&r.telemetry?.estop)).toBe(true);
 const csv=await fetch(url+'/export?format=csv');expect(csv.headers.get('content-type')).toContain('text/csv');expect(await csv.text()).toContain('"SIMULATION"');expect((await fetch(url+'/export?format=xml')).status).toBe(400);
});
it('rejects cross-origin requests, DNS rebinding and unauthenticated writes',async()=>{
 const r=makeServer();runtimes.push(r);await new Promise<void>(ok=>r.server.listen(0,'127.0.0.1',ok));const port=(r.server.address() as {port:number}).port,url=`http://127.0.0.1:${port}`;
 expect((await fetch(url+'/api/state')).status).toBe(200);
 expect((await fetch(url+'/api/state',{headers:{Origin:'https://evil.example'}})).status).toBe(403);
 expect((await fetch(url+'/api/camera',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})).status).toBe(403);
 expect(await new Promise<number>(ok=>{http.get(url+'/api/state',{headers:{Host:'evil.example'}},res=>{res.resume();ok(res.statusCode!);});})).toBe(403);
 const ws=new WebSocket(`ws://127.0.0.1:${port}/api/control`,{origin:'https://evil.example'});expect(await new Promise<string>(ok=>{ws.on('unexpected-response',(_req,res)=>{ok(String(res.statusCode));res.resume();});ws.on('error',()=>{});})).toBe('403');ws.terminate();
});
it.each(['obstacle','sensor-fault','estop'])('reproducible virtual AUTO scenario: %s',async scenario=>{
 const r=makeServer();runtimes.push(r);const {Simulation}=await import('../src/transports');await r.bridge.connect(async()=>new Simulation(scenario),true,'SIMULATION');
 await waitFor(()=>r.bridge.ready());r.bridge.command('ARM');await waitFor(()=>!!r.bridge.state.telemetry?.armed);r.bridge.command('AUTO');
 await waitFor(()=>r.bridge.state.telemetry?.applied===1);
 if(scenario==='obstacle'){
  await waitFor(()=>['SETTLE','TURN_DEAD_TIME','TURNING','REASSESS'].includes(r.bridge.state.telemetry?.nav??''),4500);
  expect(r.bridge.state.telemetry?.cm[0]).toBe(25);
  await waitFor(()=>!r.bridge.state.telemetry?.armed||r.bridge.state.telemetry?.cm[0]===120,4500);
 }else{
  await waitFor(()=>!r.bridge.state.telemetry?.armed,4500);
  expect(r.bridge.state.telemetry?.applied).toBe(0);
  expect(r.bridge.state.telemetry?.nav).toBe(scenario==='estop'?'ESTOP':'SENSOR_FAULT');
 }
});
it('WebSocket routes permitted physical commands to the selected COM7 mock and retains inhibition',async()=>{
 const r=makeServer();runtimes.push(r);await new Promise<void>(ok=>r.server.listen(0,'127.0.0.1',ok));
 const port=(r.server.address() as {port:number}).port,usb=new MockSerial();
 const open=vi.spyOn(Hardware,'open').mockResolvedValue(usb as unknown as Hardware);
 const socket=new WebSocket(`ws://127.0.0.1:${port}/api/control`,{origin:`http://127.0.0.1:${port}`});
 await new Promise<void>(ok=>socket.on('open',ok));const send=(value:unknown)=>socket.send(JSON.stringify(value));
 try{
  send({type:'connect',simulation:false,port:'COM7'});await waitFor(()=>r.bridge.state.connected);expect(open).toHaveBeenCalledWith('COM7');
  usb.ack();const permitted={...sample,mode:'MOTOR_OPERATION' as const,motorCapable:true,commissioningReady:true,inhibit:'NONE' as const,armed:false,healthy:false,nav:'DISARMED'};
  usb.telemetry(permitted);send({type:'command',command:'ARM'});await waitFor(()=>usb.writes.includes('ARM\n'));
  usb.telemetry({...permitted,armed:true,nav:'MANUAL'});
  for(const direction of ['F','B','L','R']){
   send({type:'hold',direction});await waitFor(()=>usb.writes.includes(direction+'\n'));
   send({type:'release'});await waitFor(()=>r.bridge.state.intent===null);
  }
  usb.telemetry({...permitted,commissioningReady:false,inhibit:'COMMISSIONING_REQUIRED'});
  const before=usb.writes.filter(v=>v==='ARM\n').length;
  send({type:'command',command:'ARM'});await waitFor(()=>!!r.bridge.state.error?.includes('COMMISSIONING_REQUIRED'));
  expect(usb.writes.filter(v=>v==='ARM\n')).toHaveLength(before);expect(r.bridge.state.telemetry?.en).toBe(false);
  send({type:'disconnect'});await waitFor(()=>!r.bridge.state.connected&&!r.bridge.state.disconnecting);
  const closedWrites=usb.writes.length;send({type:'connect',simulation:true,scenario:'clear'});await waitFor(()=>r.bridge.ready());
  expect(r.bridge.state.telemetry).toMatchObject({mode:'SIMULATION',simulated:true,armed:false});
  send({type:'command',command:'ARM'});await waitFor(()=>!!r.bridge.state.telemetry?.armed);
  expect(usb.writes).toHaveLength(closedWrites);expect(open).toHaveBeenCalledTimes(1);
 }finally{socket.close();open.mockRestore();}
});
