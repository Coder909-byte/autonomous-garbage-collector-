import type { Telemetry,VisionState,VisionTarget } from '../../../packages/protocol/index.js';

// Laptop-side camera guidance. Firmware safety is unchanged: every motion
// still needs ARM, heartbeats, fresh telemetry and the 1200 ms deadline.
export const VISION={
 FRESH_MS:700,      // a detection older than this is not steered on
 LOST_MS:1500,      // no garbage for this long hands over to firmware AUTO
 CENTER:0.15,       // |cx-0.5| within this drives straight
 MIN_CONF:0.35,
 // Telemetry arrives every 500 ms, so a reading can be ~0.7 s old when used;
 // stop at the firmware AUTO front threshold to leave that margin.
 FRONT_STOP_CM:35,
 SENSOR_MS:500,     // firmware-reported reading age at telemetry time
 TURN_MS:250,       // turn pulse incl. the 100 ms firmware neutral gate; then wait for a newer frame
 TICK_MS:100,
} as const;

export type VisionAction='F'|'L'|'R'|'STOP'|'EXPLORE';
export interface VisionDecision {action:VisionAction;phase:VisionState['phase'];reason:string;target:VisionTarget|null}

// Largest confident box: usually the nearest item on the floor.
export function bestTarget(targets:VisionTarget[]):VisionTarget|null {
 let best:VisionTarget|null=null;
 for(const t of targets)if(t.conf>=VISION.MIN_CONF&&(!best||t.w*t.h>best.w*best.h))best=t;
 return best;
}

export function decide(input:{now:number;detectedAt:number|null;lastTargetAt:number|null;targets:VisionTarget[];telemetry:Telemetry;receivedAt:number;turnEndedAt:number}):VisionDecision {
 const {now,detectedAt,telemetry:t}=input;
 if(detectedAt===null||now-detectedAt>VISION.LOST_MS)
  return {action:'STOP',phase:'WAITING',reason:'No camera detections: start the vision service and connect the camera',target:null};
 const target=now-detectedAt<=VISION.FRESH_MS?bestTarget(input.targets):null;
 if(!target){
  if(input.lastTargetAt===null||now-input.lastTargetAt>VISION.LOST_MS)
   return {action:'EXPLORE',phase:'EXPLORE',reason:'No garbage in view; firmware obstacle-avoiding cruise',target:null};
  return {action:'STOP',phase:'WAITING',reason:'Target lost; holding for the camera',target:null};
 }
 const frontValid=t.cm[0]>=2&&t.age[0]<=VISION.SENSOR_MS&&now-input.receivedAt<1200;
 if(!frontValid)return {action:'STOP',phase:'BLOCKED',reason:'Front ultrasonic reading invalid or stale',target};
 const offset=target.cx-0.5;
 if(Math.abs(offset)>VISION.CENTER){
  const phase=offset<0?'ALIGN_LEFT':'ALIGN_RIGHT';
  if(detectedAt!<=input.turnEndedAt)return {action:'STOP',phase,reason:'Waiting for a frame taken after the last turn',target};
  return {action:offset<0?'L':'R',phase,reason:`Turning toward ${target.label}`,target};
 }
 if(t.cm[0]<=VISION.FRONT_STOP_CM)return {action:'STOP',phase:'BLOCKED',reason:`Front obstacle at ${t.cm[0]} cm`,target};
 return {action:'F',phase:'APPROACH',reason:`Collecting ${target.label} (${Math.round(target.conf*100)}%)`,target};
}
