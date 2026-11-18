import {spawn} from 'node:child_process';
import {EventEmitter} from 'node:events';
import {afterEach,describe,it,expect} from 'vitest';
import {Bridge} from '../src/bridge';
import type {Transport} from '../src/transports';
import {VISION,bestTarget,decide} from '../src/vision';
import {isState,visionFrame,type Telemetry,type VisionTarget} from '../../../packages/protocol/index';
import {sample} from './fixtures';

const tel=(cm:[number,number,number]=[120,100,70]):Telemetry=>({...sample,armed:true,cm,age:[50,50,50]});
const box=(cx:number,size=0.2,conf=0.8,label='bottle'):VisionTarget=>({label,conf,cx,cy:0.6,w:size,h:size});
const base={now:10_000,detectedAt:10_000-100,lastTargetAt:10_000-100,receivedAt:10_000-50,turnEndedAt:0};

describe('camera seek decisions',()=>{
 it('drives forward to a centred target and turns toward an off-centre one',()=>{
  expect(decide({...base,targets:[box(0.52)],telemetry:tel()})).toMatchObject({action:'F',phase:'APPROACH'});
  expect(decide({...base,targets:[box(0.1)],telemetry:tel()})).toMatchObject({action:'L',phase:'ALIGN_LEFT'});
  expect(decide({...base,targets:[box(0.9)],telemetry:tel()})).toMatchObject({action:'R',phase:'ALIGN_RIGHT'});
 });
 it('front ultrasonic has priority over the camera',()=>{
  expect(decide({...base,targets:[box(0.5)],telemetry:tel([VISION.FRONT_STOP_CM,100,100])})).toMatchObject({action:'STOP',phase:'BLOCKED'});
  expect(decide({...base,targets:[box(0.5)],telemetry:tel([-1,100,100])})).toMatchObject({action:'STOP',phase:'BLOCKED'});
  expect(decide({...base,targets:[box(0.5)],telemetry:{...tel(),age:[600,50,50]}})).toMatchObject({action:'STOP'});
 });
 it('waits for a frame newer than the last turn pulse before turning again',()=>{
  expect(decide({...base,turnEndedAt:base.detectedAt,targets:[box(0.1)],telemetry:tel()})).toMatchObject({action:'STOP',phase:'ALIGN_LEFT'});
 });
 it('stops without detections, holds briefly after losing a target, then explores with firmware AUTO',()=>{
  expect(decide({...base,detectedAt:null,lastTargetAt:null,targets:[],telemetry:tel()})).toMatchObject({action:'STOP',phase:'WAITING'});
  expect(decide({...base,detectedAt:base.now-VISION.LOST_MS-1,targets:[box(0.5)],telemetry:tel()})).toMatchObject({action:'STOP',phase:'WAITING'});
  expect(decide({...base,targets:[],telemetry:tel()})).toMatchObject({action:'STOP',phase:'WAITING'});
  expect(decide({...base,lastTargetAt:base.now-VISION.LOST_MS-1,targets:[],telemetry:tel()})).toMatchObject({action:'EXPLORE'});
  expect(decide({...base,lastTargetAt:null,targets:[box(0.5,0.2,0.1)],telemetry:tel()})).toMatchObject({action:'EXPLORE'});
 });
 it('prefers the largest confident box',()=>{
  expect(bestTarget([box(0.2,0.1),box(0.8,0.4),box(0.5,0.9,0.2)])?.cx).toBe(0.8);
 });
 it('validates vision frames strictly',()=>{
  expect(visionFrame({detector:'yolo',targets:[box(0.5)]}).targets).toHaveLength(1);
  for(const bad of [null,{detector:'',targets:[]},{detector:'x',targets:[{...box(0.5),cx:1.5}]},{detector:'x',targets:Array(7).fill(box(0.5))},{detector:'x',targets:[{...box(0.5),label:'<script>'}]}])
   expect(()=>visionFrame(bad)).toThrow();
 });
});

class MotorFirmware extends EventEmitter implements Transport {
 private child=spawn('build/rover-motor-bench-release-sim');
 constructor(){super();this.child.stdout.on('data',b=>this.emit('data',b.toString()));this.child.on('exit',()=>this.emit('lost'));}
 write(data:string){this.child.stdin.write(data);}
 async close(){this.child.stdin.end();this.child.kill();}
}
const bridges:Bridge[]=[];
afterEach(async()=>{for(const b of bridges.splice(0))await b.dispose();});
async function waitFor(test:()=>boolean,ms=5000){const start=Date.now();while(!test()){if(Date.now()-start>ms)throw Error('Vision condition timed out');await new Promise(r=>setTimeout(r,20));}}

it('real bench firmware: camera seek turns, approaches with brushes, explores, and yields to the operator',async()=>{
 const b=new Bridge();bridges.push(b);await b.connect(async()=>new MotorFirmware(),false,'HOST-BENCH-RELEASE');
 await waitFor(()=>b.ready());
 expect(()=>b.visionEnable(true)).toThrow('armed');
 b.command('ARM');await waitFor(()=>!!b.state.telemetry?.armed);
 let target:VisionTarget|null=box(0.1);
 const feed=setInterval(()=>b.visionFrame({detector:'test',targets:target?[target]:[]}),100);
 try{
  b.visionEnable(true);expect(isState(b.state)).toBe(true);
  await waitFor(()=>b.state.telemetry?.applied===3);
  target=box(0.5);
  await waitFor(()=>b.state.telemetry?.applied===1&&b.state.telemetry?.brush===true&&b.state.telemetry?.conveyor===true);
  expect(b.state.vision).toMatchObject({enabled:true,phase:'APPROACH'});
  target=null;
  await waitFor(()=>b.state.telemetry?.auto===true,6000);
  expect(b.state.vision?.phase).toBe('EXPLORE');
  b.command('MANUAL');
  expect(b.state.vision).toMatchObject({enabled:false,phase:'OFF'});
  await waitFor(()=>b.state.telemetry?.auto===false&&b.state.telemetry?.applied===0);
 }finally{clearInterval(feed);}
},20000);
