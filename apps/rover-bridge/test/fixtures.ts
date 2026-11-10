import {EventEmitter} from 'node:events';
import type {Telemetry} from '../../../packages/protocol/index';
export const sample:Telemetry={v:1,fw:'rover-usb-v1',ms:100,armed:true,auto:false,estop:false,healthy:true,requested:0,applied:0,en:false,brushReq:false,conveyorReq:false,brush:false,conveyor:false,nav:'MANUAL',cm:[120,100,70],age:[20,85,150]};
export class MockSerial extends EventEmitter {
 writes:string[]=[];closed=false;write(value:string){this.writes.push(value);}
 async close(){this.closed=true;}
 telemetry(t:Partial<Telemetry>={}){this.emit('data','TEL '+JSON.stringify({...sample,...t})+'\n');}
 ack(){for(const line of this.writes.splice(0))this.emit('data','OK '+line);}
}
