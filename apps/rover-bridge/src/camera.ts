import http from 'node:http';
import type { Request,Response } from 'express';
export function cameraAddress(value:unknown):string {
 if(typeof value!=='string'||!/^\d{1,3}(\.\d{1,3}){3}$/.test(value))throw Error('Enter the camera numeric private IPv4 address');
 const p=value.split('.').map(Number);
 if(p.some(n=>n>255)||p[3]===0||p[3]===255||!(p[0]===10||(p[0]===192&&p[1]===168)||(p[0]===172&&p[1]>=16&&p[1]<=31)))throw Error('Camera must be on the configured private WLAN');
 return p.join('.');
}
export function cameraPath(endpoint:string,query:Request['query']) {
 if(endpoint==='status'||endpoint==='snapshot'||endpoint==='stream')return '/'+endpoint;
 if(endpoint==='settings'){
  const width=Number(query.width),quality=Number(query.quality);
  if(![320,640].includes(width)||!Number.isInteger(quality)||quality<10||quality>40)throw Error('Invalid camera settings');
  return `/settings?width=${width}&quality=${quality}`;
 }
 throw Error('Unknown camera endpoint');
}
export function proxyCamera(ip:string,endpoint:string,req:Request,res:Response){
 const path=cameraPath(endpoint,req.query);let ended=false;
 const fail=(e:Error)=>{if(ended)return;ended=true;if(!res.headersSent)res.status(502).json({error:`Camera unavailable: ${e.message}`});else res.destroy();};
 const upstream=http.request({hostname:cameraAddress(ip),port:endpoint==='stream'?81:80,path,method:endpoint==='settings'?'POST':'GET',timeout:5000},source=>{
  if(ended){source.destroy();return;}
  if(source.statusCode!==200){source.resume();fail(Error(`HTTP ${source.statusCode}`));return;}
  const expected=endpoint==='stream'?'multipart/x-mixed-replace':endpoint==='snapshot'?'image/jpeg':'application/json';
  if(!String(source.headers['content-type']).startsWith(expected)){source.resume();fail(Error('Unexpected camera response format'));return;}
  res.setHeader('Content-Type',String(source.headers['content-type']));res.setHeader('Cache-Control','no-store');
  source.on('error',fail);source.on('end',()=>{ended=true;});source.pipe(res);
 });
 upstream.on('timeout',()=>upstream.destroy(Error('Camera timed out')));upstream.on('error',fail);
 res.on('close',()=>{ended=true;upstream.destroy();});upstream.end();
}
