import express from 'express';
import { createServer,type IncomingMessage } from 'node:http';
import { WebSocketServer } from 'ws';
import { fileURLToPath } from 'node:url';
import { dirname,resolve } from 'node:path';
import { existsSync } from 'node:fs';
import QRCode from 'qrcode';
import { Bridge } from './bridge.js';
import { Hardware,Network,Simulation,parseWifiTarget,ports } from './transports.js';
import { cameraAddress,proxyCamera } from './camera.js';
import { SHARE_COOKIE,ipv4Host,isLoopback,keyMatches,loadShareKey,requestKey,shareURLs } from './share.js';
let root=dirname(fileURLToPath(import.meta.url));while(!existsSync(resolve(root,'include/rover_control.h'))&&dirname(root)!==root)root=dirname(root);
process.env.ROVER_ROOT=root;
function configuredPort(name:string,fallback:number){const value=process.env[name];if(value===undefined)return fallback;const port=Number(value);if(!/^\d+$/.test(value)||!Number.isInteger(port)||port<1||port>65535)throw Error(`Invalid ${name}`);return port;}
// trustLoopback=false lets tests treat loopback peers as other devices.
export type ShareOptions={key:string;trustLoopback?:boolean};
export const TAKEN_OVER=4001;
export function makeServer(bridge=new Bridge(),testPort?:number,share?:ShareOptions){
 const dashboardPort=configuredPort('ROVER_DASHBOARD_PORT',5173);
 const app=express();const server=createServer(app);const wss=new WebSocketServer({noServer:true,maxPayload:1024});let client:import('ws').WebSocket|null=null;let cameraIP='';
 let viewer:express.Response|null=null;
 const port=()=>testPort??(server.address() as import('node:net').AddressInfo|null)?.port??8787;
 const loopbackHost=(host:string|undefined)=>host===`127.0.0.1:${port()}`||host===`localhost:${port()}`;
 const validHost=(host:string|undefined)=>loopbackHost(host)||(!!share&&ipv4Host(host,port()));
 const validOrigin=(origin:string|undefined,host:string|undefined)=>{
  const p=port();
  if(!origin)return false;
  if([`http://127.0.0.1:${p}`,`http://localhost:${p}`,`http://127.0.0.1:${dashboardPort}`,`http://localhost:${dashboardPort}`].includes(origin))return true;
  return !!share&&ipv4Host(host,p)&&origin===`http://${host}`;
 };
 const local=(req:IncomingMessage)=>!share||(share.trustLoopback!==false&&isLoopback(req.socket.remoteAddress));
 const authorized=(req:IncomingMessage)=>local(req)||keyMatches(share!.key,requestKey(req));
 app.disable('x-powered-by');app.use((req,res,next)=>{
  if(!validHost(req.headers.host))return void res.status(403).json({error:'Loopback Host required'});
  res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');
  res.setHeader('Content-Security-Policy',"default-src 'self'; img-src 'self' blob:; connect-src 'self'; style-src 'self'; frame-ancestors 'none'");
  if(share&&req.method==='GET'&&req.path==='/'&&typeof req.query.key==='string'){
   if(!keyMatches(share.key,req.query.key))return void res.status(401).type('text/plain').send('This link is out of date. Scan the QR code in Mission Control on the operator laptop again.');
   res.setHeader('Set-Cookie',`${SHARE_COOKIE}=${share.key}; Path=/; HttpOnly; SameSite=Strict; Max-Age=31536000`);
   return void res.redirect(302,'/');
  }
  if(share&&!authorized(req)){
   if(req.path.startsWith('/api/'))return void res.status(401).json({error:'Scan the Mission Control QR code to get access'});
   return void res.status(401).type('text/plain').send('Rover Mission Control: join the ROVER-CTRL Wi-Fi, then scan the QR code shown in Mission Control on the operator laptop.');
  }
  if(req.headers.origin&&!validOrigin(req.headers.origin,req.headers.host))return void res.status(403).json({error:'Local operator origin required'});
  // The local vision service is a non-browser loopback client; browsers always send Origin on POST.
  const visionService=req.path==='/api/vision'&&req.method==='POST'&&!req.headers.origin&&req.headers['x-rover-client']==='vision'&&local(req);
  if(req.path.startsWith('/api/')&&req.method!=='GET'&&!visionService&&(!validOrigin(req.headers.origin,req.headers.host)||req.headers['x-rover-client']!=='dashboard'))return void res.status(403).json({error:'Local dashboard request required'});
  next();
 });
 app.use(express.json({limit:'1kb'}));
 app.get('/api/state',(_req,res)=>res.json(bridge.state));
 app.get('/api/control/status',(_req,res)=>res.set('Cache-Control','no-store').json({busy:!!client}));
 app.get('/api/share',(req,res)=>{
  if(!local(req))return void res.status(403).json({error:'Operator laptop only'});
  res.set('Cache-Control','no-store').json({enabled:!!share,urls:share?shareURLs(port(),share.key):[]});
 });
 app.get('/api/share/qr.svg',async(req,res)=>{
  const url=share&&local(req)?shareURLs(port(),share.key)[Number(req.query.i)||0]:undefined;
  if(!url)return void res.status(404).json({error:'No shareable network address'});
  res.set('Cache-Control','no-store').type('image/svg+xml').send(await QRCode.toString(url,{type:'svg',margin:2,errorCorrectionLevel:'M'}));
 });
 app.get('/api/ports',async(_req,res)=>{try{res.json(await ports());}catch(e){res.status(503).json({error:String(e)});}});
 app.get('/api/diagnostics',(_req,res)=>res.set('Cache-Control','no-store').json(bridge.diagnostics.recent()));
 app.get('/api/diagnostics/export',(req,res)=>{
  const format=req.query.format??'json';if(format!=='json'&&format!=='csv')return void res.status(400).json({error:'Use csv or json'});
  res.set('Cache-Control','no-store').attachment(`rover-diagnostics-${Date.now()}.${format}`);
  if(format==='csv')res.type('text/csv').send(bridge.diagnostics.csv());else res.json(bridge.diagnostics.snapshot());
 });
 app.post('/api/vision',(req,res)=>{try{bridge.visionFrame(req.body);res.json({ok:true,vision:bridge.state.vision});}catch(e){res.status(400).json({error:String(e)});}});
 app.post('/api/camera',(req,res)=>{try{cameraIP=cameraAddress(req.body.ip);res.json({ip:cameraIP});}catch(e){res.status(400).json({error:String(e)});}});
 app.all('/api/camera/:endpoint',(req,res)=>{
  try{if(!cameraIP)throw Error('Camera disconnected: configure address first');
   if(req.params.endpoint==='settings'&&req.method!=='POST')throw Error('Settings require POST');
   if(req.params.endpoint!=='settings'&&req.method!=='GET')throw Error('Camera endpoint requires GET');
   if(req.params.endpoint==='stream'){
    // The ESP32-CAM serves one stream at a time: the newest viewer takes it over.
    if(viewer&&viewer!==res)viewer.destroy();
    viewer=res;res.on('close',()=>{if(viewer===res)viewer=null;});
   }
   proxyCamera(cameraIP,String(req.params.endpoint),req,res);
  }catch(e){res.status(400).json({error:String(e)});}
 });
 app.use(express.static(resolve(root,'apps/rover-dashboard/dist')));
 app.use((err:Error,_req:express.Request,res:express.Response,_next:express.NextFunction)=>res.status(400).json({error:err.message}));
 server.on('upgrade',(req,socket,head)=>{
  const url=new URL(req.url??'/','http://bridge');const takeover=url.searchParams.get('takeover')==='1';
  const reject=(status:string)=>{socket.write(`HTTP/1.1 ${status}\r\nConnection: close\r\n\r\n`);socket.destroy();};
  if(url.pathname!=='/api/control'||!validHost(req.headers.host)||!validOrigin(req.headers.origin,req.headers.host)||(share&&!authorized(req)))return reject('403 Forbidden');
  if(client&&!takeover)return reject('409 Conflict');
  if(client){
   // Taking control always stops and disconnects the rover; the new operator reconnects and re-arms.
   const previous=client;client=null;bridge.stopHold();void bridge.disconnect();
   previous.close(TAKEN_OVER,'Control taken by another device');setTimeout(()=>previous.terminate(),500).unref();
  }
  wss.handleUpgrade(req,socket,head,ws=>wss.emit('connection',ws,req));
 });
 const publish=()=>{if(client?.readyState===1){if(client.bufferedAmount>65536){client.terminate();return;}client.send(JSON.stringify(bridge.state));}};
 bridge.on('state',publish);
 wss.on('connection',ws=>{
  client=ws;publish();let rateAt=Date.now(),count=0,alive=true;
  ws.on('pong',()=>{alive=true;});const health=setInterval(()=>{if(!alive){ws.terminate();return;}alive=false;ws.ping();},2000);
  ws.on('message',async raw=>{
   if(client!==ws)return;
   try{
    if(Date.now()-rateAt>=1000){count=0;rateAt=Date.now();}if(++count>50)throw Error('Control message rate exceeded');
    const m=JSON.parse(raw.toString());if(!m||typeof m!=='object')throw Error('Invalid message');
    switch(m.type){
     case 'connect':
      if(m.simulation!==true&&m.simulation!==false)throw Error('Select hardware or simulation explicitly');
      if(!m.simulation&&m.wifi!==undefined){const target=parseWifiTarget(m.wifi);await bridge.connect(async()=>Network.open(`${target.host}:${target.port}`),false,`WIFI ${target.host}:${target.port}`);break;}
      await bridge.connect(async()=>m.simulation?new Simulation(m.scenario||'clear'):Hardware.open(String(m.port)),m.simulation,m.simulation?'SIMULATION':String(m.port));break;
     case 'disconnect':await bridge.disconnect();break;
     case 'command':bridge.command(m.command);break;
     case 'hold':bridge.hold(m.direction);break;
     case 'release':bridge.stopHold();break;
     case 'vision':bridge.visionEnable(m.enabled===true);break;
     default:throw Error('Invalid control message');
    }
   }catch(e){bridge.log('ERROR',String(e));bridge.stopHold();}
  });
  ws.on('close',()=>{clearInterval(health);if(client===ws){client=null;void bridge.disconnect();}});
  ws.on('error',()=>{ws.terminate();});
 });
 return {server,bridge,async close(){client?.terminate();viewer?.destroy();bridge.off('state',publish);await bridge.dispose();wss.close();await new Promise<void>(ok=>server.close(()=>ok()));}};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const port=configuredPort('ROVER_BRIDGE_PORT',8787);
 const sharing=process.argv.includes('--share')||process.env.ROVER_SHARE==='1';
 const share=sharing?{key:loadShareKey(resolve(root,'.rover-share-key'))}:undefined;
 const runtime=makeServer(undefined,undefined,share);
 runtime.server.listen(port,sharing?'0.0.0.0':'127.0.0.1',async()=>{
  console.log(`Rover bridge http://127.0.0.1:${port} · ${sharing?'shared on the local network':'local operator only'} · disarmed on connect`);
  if(!share)return;
  const urls=shareURLs(port,share.key);
  if(!urls.length){console.log('No network address yet. Join the ROVER-CTRL Wi-Fi; Mission Control shows the QR code once connected.');return;}
  console.log('Other phones/laptops: join the ROVER-CTRL Wi-Fi, then scan this QR code or open:');
  for(const url of urls)console.log('  '+url);
  console.log(await QRCode.toString(urls[0],{type:'terminal',small:true}));
 });
 for(const signal of ['SIGINT','SIGTERM'] as const)process.on(signal,()=>void runtime.close().finally(()=>process.exit(0)));
}
