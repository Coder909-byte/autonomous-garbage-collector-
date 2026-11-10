import express from 'express';
import { createServer } from 'node:http';
import { WebSocketServer } from 'ws';
import { fileURLToPath } from 'node:url';
import { dirname,resolve } from 'node:path';
import { existsSync } from 'node:fs';
import { Bridge } from './bridge.js';
import { Hardware,Simulation,ports } from './transports.js';
import { cameraAddress,proxyCamera } from './camera.js';
let root=dirname(fileURLToPath(import.meta.url));while(!existsSync(resolve(root,'include/rover_control.h'))&&dirname(root)!==root)root=dirname(root);
process.env.ROVER_ROOT=root;
export function makeServer(bridge=new Bridge(),testPort?:number){
 const app=express();const server=createServer(app);const wss=new WebSocketServer({noServer:true,maxPayload:1024});let client:import('ws').WebSocket|null=null;let cameraIP='';
 const validOrigin=(origin:string|undefined)=>{
  const p=testPort??(server.address() as import('node:net').AddressInfo|null)?.port??8787;
  return !!origin&&[`http://127.0.0.1:${p}`,`http://localhost:${p}`,'http://127.0.0.1:5173','http://localhost:5173'].includes(origin);
 };
 const validHost=(host:string|undefined)=>{
  const p=testPort??(server.address() as import('node:net').AddressInfo|null)?.port??8787;
  return host===`127.0.0.1:${p}`||host===`localhost:${p}`;
 };
 app.disable('x-powered-by');app.use((req,res,next)=>{
  if(!validHost(req.headers.host))return void res.status(403).json({error:'Loopback Host required'});
  res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');
  res.setHeader('Content-Security-Policy',"default-src 'self'; img-src 'self' blob:; connect-src 'self'; style-src 'self'; frame-ancestors 'none'");
  if(req.headers.origin&&!validOrigin(req.headers.origin))return void res.status(403).json({error:'Local operator origin required'});
  if(req.path.startsWith('/api/')&&req.method!=='GET'&&(!validOrigin(req.headers.origin)||req.headers['x-rover-client']!=='dashboard'))return void res.status(403).json({error:'Local dashboard request required'});
  next();
 });
 app.use(express.json({limit:'1kb'}));
 app.get('/api/state',(_req,res)=>res.json(bridge.state));
 app.get('/api/ports',async(_req,res)=>{try{res.json(await ports());}catch(e){res.status(503).json({error:String(e)});}});
 app.post('/api/camera',(req,res)=>{try{cameraIP=cameraAddress(req.body.ip);res.json({ip:cameraIP});}catch(e){res.status(400).json({error:String(e)});}});
 app.all('/api/camera/:endpoint',(req,res)=>{
  try{if(!cameraIP)throw Error('Camera disconnected: configure address first');
   if(req.params.endpoint==='settings'&&req.method!=='POST')throw Error('Settings require POST');
   if(req.params.endpoint!=='settings'&&req.method!=='GET')throw Error('Camera endpoint requires GET');
   proxyCamera(cameraIP,String(req.params.endpoint),req,res);
  }catch(e){res.status(400).json({error:String(e)});}
 });
 app.use(express.static(resolve(root,'apps/rover-dashboard/dist')));
 app.use((err:Error,_req:express.Request,res:express.Response,_next:express.NextFunction)=>res.status(400).json({error:err.message}));
 server.on('upgrade',(req,socket,head)=>{
  if(req.url!=='/api/control'||!validHost(req.headers.host)||!validOrigin(req.headers.origin)||client){socket.write('HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n');socket.destroy();return;}
  wss.handleUpgrade(req,socket,head,ws=>wss.emit('connection',ws,req));
 });
 const publish=()=>{if(client?.readyState===1){if(client.bufferedAmount>65536){client.terminate();return;}client.send(JSON.stringify(bridge.state));}};
 bridge.on('state',publish);
 wss.on('connection',ws=>{
  client=ws;publish();let rateAt=Date.now(),count=0,alive=true;
  ws.on('pong',()=>{alive=true;});const health=setInterval(()=>{if(!alive){ws.terminate();return;}alive=false;ws.ping();},2000);
  ws.on('message',async raw=>{
   try{
    if(Date.now()-rateAt>=1000){count=0;rateAt=Date.now();}if(++count>50)throw Error('Control message rate exceeded');
    const m=JSON.parse(raw.toString());if(!m||typeof m!=='object')throw Error('Invalid message');
    switch(m.type){
     case 'connect':
      if(m.simulation!==true&&m.simulation!==false)throw Error('Select hardware or simulation explicitly');
      await bridge.connect(async()=>m.simulation?new Simulation(m.scenario||'clear'):Hardware.open(String(m.port)),m.simulation,m.simulation?'SIMULATION':String(m.port));break;
     case 'disconnect':await bridge.disconnect();break;
     case 'command':bridge.command(m.command);break;
     case 'hold':bridge.hold(m.direction);break;
     case 'release':bridge.stopHold();break;
     default:throw Error('Invalid control message');
    }
   }catch(e){bridge.log('ERROR',String(e));bridge.stopHold();}
  });
  ws.on('close',()=>{clearInterval(health);if(client===ws){client=null;void bridge.disconnect();}});
  ws.on('error',()=>{ws.terminate();});
 });
 return {server,bridge,async close(){client?.terminate();bridge.off('state',publish);await bridge.dispose();wss.close();await new Promise<void>(ok=>server.close(()=>ok()));}};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const runtime=makeServer();runtime.server.listen(8787,'127.0.0.1',()=>console.log('Rover bridge http://127.0.0.1:8787 · local operator only · disarmed on connect'));
 for(const signal of ['SIGINT','SIGTERM'] as const)process.on(signal,()=>void runtime.close().finally(()=>process.exit(0)));
}
