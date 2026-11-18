import {afterEach,it,expect} from 'vitest';
import {WebSocket} from 'ws';
import http from 'node:http';
import {makeServer,TAKEN_OVER} from '../src/server';
import {cookieValue,ipv4Host,keyMatches} from '../src/share';
const KEY='test-share-key-0123456789abcdef';
const runtimes:ReturnType<typeof makeServer>[]=[];
afterEach(async()=>{for(const r of runtimes.splice(0))await r.close();});
async function start(share?:Parameters<typeof makeServer>[2]){
 const r=makeServer(undefined,undefined,share);runtimes.push(r);await new Promise<void>(ok=>r.server.listen(0,'127.0.0.1',ok));
 return {r,port:(r.server.address() as {port:number}).port};
}
function get(port:number,path:string,headers:Record<string,string>={},method='GET',body?:string){
 return new Promise<{status:number;headers:http.IncomingHttpHeaders;body:string}>((ok,fail)=>{
  const req=http.request({host:'127.0.0.1',port,path,method,headers},res=>{let text='';res.on('data',b=>text+=b);res.on('end',()=>ok({status:res.statusCode!,headers:res.headers,body:text}));});
  req.on('error',fail);req.end(body);
 });
}
function control(port:number,headers:Record<string,string>,takeover=false){
 const host=headers.host??`127.0.0.1:${port}`;
 return new WebSocket(`ws://127.0.0.1:${port}/api/control${takeover?'?takeover=1':''}`,{origin:`http://${host}`,headers});
}
const opened=(ws:WebSocket)=>new Promise<string>(ok=>{ws.on('open',()=>ok('open'));ws.on('unexpected-response',(_req,res)=>{res.resume();ok(String(res.statusCode));});ws.on('error',()=>{});});
it('parses cookies, compares keys and accepts only numeric non-loopback IPv4 hosts',()=>{
 expect(cookieValue('a=1; rover_key=abc ; b=2','rover_key')).toBe('abc');expect(cookieValue(undefined,'rover_key')).toBeUndefined();
 expect(keyMatches(KEY,KEY)).toBe(true);expect(keyMatches(KEY,KEY.slice(1))).toBe(false);expect(keyMatches(KEY,undefined)).toBe(false);
 expect(ipv4Host('192.168.4.3:8787',8787)).toBe(true);
 for(const host of ['192.168.4.3:9999','rover.example:8787','127.0.0.1:8787','300.1.1.1:8787',undefined])expect(ipv4Host(host,8787)).toBe(false);
});
it('without share mode, only this laptop is served and sharing reports off',async()=>{
 const {port}=await start();
 expect((await get(port,'/api/share',{host:`127.0.0.1:${port}`})).body).toBe('{"enabled":false,"urls":[]}');
 expect((await get(port,'/api/state',{host:`192.168.4.3:${port}`})).status).toBe(403);
});
it('share mode: other devices need the QR key, then get a cookie',async()=>{
 const {port}=await start({key:KEY,trustLoopback:false});const host=`192.168.4.3:${port}`;
 expect((await get(port,'/api/state',{host})).status).toBe(401);
 expect((await get(port,'/',{host})).status).toBe(401);
 expect((await get(port,'/?key=wrong-key-wrong-key-wrong-key',{host})).status).toBe(401);
 const entry=await get(port,`/?key=${KEY}`,{host});
 expect(entry.status).toBe(302);expect(entry.headers.location).toBe('/');
 const cookie=String(entry.headers['set-cookie']);expect(cookie).toContain(`rover_key=${KEY}`);expect(cookie).toContain('HttpOnly');expect(cookie).toContain('SameSite=Strict');
 const auth={host,cookie:`rover_key=${KEY}`};
 expect((await get(port,'/api/state',auth)).status).toBe(200);
 expect((await get(port,'/api/state',{...auth,host:`rover.example:${port}`})).status).toBe(403);
 expect((await get(port,'/api/state',{...auth,origin:'http://192.168.4.9:'+port})).status).toBe(403);
 expect((await get(port,'/api/share',auth)).status).toBe(403);
 expect((await get(port,'/api/vision',{...auth,'x-rover-client':'vision','content-type':'application/json'},'POST','{}')).status).toBe(403);
 expect((await get(port,'/api/camera',{...auth,origin:`http://${host}`,'x-rover-client':'dashboard','content-type':'application/json'},'POST','{"ip":"192.168.4.200"}')).status).toBe(200);
});
it('share mode: one device controls; another takes over only on request, stopping the rover',async()=>{
 const {r,port}=await start({key:KEY,trustLoopback:false});
 expect(await opened(control(port,{host:`192.168.4.3:${port}`}))).toBe('403');
 const first=control(port,{host:`192.168.4.3:${port}`,cookie:`rover_key=${KEY}`});expect(await opened(first)).toBe('open');
 const closedWith=new Promise<number>(ok=>first.on('close',code=>ok(code)));
 const {Simulation}=await import('../src/transports');await r.bridge.connect(async()=>new Simulation('clear'),true,'SIMULATION');expect(r.bridge.state.connected).toBe(true);
 const second=control(port,{host:`192.168.4.4:${port}`,cookie:`rover_key=${KEY}`});expect(await opened(second)).toBe('409');
 expect(JSON.parse((await get(port,'/api/control/status',{host:`192.168.4.4:${port}`,cookie:`rover_key=${KEY}`})).body)).toEqual({busy:true});
 const third=control(port,{host:`192.168.4.4:${port}`,cookie:`rover_key=${KEY}`},true);expect(await opened(third)).toBe('open');
 expect(await closedWith).toBe(TAKEN_OVER);
 const start_=Date.now();while(r.bridge.state.connected&&Date.now()-start_<3000)await new Promise(ok=>setTimeout(ok,25));
 expect(r.bridge.state.connected).toBe(false);third.close();
});
it('share mode: this laptop needs no key and gets the share links and QR code',async()=>{
 const {port}=await start({key:KEY});
 const share=JSON.parse((await get(port,'/api/share',{host:`127.0.0.1:${port}`})).body);
 expect(share.enabled).toBe(true);for(const url of share.urls)expect(url).toMatch(new RegExp(`^http://\\d+\\.\\d+\\.\\d+\\.\\d+:${port}/\\?key=${KEY}$`));
 const qr=await get(port,'/api/share/qr.svg',{host:`127.0.0.1:${port}`});
 if(share.urls.length){expect(qr.status).toBe(200);expect(qr.headers['content-type']).toContain('image/svg+xml');expect(qr.body).toContain('<svg');}
 else expect(qr.status).toBe(404);
});
