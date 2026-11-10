import {afterEach,it,expect} from 'vitest';
import {WebSocket} from 'ws';
import http from 'node:http';
import {makeServer} from '../src/server';
import type {BridgeState} from '../../../packages/protocol/index';
const runtimes:ReturnType<typeof makeServer>[]=[];
afterEach(async()=>{for(const r of runtimes.splice(0))await r.close();});
const waitFor=async(test:()=>boolean,ms=4000)=>{const start=Date.now();while(!test()){if(Date.now()-start>ms)throw Error('Condition timed out');await new Promise(r=>setTimeout(r,25));}};
it('full WebSocket → bridge → real C++ mock serial → telemetry path',async()=>{
 const r=makeServer();runtimes.push(r);await new Promise<void>(ok=>r.server.listen(0,'127.0.0.1',ok));const port=(r.server.address() as {port:number}).port;
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
});
it('rejects cross-origin requests, DNS rebinding and unauthenticated writes',async()=>{
 const r=makeServer();runtimes.push(r);await new Promise<void>(ok=>r.server.listen(0,'127.0.0.1',ok));const port=(r.server.address() as {port:number}).port,url=`http://127.0.0.1:${port}`;
 expect((await fetch(url+'/api/state')).status).toBe(200);
 expect((await fetch(url+'/api/state',{headers:{Origin:'https://evil.example'}})).status).toBe(403);
 expect((await fetch(url+'/api/camera',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})).status).toBe(403);
 expect(await new Promise<number>(ok=>{http.get(url+'/api/state',{headers:{Host:'evil.example'}},res=>{res.resume();ok(res.statusCode!);});})).toBe(403);
 const ws=new WebSocket(`ws://127.0.0.1:${port}/api/control`,{origin:'https://evil.example'});expect(await new Promise<string>(ok=>{ws.on('unexpected-response',(_req,res)=>{ok(String(res.statusCode));res.resume();});ws.on('error',()=>{});})).toBe('403');ws.terminate();
});
it.each(['obstacle','sensor-fault','estop'])('reproducible C++ AUTO scenario: %s',async scenario=>{
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
