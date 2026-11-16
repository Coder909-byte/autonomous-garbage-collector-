import {useEffect,useState} from 'react';
import {MOTIONS,type Telemetry,type DiagnosticRecord} from '../../../packages/protocol/index';
import {navigationDetail,sensorValid} from './navigation';

export function Navigation({t,fresh,age}:{t:Telemetry|null;fresh:boolean;age:number}){
 const motion=fresh&&t?t.applied:0;
 return <section className="panel navigation" aria-label="Navigation visualization"><div className="panel-title"><h2>Obstacle decision</h2><span className={'pill '+(fresh?'':'warn')}>{fresh?t?.nav:'UNKNOWN'}</span></div>
  <div className="navigation-body"><svg viewBox="0 0 280 180" role="img" aria-label={`Rover proximity; applied ${fresh&&t?MOTIONS[motion]:'unknown'}`}>
   {[{x:140,y:22,i:0,name:'Front'},{x:38,y:100,i:1,name:'Left'},{x:242,y:100,i:2,name:'Right'}].map(({x,y,i,name})=>{const valid=fresh&&t&&sensorValid(t,i,age);const blocked=valid&&t.cm[i]<=(i===0?35:20);return <g key={name} className={!valid?'range-unknown':blocked?'range-blocked':'range-clear'}><path d={`M140 115 L${x} ${y+10}`} stroke="currentColor" strokeDasharray="4 4"/><circle cx={x} cy={y+10} r="4" fill="currentColor"/><text x={x} y={y-5} textAnchor="middle" fill="currentColor">{name} {valid?`${t.cm[i]} cm`:'invalid'}</text></g>;})}
   <rect x="111" y="85" width="58" height="70" rx="9" fill="#192e47" stroke="#658bb5"/><path d="M130 100l10-9 10 9" fill="none" stroke="#a6d1ff"/>
   <text x="140" y="132" textAnchor="middle" fill="#c7d9f1">ROVER</text>
   <text x="140" y="176" textAnchor="middle" fill="#a6d1ff">{fresh&&t?`${['■','↑','↓','↶','↷'][motion]} ${MOTIONS[motion]}`:'OUTPUT UNKNOWN'}</text>
  </svg><p>{navigationDetail(t,fresh)}</p></div>
  <p className="tiny">Firmware-reported decision and software outputs. Diagram is not a map, measured heading or physical motion feedback.</p>
 </section>;
}
type Recent={count:number;capacity:number;dropped:number;samples:DiagnosticRecord[];events:DiagnosticRecord[]};
export function DiagnosticsPanel({online}:{online:boolean}){
 const [data,setData]=useState<Recent|null>(null),[error,setError]=useState('');
 useEffect(()=>{
  if(!online)return;let disposed=false,pending=false;const controller=new AbortController();
  const poll=async()=>{if(pending)return;pending=true;try{const response=await fetch('/api/diagnostics',{signal:AbortSignal.any([controller.signal,AbortSignal.timeout(7000)])});if(!response.ok)throw Error(`HTTP ${response.status}`);const value=await response.json();if(!Array.isArray(value.samples)||!Array.isArray(value.events)||!Number.isInteger(value.count))throw Error('Invalid diagnostics response');if(!disposed){setData(value);setError('');}}catch(e){if(!disposed)setError(String(e));}finally{pending=false;}};
  void poll();const timer=setInterval(()=>void poll(),2000);return()=>{disposed=true;controller.abort();clearInterval(timer);};
 },[online]);
 const samples=data?.samples??[],latest=samples.at(-1);
 // Never connect different sources or sessions with a line. Invalid readings create gaps.
 const series=samples.filter(r=>r.session===latest?.session),start=series[0]?.at??0,end=latest?.at??start;
 const path=(index:number)=>{let segment=false;return series.map(r=>{const t=r.telemetry;if(!t||!sensorValid(t,index,0)){segment=false;return '';}
  const x=20+((r.at-start)/Math.max(1,end-start))*760,y=125-(t.cm[index]/400)*110;const command=segment?'L':'M';segment=true;return `${command}${x.toFixed(1)},${y.toFixed(1)}`;}).join(' ');};
 return <section className="panel diagnostics" aria-label="Diagnostics recording"><div className="panel-title"><h2>Telemetry recording &amp; trends</h2><span className={'pill '+(online?'good':'warn')}>{online?'Bridge recording':'Bridge offline'}</span></div>
  <div className="diagnostic-toolbar"><p>{data?`${data.count.toLocaleString()} / ${data.capacity.toLocaleString()} records · ${data.dropped} older records evicted`:'Waiting for diagnostics.'}</p><div><a className="button secondary" href="/api/diagnostics/export?format=csv" download>Export CSV</a><a className="button secondary" href="/api/diagnostics/export?format=json" download>Export JSON</a></div></div>
  {latest?<><div className="trend-legend"><b>{latest.source.toUpperCase()} · {latest.port}</b><span className="front-line">Front</span><span className="left-line">Left</span><span className="right-line">Right</span></div><svg className="trend" viewBox="0 0 800 150" role="img" aria-label="Recent front, left and right ultrasonic trends, 0 to 400 centimeters"><path d="M20 15V125H780 M20 70H780" stroke="#2a3b51" fill="none"/><text x="24" y="12">400 cm</text><text x="24" y="145">0 cm · {new Date(start).toLocaleTimeString()}</text><text x="620" y="145">{new Date(end).toLocaleTimeString()}</text>{[0,1,2].map(i=><path key={i} className={['front-line','left-line','right-line'][i]} d={path(i)} fill="none" strokeWidth="2"/>)}</svg></>:<p className="tiny">Connect a rover or simulator to record ultrasonic samples.</p>}
  <p className="tiny">Last 120 telemetry samples; chart shows the latest session only. Invalid/stale sensor samples create gaps. Laptop UTC receipt times, source and session are included in every export. In-memory buffer survives disconnect, but is lost when the bridge stops; export to save.</p>
  {error&&<p role="alert" className="danger">Diagnostics unavailable: {error}</p>}
  <details><summary>Recent connection, safety and communication events</summary><div className="diagnostic-events">{data?.events.slice().reverse().map(r=><p key={r.id}><time>{r.timestamp}</time> <b>{r.source.toUpperCase()}</b> {r.message}</p>)}</div></details>
 </section>;
}
