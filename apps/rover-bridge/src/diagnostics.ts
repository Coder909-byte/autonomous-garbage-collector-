import {randomUUID} from 'node:crypto';
import {MOTIONS,type Log,type Telemetry,type DiagnosticRecord} from '../../../packages/protocol/index.js';
// Bounded, in-memory recording survives disconnects, never writes to a serial port.
// Export before stopping the bridge; timestamps are laptop receipt time in UTC.
export class Diagnostics {
 private records:DiagnosticRecord[]=[];
 private context:{session:string;source:DiagnosticRecord['source'];port:string|null}={session:randomUUID(),source:'bridge',port:null};
 private sequence=0;private dropped=0;
 constructor(private capacity=10000){}
 begin(simulation:boolean,port:string){this.context={session:randomUUID(),source:simulation?'simulation':'hardware',port};}
 record(at:number,kind:Log['kind'],message:string,t?:Telemetry,event?:DiagnosticRecord['event']){
  this.records.push({id:++this.sequence,at,timestamp:new Date(at).toISOString(),...this.context,
   event:event??(t?'telemetry':kind==='ERROR'?'communication':kind==='TX'?'command':kind==='ACK'?'ack':'info'),
   kind,message:message.slice(0,1024),telemetry:t?structuredClone(t):null});
  if(this.records.length>this.capacity){this.records.shift();++this.dropped;}
 }
 snapshot(){return {schema:1 as const,capacity:this.capacity,count:this.records.length,dropped:this.dropped,records:this.records};}
 recent(){return {...this.snapshot(),records:undefined,
  samples:this.records.filter(r=>r.event==='telemetry').slice(-120),
  events:this.records.filter(r=>['emergency','connection','communication'].includes(r.event)).slice(-10)};}
 csv(){
  const columns=['id','timestamp_utc','session','source','port','event','kind','message','firmware','device_ms','front_cm','left_cm','right_cm','front_age_ms','left_age_ms','right_age_ms','requested','applied','armed','auto','estop','healthy','driver_enable','brush_requested','brush_applied','conveyor_requested','conveyor_applied','navigation'];
  // Prevent external text from being interpreted as a spreadsheet formula.
  const cell=(v:unknown)=>{let s=v===null||v===undefined?'':String(v);if(typeof v==='string'&&/^\s*[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};
  return [columns,...this.records.map(r=>{const t=r.telemetry;return [r.id,r.timestamp,r.session,r.source,r.port,r.event,r.kind,r.message,t?.fw,t?.ms,...(t?.cm??['','','']),...(t?.age??['','','']),t?MOTIONS[t.requested]:'',t?MOTIONS[t.applied]:'',t?.armed,t?.auto,t?.estop,t?.healthy,t?.en,t?.brushReq,t?.brush,t?.conveyorReq,t?.conveyor,t?.nav];})].map(row=>row.map(cell).join(',')).join('\r\n')+'\r\n';
 }
}
