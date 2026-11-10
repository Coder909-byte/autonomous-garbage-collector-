import type {Direction} from '../../../packages/protocol/index';
export type Send=(message:Record<string,unknown>)=>void;
export class HoldControl {
 private timer:ReturnType<typeof setInterval>|null=null;private source:string|null=null;
 constructor(private send:Send){}
 start(direction:Direction,source:string){
  if(this.source===source)return;this.release();this.source=source;
  const renew=()=>{if(document.hidden||!document.hasFocus()){this.release();return;}this.send({type:'hold',direction});};
  this.send({type:'hold',direction});this.timer=setInterval(renew,80);
 }
 release(source?:string){if(source&&source!==this.source)return;if(this.timer)clearInterval(this.timer);const active=this.source!==null;this.source=null;this.timer=null;if(active)this.send({type:'release'});}
}
export function keyDirection(key:string):Direction|null{return ({w:'F',s:'B',a:'L',d:'R'} as Record<string,Direction>)[key.toLowerCase()]??null;}
