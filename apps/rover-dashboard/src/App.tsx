import {useCallback,useEffect,useMemo,useRef,useState} from 'react';
import {isState,MOTIONS,type BridgeState,type Command,type Direction} from '../../../packages/protocol/index';
import {HoldControl,keyDirection} from './control';
const empty:BridgeState={connected:false,connecting:false,protocolReady:false,simulation:false,port:null,telemetry:null,receivedAt:null,intent:null,logs:[],error:null};
async function api(path:string,body?:unknown){
 const response=await fetch('/api/'+path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json','X-Rover-Client':'dashboard'},body:body===undefined?undefined:JSON.stringify(body)});
 const data=await response.json();if(!response.ok)throw Error(data?.error||`HTTP ${response.status}`);return data;
}
function time(at:number|null){return at===null?'Never':new Date(at).toLocaleTimeString();}
function Icon({type}:{type:'camera'|'link'|'sensor'|'rover'}){return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">{type==='camera'?<><path d="M3 7h4l2-3h6l2 3h4v13H3z"/><circle cx="12" cy="13" r="4"/></>:type==='link'?<><path d="M9 15l6-6M8 17l-1 1a4 4 0 01-6-6l4-4a4 4 0 016 0m2-1l1-1a4 4 0 016 6l-4 4a4 4 0 01-6 0"/></>:type==='sensor'?<><path d="M4 6a12 12 0 0116 0M7 10a7 7 0 0110 0M10 14a3 3 0 014 0"/><circle cx="12" cy="19" r="1"/></>:<><path d="M4 7h16v10H4zM8 7V3h8v4M8 11h8M2 9v6m20-6v6"/><circle cx="7" cy="20" r="2"/><circle cx="17" cy="20" r="2"/></>}</svg>;}
export default function App(){
 const [history,setHistory]=useState<{at:number;nav:string;motion:number}[]>([]);
 const [state,setState]=useState<BridgeState>(empty),[online,setOnline]=useState(false),[error,setError]=useState(''),[clock,setClock]=useState(Date.now());
 const [ports,setPorts]=useState<{path:string;label:string}[]>([]),[port,setPort]=useState(''),[simulation,setSimulation]=useState(true),[scenario,setScenario]=useState('clear');
 const ws=useRef<WebSocket|null>(null);
 const send=useCallback((m:Record<string,unknown>)=>{if(ws.current?.readyState===WebSocket.OPEN)ws.current.send(JSON.stringify(m));else setError('Bridge disconnected. Stop delivery is unconfirmed.');},[]);
 const hold=useMemo(()=>new HoldControl(send),[send]);
 const refresh=useCallback(async()=>{try{const p=await api('ports');if(!Array.isArray(p)||!p.every(v=>typeof v.path==='string'&&typeof v.label==='string'))throw Error('Invalid serial discovery response');setPorts(p);if(p.length)setPort(prev=>prev||p[0].path);}catch(e){setError(String(e));}},[]);
 useEffect(()=>{
  let disposed=false,retry:ReturnType<typeof setTimeout>|undefined;
  const open=()=>{
   if(disposed)return;
   const socket=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/api/control`);ws.current=socket;
   socket.onopen=()=>{if(!disposed&&ws.current===socket){setOnline(true);setError('');void refresh();}};
   socket.onmessage=e=>{if(disposed||ws.current!==socket)return;try{const value=JSON.parse(e.data);if(!isState(value))throw Error('Invalid bridge state');setState(value);}catch{hold.release();socket.close();setState(empty);setOnline(false);setError('Invalid server response. Control disabled; stop delivery unconfirmed.');}};
   socket.onerror=()=>{if(!disposed&&ws.current===socket){hold.release();setError('Cannot reach the local bridge, or another operator owns control.');}};
   socket.onclose=()=>{if(!disposed&&ws.current===socket){hold.release();setOnline(false);setState(empty);setError('Bridge disconnected. Manual lease expires; STOP delivery is unconfirmed.');retry=setTimeout(open,1000);}};
  };
  retry=setTimeout(open,0);const timer=setInterval(()=>setClock(Date.now()),100);
  return()=>{disposed=true;clearInterval(timer);clearTimeout(retry);hold.release();ws.current?.close();};
 },[hold,refresh]);
 const t=state.telemetry,age=state.receivedAt===null?Infinity:clock-state.receivedAt;
 useEffect(()=>{
  if(!t||state.receivedAt===null){setHistory([]);return;}
  setHistory(current=>{const previous=current.at(-1);return previous&&previous.nav===t.nav&&previous.motion===t.applied?current:[...current,{at:state.receivedAt!,nav:t.nav,motion:t.applied}].slice(-7);});
 },[t,state.receivedAt]);
 const fresh=state.connected&&state.protocolReady&&age<1200,canMove=online&&fresh&&!!t?.armed&&!t.auto&&!t.estop&&t.healthy;
 const command=useCallback((c:Command)=>{hold.release();send({type:'command',command:c});},[send,hold]);
 useEffect(()=>{if(!canMove)hold.release();},[canMove,hold]);
 useEffect(()=>{
  const release=()=>hold.release();const visibility=()=>{if(document.hidden)release();};
  const down=(e:KeyboardEvent)=>{
   if((e.target as HTMLElement)?.closest?.('input,select,textarea')&&e.code!=='Space')return;
   if(e.code==='Space'){e.preventDefault();command('S');return;}
   if(e.ctrlKey||e.metaKey||e.altKey)return;
   const d=keyDirection(e.key);if(d){e.preventDefault();if(!e.repeat&&canMove)hold.start(d,'key:'+e.key.toLowerCase());}
  };
  const up=(e:KeyboardEvent)=>{if(keyDirection(e.key))hold.release('key:'+e.key.toLowerCase());};
  window.addEventListener('keydown',down);window.addEventListener('keyup',up);window.addEventListener('blur',release);window.addEventListener('pagehide',release);document.addEventListener('visibilitychange',visibility);
  return()=>{release();window.removeEventListener('keydown',down);window.removeEventListener('keyup',up);window.removeEventListener('blur',release);window.removeEventListener('pagehide',release);document.removeEventListener('visibilitychange',visibility);};
 },[canMove,command,hold]);
 const direction=(label:string,d:Direction,arrow:string)=><button className={'direction dir-'+d} aria-label={label} disabled={!canMove}
 onPointerDown={e=>{if(e.button!==0)return;e.preventDefault();e.currentTarget.setPointerCapture?.(e.pointerId);hold.start(d,'pointer:'+e.pointerId);}}
 onPointerUp={e=>hold.release('pointer:'+e.pointerId)} onPointerCancel={()=>hold.release()} onLostPointerCapture={()=>hold.release()}>{arrow}<kbd>{({F:'W',B:'S',L:'A',R:'D'})[d]}</kbd></button>;
 const lastTX=[...state.logs].reverse().find(l=>l.kind==='TX'),lastACK=[...state.logs].reverse().find(l=>l.kind==='ACK');
 const session=state.connected?(state.simulation?'SIMULATION MODE':'USB HARDWARE'):online?'NO ROVER CONNECTED':'BRIDGE OFFLINE';
 return <div className="station">
  <header><div className="brand"><span className="brandmark"><Icon type="rover"/></span><div>ROVER<span className="brand-sub">AUTONOMOUS COLLECTION SYSTEM</span></div></div><div className="header-right"><span className={'session '+(state.simulation&&state.connected?'sim':'')}><i/> {session}</span><span className="clock">{new Date(clock).toLocaleTimeString()}</span></div></header>
  <div className="page-heading"><div><div className="eyebrow">OPERATOR WORKSPACE <span>/ 01</span></div><h1>Mission control<span className="live-dot"/></h1><p>Local control. Onboard authority. Every output accounted for.</p></div><button className="estop" disabled={!state.connected} onClick={()=>command('ESTOP')}><span>■</span> SOFTWARE EMERGENCY STOP<small>Latches firmware E-stop · physical cutoff still required</small></button></div>
  {(error||state.error)&&<div role="alert" className="alert">{error||state.error}<button aria-label="Dismiss error" onClick={()=>{setError('');setState(s=>({...s,error:null}));}}>×</button></div>}
  {state.connected&&state.simulation&&<div className="simulation-banner">SIMULATION MODE <span>Native controller · synthetic distances · no physical outputs or camera footage</span></div>}
  <main className="dashboard-grid">
   <aside className="left-column">
    <section className="panel"><div className="panel-title"><Icon type="link"/><h2>Connection</h2><span className={'pill '+(state.connected?'good':'')}>{state.connecting?'Opening':state.connected?'Connected':'Disconnected'}</span></div>
     <label>CONTROL SOURCE<select aria-label="Control source" value={simulation?'simulation':'hardware'} disabled={state.connected||state.connecting} onChange={e=>setSimulation(e.target.value==='simulation')}><option value="simulation">Offline simulator</option><option value="hardware">Main ESP32 · USB serial</option></select></label>
     {simulation?<label>SCENARIO<select aria-label="Scenario" value={scenario} disabled={state.connected} onChange={e=>setScenario(e.target.value)}><option value="clear">Clear path</option><option value="obstacle">Obstacle at 3s, clear at 6s</option><option value="sensor-fault">Sensor fault at 3s</option><option value="estop">E-stop feedback opens at 3s</option></select></label>:<label>SERIAL PORT <button className="text-button" onClick={()=>void refresh()}>Refresh</button><select aria-label="Serial port" value={port} disabled={state.connected} onChange={e=>setPort(e.target.value)}><option value="">Select a port</option>{ports.map(p=><option key={p.path} value={p.path}>{p.path} {p.label}</option>)}</select></label>}
     <button className={state.connected?'button secondary full':'button primary full'} disabled={!online||state.connecting||(!state.connected&&!simulation&&!port)} onClick={()=>{hold.release();send(state.connected?{type:'disconnect'}:{type:'connect',simulation,port,scenario});}}>{state.connected?'Disconnect rover':'Connect rover'} <span aria-hidden="true">↗</span></button>
     <div className="micro-line"><span>USB protocol</span><span>115200 baud / v{t?.v??'—'}</span></div>
    </section>
    <section className="panel manual-panel"><div className="panel-title"><h2>Drive control</h2><span className={'pill '+(t?.armed?'good':'')}>{t?(t.armed?'ARMED':'DISARMED'):'UNKNOWN'}</span></div>
     <div className="segmented"><button disabled={!fresh} className={!t?.auto?'selected':''} onClick={()=>command('MANUAL')}>Manual</button><button disabled={!fresh||!t?.armed} className={t?.auto?'selected':''} onClick={()=>command('AUTO')}>Autonomous</button></div>
     <div className="dpad">{direction('Forward','F','↑')}{direction('Left','L','←')}<button className="direction stop" aria-label="Stop movement" disabled={!state.connected} onClick={()=>command('S')}>■<kbd>SPACE</kbd></button>{direction('Right','R','→')}{direction('Backward','B','↓')}</div>
     <p className="control-hint">Hold to move. Release to stop.<br/>W A S D · Space to stop</p>
     <div className="two-buttons"><button className="button primary" disabled={!fresh||t?.armed||t?.estop||!t?.healthy} onClick={()=>command('ARM')}>ARM</button><button className="button secondary" disabled={!state.connected} onClick={()=>command('DISARM')}>DISARM</button></div>
     <button className="text-button reset" disabled={!fresh||t?.armed||!t?.healthy||!t?.estop} onClick={()=>command('RESET')}>Reset firmware E-stop latch</button>
     <p className="tiny">ARM permits control; it does not start motion.</p>
    </section>
   </aside>
   <div className="center-column"><Camera/>
    <section className="panel operations" aria-label="Operational state"><div className="panel-title"><h2>Operational state</h2><span className={'pill '+(fresh?'good':'warn')}>{t?(fresh?'Fresh telemetry':'STALE TELEMETRY'):'Awaiting telemetry'}</span></div>
     <div className="metric-grid"><div><label>REQUESTED MOVEMENT</label><strong>{fresh&&t?MOTIONS[t.requested]:'—'}</strong></div><div><label>APPLIED FIRMWARE OUTPUT</label><strong className="accent">{fresh&&t?MOTIONS[t.applied]:'—'}</strong></div><div><label>NAVIGATION PHASE</label><strong>{fresh?t?.nav:'—'}</strong></div><div><label>DRIVER ENABLE</label><strong>{fresh?(t?.en?'HIGH':'LOW'):'UNKNOWN'}</strong></div></div>
     <div className="authority"><i/> Physical movement: <b>not measured</b><span>No encoders or independent motion feedback</span></div>
    </section>
   </div>
   <aside className="right-column"><section className="panel"><div className="panel-title"><Icon type="sensor"/><h2>Proximity sensors</h2></div>
    {['Front','Left','Right'].map((name,i)=>{const valid=fresh&&t&&t.cm[i]>=2&&t.age[i]+age<=500;const blocked=valid&&t.cm[i]<=(i===0?35:20);return <div className={'sensor '+(blocked?'blocked':'')} key={name}><div className="sensor-top"><span>{name}</span><span className={'sensor-state '+(valid?'':'warn')}>{!valid?'INVALID / STALE':blocked?'OBSTACLE':'CLEAR'}</span></div><div className="sensor-value">{valid?t.cm[i]:'—'}<small>cm</small><span>{t?`${Math.max(0,Math.round(t.age[i]+age))} ms old`:'No reading'}</span></div><div className="range-track"><span style={{width:valid?`${Math.min(100,t.cm[i]/2)}%`:'0%'}}/></div></div>;})}
     <p className="tiny">AUTO thresholds: front 35 cm · sides 20 cm. Sensor freshness limit: 500 ms.</p>
    </section>
    <section className="panel cleaning"><div className="panel-title"><h2>Collection system</h2><span className="subtle">L298N</span></div>{(['Brushes','Conveyor'] as const).map((name,i)=>{const requested=i===0?t?.brushReq:t?.conveyorReq,applied=i===0?t?.brush:t?.conveyor;return <div className="clean-row" key={name}><div><h3>{name}</h3><small>Requested {fresh?(requested?'ON':'OFF'):'—'} <span>·</span> Applied <b>{fresh?(applied?'ON':'OFF'):'UNKNOWN'}</b></small></div><button aria-label={`${name} ${requested?'OFF':'ON'}`} aria-pressed={!!requested} className={'toggle '+(requested&&fresh?'on':'')} disabled={!fresh||(!t?.armed&&!requested)} onClick={()=>command(`${i===0?'BRUSH':'CONVEYOR'} ${requested?'OFF':'ON'}` as Command)}><i/></button></div>;})}
     <div className="two-buttons"><button className="button secondary" disabled={!fresh||!t?.armed} onClick={()=>command('CLEAN ON')}>CLEAN ON</button><button className="button secondary" disabled={!state.connected} onClick={()=>command('CLEAN OFF')}>CLEAN OFF</button></div><p className="tiny">Outputs run only during applied forward motion. Requested ON can remain pending while stopped.</p>
    </section>
   </aside>
  </main>
  <section className="panel telemetry-strip"><div><span className="eyebrow">LAST UPDATE</span><b>{time(state.receivedAt)}</b></div><div><span className="eyebrow">FIRMWARE</span><b>{t?.fw??'Not identified'}</b></div><div><span className="eyebrow">E-STOP FEEDBACK</span><b className={t?.estop?'danger':''}>{fresh?(t?.estop?'LATCHED':t?.healthy?'HIGH · healthy':'LOW · unsafe'):'UNKNOWN'}</b></div><div><span className="eyebrow">LAST TRANSMITTED</span><b>{lastTX?.text??'—'}</b></div><div><span className="eyebrow">LAST ACKNOWLEDGED</span><b>{lastACK?.text??'—'}</b></div></section>
  <section className="panel timeline" aria-label="Telemetry timeline"><span className="eyebrow">STATE TIMELINE</span><div>{history.length?history.map((entry,i)=><div key={i}><span className="timeline-point"/><time>{time(entry.at)}</time><b>{MOTIONS[entry.motion]}</b><small>{entry.nav}</small></div>):<p>Waiting for firmware state changes.</p>}</div></section>
  <details className="panel console"><summary><span className="terminal-icon">›_</span> Developer console <span>Commands · acknowledgements · raw serial · parsed telemetry</span><b>{state.logs.length} events</b></summary><div className="console-content"><div className="logs" role="log">{state.logs.length?state.logs.slice().reverse().map((l,i)=><div key={i} className={'log '+l.kind}><time>{time(l.at)}</time><b>{l.kind}</b><code>{l.text}</code></div>):<p>No serial events. Connect a rover or simulator.</p>}</div><pre aria-label="Parsed telemetry">{t?JSON.stringify(t,null,2):'No versioned telemetry received.'}</pre></div></details>
  <footer><span><i/> MAIN ESP32 RETAINS FINAL CONTROL AUTHORITY</span><span>Software stop does not confirm motor-power isolation. Use the physical emergency cutoff.</span></footer>
 </div>;
}
function Camera(){
 const [ip,setIP]=useState(()=>localStorage.getItem('rover.cameraIP')||''),[active,setActive]=useState(false),[status,setStatus]=useState('DISCONNECTED'),[error,setError]=useState(''),[width,setWidth]=useState(320),[quality,setQuality]=useState(14),[busy,setBusy]=useState(false);
 const validate=(s:unknown)=>{if(!s||typeof s!=='object'||typeof (s as {ready?:unknown}).ready!=='boolean'||typeof (s as {streaming?:unknown}).streaming!=='boolean')throw Error('Invalid camera status');return s as {ready:boolean;streaming:boolean;width:number;quality:number};};
 const connect=async()=>{setBusy(true);setError('');try{await api('camera',{ip});const s=validate(await api('camera/status'));if(!s.ready)throw Error('Camera initialization failed; inspect camera serial diagnostics');localStorage.setItem('rover.cameraIP',ip);setWidth(s.width);setQuality(s.quality);setStatus('CONNECTING');setActive(true);}catch(e){setError(String(e));setStatus('UNAVAILABLE');setActive(false);}finally{setBusy(false);}};
 useEffect(()=>{if(!active)return;let live=true;const timer=setInterval(()=>{void api('camera/status').then(raw=>{const s=validate(raw);if(live){if(!s.ready)throw Error('Camera unavailable');setStatus(s.streaming?'LIVE CAMERA':'CONNECTING');}}).catch(e=>{if(live){setError(String(e));setStatus('STREAM FAILED');setActive(false);}});},2000);return()=>{live=false;clearInterval(timer);};},[active]);
 const snapshot=async()=>{try{const response=await fetch('/api/camera/snapshot');if(!response.ok||!response.headers.get('content-type')?.startsWith('image/jpeg'))throw Error('Snapshot unavailable');const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download='rover-snapshot.jpg';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){setError(String(e));}};
 return <section className="panel camera-panel"><div className="panel-title"><Icon type="camera"/><h2>Vision / ESP32-CAM</h2><span className={'pill '+(status==='LIVE CAMERA'?'good':'')}>{status}</span></div><div className={'camera-view '+(active?'active':'')}>
  {active?<img alt="Live ESP32-CAM MJPEG stream" src="/api/camera/stream" onError={()=>{setActive(false);setStatus('STREAM FAILED');setError('MJPEG stream failed. Check camera power, Wi-Fi and address.');}}/>:<div className="camera-placeholder"><div className="camera-reticle"><Icon type="camera"/></div><h3>No camera connected</h3><p>Connect the separate ESP32-CAM on your trusted Wi-Fi network.</p><span>No simulated or prerecorded video</span></div>}
  <span className="feed-label">CAM 01 <i/> LOCAL WI-FI</span><span className="feed-corner top-left"/><span className="feed-corner bottom-right"/>
 </div><div className="camera-toolbar"><label>CAMERA IPv4<input aria-label="Camera address" placeholder="192.168.50.20" value={ip} disabled={active} onChange={e=>setIP(e.target.value)}/></label><button className="button secondary" disabled={busy} onClick={()=>active?(setActive(false),setStatus('DISCONNECTED')):void connect()}>{active?'Disconnect camera':'Connect camera'}</button><button className="button icon-button" aria-label="Snapshot" disabled={!active} onClick={()=>void snapshot()}><Icon type="camera"/></button></div>
 <details className="camera-settings"><summary>Camera settings <span>Disconnect stream before applying</span></summary><div><select aria-label="Camera resolution" value={width} disabled={active} onChange={e=>setWidth(Number(e.target.value))}><option value={320}>QVGA / 320 × 240</option><option value={640}>VGA / 640 × 480 · PSRAM required</option></select><label>JPEG quality<input aria-label="JPEG quality" type="number" min="10" max="40" value={quality} disabled={active} onChange={e=>setQuality(Number(e.target.value))}/></label><button className="button secondary" disabled={active||busy||!ip} onClick={()=>{setBusy(true);void api('camera',{ip}).then(()=>api(`camera/settings?width=${width}&quality=${quality}`,{})).then(raw=>{validate(raw);setError('');}).catch(e=>setError(String(e))).finally(()=>setBusy(false));}}>Apply</button></div></details>
 {error&&<p role="alert" className="camera-error">{error}</p>}</section>;
}
