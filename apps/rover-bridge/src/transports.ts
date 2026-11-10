import { SerialPort } from 'serialport';
import { spawn } from 'node:child_process';
import { EventEmitter } from 'node:events';
import { resolve } from 'node:path';
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
export class Simulation extends EventEmitter implements Transport {
 private child;
 constructor(scenario:string){
  super();if(!['clear','obstacle','sensor-fault','estop'].includes(scenario))throw Error('Invalid simulation scenario');
  this.child=spawn(resolve(process.env.ROVER_ROOT||process.cwd(),'build/rover-sim'),[scenario]);
  this.child.stdout.on('data',b=>this.emit('data',b.toString()));
  this.child.stderr.on('data',b=>this.emit('fault',Error(b.toString())));
  this.child.on('error',e=>this.emit('fault',Error(`Build simulator first: ${e.message}`)));
  this.child.on('exit',()=>this.emit('lost'));
 }
 write(data:string){if(!this.child.stdin.writable)throw Error('Simulator closed');this.child.stdin.write(data);}
 async close(){this.child.stdin.end();this.child.kill();}
}
