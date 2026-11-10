import {EventEmitter} from 'node:events';
import {describe,it,expect,vi} from 'vitest';
const config=vi.hoisted(()=>({busy:false,failWrite:false,lastOptions:{} as Record<string,unknown>}));
vi.mock('serialport',()=>({SerialPort:class extends EventEmitter {
 static async list(){return [{path:'/dev/mock',manufacturer:'Mock ESP32',serialNumber:'test'}];}
 isOpen=false;
 constructor(options:Record<string,unknown>){super();config.lastOptions=options;}
 open(cb:(e?:Error)=>void){if(config.busy)cb(Error('resource busy'));else{this.isOpen=true;cb();}}
 write(_s:string,cb:(e?:Error)=>void){cb(config.failWrite?Error('write failed'):undefined);}
 drain(cb:()=>void){cb();}close(cb:()=>void){this.isOpen=false;cb();}
}}));
import {Hardware,ports} from '../src/transports';
describe('hardware serial boundary using a mocked driver',()=>{
 it('discovers only real enumerated ports, uses exclusive 115200 and closes',async()=>{expect(await ports()).toEqual([{path:'/dev/mock',label:'Mock ESP32 · test'}]);await expect(Hardware.open('/dev/arbitrary')).rejects.toThrow('enumerated');const d=await Hardware.open('/dev/mock');expect(config.lastOptions).toMatchObject({baudRate:115200,lock:true,autoOpen:false});d.write('S\n');await d.close();expect(()=>d.write('F\n')).toThrow('closed');});
 it('reports contention/open failure and asynchronous write errors',async()=>{config.busy=true;await expect(Hardware.open('/dev/mock')).rejects.toThrow('owned');config.busy=false;const d=await Hardware.open('/dev/mock');const error=vi.fn();d.on('fault',error);config.failWrite=true;d.write('S\n');expect(error).toHaveBeenCalled();config.failWrite=false;await d.close();});
});
