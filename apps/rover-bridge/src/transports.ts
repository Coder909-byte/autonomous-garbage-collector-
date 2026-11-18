import { SerialPort } from 'serialport';
import { EventEmitter } from 'node:events';
import { Socket } from 'node:net';
export {Simulation} from './simulator.js';
export interface Transport extends EventEmitter {write(data:string):void;close():Promise<void>}
export async function ports(){return (await SerialPort.list()).map(p=>({path:p.path,label:[p.manufacturer,p.serialNumber].filter(Boolean).join(' · ')}));}
export class Hardware extends EventEmitter implements Transport {
 constructor(private port:SerialPort){super();port.on('data',b=>this.emit('data',b.toString()));port.on('error',e=>this.emit('fault',e));port.on('close',()=>this.emit('lost'));}
 static async open(path:string){
  if(!(await ports()).some(p=>p.path===path))throw Error('Select a currently enumerated serial port');
  const port=new SerialPort({path,baudRate:115200,autoOpen:false,lock:true});
  await new Promise<void>((ok,fail)=>port.open(e=>e?fail(Error(`Port unavailable or owned by uploader/monitor: ${e.message}`)):ok()));
  return new Hardware(port);
 }
 write(data:string){if(!this.port.isOpen)throw Error('Serial port closed');this.port.write(data,e=>{if(e)this.emit('fault',e);});}
 async close(){if(!this.port.isOpen)return;await new Promise<void>(ok=>{const timer=setTimeout(()=>{this.port.close(()=>ok());},250);this.port.drain(()=>{clearTimeout(timer);this.port.close(()=>ok());});});}
}
export const WIFI_PORT=3333;
// Accepts an IPv4 address or a hostname with an optional :port suffix.
export function parseWifiTarget(value:unknown):{host:string;port:number}{
 if(typeof value!=='string')throw Error('Enter the rover Wi-Fi address');
 const match=/^([A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?)(?::(\d{1,5}))?$/.exec(value.trim());
 if(!match)throw Error('Invalid rover Wi-Fi address');
 const port=match[2]===undefined?WIFI_PORT:Number(match[2]);
 if(port<1||port>65535)throw Error('Invalid rover Wi-Fi port');
 return {host:match[1],port};
}
export class Network extends EventEmitter implements Transport {
 constructor(private socket:Socket){super();socket.setEncoding('utf8');socket.on('data',b=>this.emit('data',String(b)));socket.on('error',e=>this.emit('fault',e));socket.on('close',()=>this.emit('lost'));}
 static async open(target:string,timeoutMs=4000){
  const {host,port}=parseWifiTarget(target);
  const socket=new Socket();socket.setNoDelay(true);socket.setKeepAlive(true,1000);
  await new Promise<void>((ok,fail)=>{
   const timer=setTimeout(()=>{socket.destroy();fail(Error(`Rover Wi-Fi ${host}:${port} did not answer. Join the ROVER-CTRL network first.`));},timeoutMs);
   socket.once('error',e=>{clearTimeout(timer);socket.destroy();fail(Error(`Rover Wi-Fi ${host}:${port} unavailable: ${e.message}`));});
   socket.connect(port,host,()=>{clearTimeout(timer);socket.removeAllListeners('error');ok();});
  });
  return new Network(socket);
 }
 write(data:string){if(this.socket.destroyed||!this.socket.writable)throw Error('Wi-Fi link closed');this.socket.write(data,e=>{if(e)this.emit('fault',e);});}
 async close(){if(this.socket.destroyed)return;await new Promise<void>(ok=>{const timer=setTimeout(()=>{this.socket.destroy();ok();},250);this.socket.end(()=>{clearTimeout(timer);this.socket.destroy();ok();});});}
}
