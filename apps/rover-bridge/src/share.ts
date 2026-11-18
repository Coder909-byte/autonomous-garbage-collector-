import { randomBytes,timingSafeEqual } from 'node:crypto';
import { existsSync,readFileSync,writeFileSync } from 'node:fs';
import { networkInterfaces } from 'node:os';
import type { IncomingMessage } from 'node:http';
// Share mode opens Mission Control to other devices on the rover's Wi-Fi. They
// get in with a secret key carried by the QR-code link, then kept as a cookie.
export const SHARE_COOKIE='rover_key';
const KEY=/^[A-Za-z0-9_-]{22,64}$/;
export function loadShareKey(file:string){
 if(existsSync(file)){const saved=readFileSync(file,'utf8').trim();if(KEY.test(saved))return saved;}
 const key=randomBytes(18).toString('base64url');writeFileSync(file,key+'\n',{mode:0o600});return key;
}
export function keyMatches(key:string,candidate:unknown){
 if(typeof candidate!=='string'||candidate.length!==key.length)return false;
 return timingSafeEqual(Buffer.from(candidate),Buffer.from(key));
}
export function cookieValue(header:string|undefined,name:string){
 for(const part of (header??'').split(';')){const at=part.indexOf('=');if(at>0&&part.slice(0,at).trim()===name)return part.slice(at+1).trim();}
 return undefined;
}
export function isLoopback(address:string|undefined){return address==='127.0.0.1'||address==='::1'||address==='::ffff:127.0.0.1';}
// Numeric IPv4 Host headers only: a DNS-rebinding page always arrives with a hostname.
export function ipv4Host(host:string|undefined,port:number){
 const m=/^(\d{1,3}(?:\.\d{1,3}){3}):(\d{1,5})$/.exec(host??'');
 return !!m&&Number(m[2])===port&&m[1].split('.').every(n=>Number(n)<=255)&&!m[1].startsWith('127.');
}
// This machine's IPv4 addresses, rover network (192.168.4.x) first.
export function shareAddresses(){
 const all=Object.values(networkInterfaces()).flat().filter(a=>!!a&&a.family==='IPv4'&&!a.internal).map(a=>a!.address);
 return [...new Set(all)].sort((a,b)=>Number(!a.startsWith('192.168.4.'))-Number(!b.startsWith('192.168.4.')));
}
export function shareURLs(port:number,key:string){return shareAddresses().map(ip=>`http://${ip}:${port}/?key=${key}`);}
export function requestKey(req:IncomingMessage){return cookieValue(req.headers.cookie,SHARE_COOKIE);}
