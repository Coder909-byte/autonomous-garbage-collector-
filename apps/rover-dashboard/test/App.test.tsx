// @vitest-environment jsdom
import {act,cleanup,fireEvent,render,screen} from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import {afterEach,beforeEach,it,expect,vi} from 'vitest';
import App from '../src/App';
import {HoldControl} from '../src/control';
import {sample} from '../../rover-bridge/test/fixtures';
import type {BridgeState} from '../../../packages/protocol/index';
class Socket {
 static OPEN=1;static current:Socket;readyState=1;onopen:()=>void=()=>{};onmessage:(e:{data:string})=>void=()=>{};onclose:()=>void=()=>{};onerror:()=>void=()=>{};
 sent:Record<string,unknown>[]=[];constructor(){Socket.current=this;}
 send(s:string){this.sent.push(JSON.parse(s));}close(){this.readyState=3;}
}
const connected:BridgeState={connected:true,connecting:false,protocolReady:true,simulation:true,port:'SIMULATION',telemetry:{...sample,armed:false,nav:'DISARMED'},receivedAt:Date.now(),intent:null,logs:[],error:null};
function mount(state=connected){render(<App/>);act(()=>vi.advanceTimersByTime(0));act(()=>Socket.current.onopen());act(()=>Socket.current.onmessage({data:JSON.stringify({...state,receivedAt:Date.now()})}));}
function update(change:Partial<BridgeState['telemetry']>){act(()=>Socket.current.onmessage({data:JSON.stringify({...connected,receivedAt:Date.now(),telemetry:{...sample,...change}})}));}
beforeEach(()=>{vi.useFakeTimers();vi.stubGlobal('WebSocket',Socket);vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url==='/api/diagnostics'?{count:0,capacity:10000,dropped:0,samples:[],events:[]}:[]})));vi.spyOn(document,'hasFocus').mockReturnValue(true);});
afterEach(()=>{cleanup();vi.useRealTimers();vi.unstubAllGlobals();});
it('renders disconnected camera, simulation label, firmware and real readings',()=>{mount();expect(screen.getByText('No camera connected')).toBeInTheDocument();expect(screen.getAllByText('SIMULATION MODE').length).toBeGreaterThan(0);expect(screen.getByText('120')).toBeInTheDocument();expect(screen.getByText('rover-usb-v1')).toBeInTheDocument();expect(screen.getByText('not measured')).toBeInTheDocument();});
it('ARM is explicit and does not send a direction',()=>{mount();fireEvent.click(screen.getByRole('button',{name:'ARM',exact:true}));expect(Socket.current.sent).toContainEqual({type:'command',command:'ARM'});expect(Socket.current.sent.some(m=>m.type==='hold')).toBe(false);});
it('keyboard movement renews only while held and keyup stops',()=>{mount();update({armed:true});fireEvent.keyDown(window,{key:'w',code:'KeyW'});act(()=>vi.advanceTimersByTime(170));expect(Socket.current.sent.filter(m=>m.type==='hold').length).toBe(3);fireEvent.keyUp(window,{key:'w'});const count=Socket.current.sent.length;act(()=>vi.advanceTimersByTime(250));expect(Socket.current.sent.length).toBe(count);expect(Socket.current.sent.at(-1)).toEqual({type:'release'});});
it('pointer release/cancel and browser blur stop leases',()=>{mount();update({armed:true});const forward=screen.getByRole('button',{name:'Forward',exact:true});fireEvent.pointerDown(forward,{button:0,pointerId:1});fireEvent.pointerUp(forward,{pointerId:1});fireEvent.keyDown(window,{key:'d'});fireEvent.blur(window);expect(Socket.current.sent.at(-1)).toEqual({type:'release'});});
it('Space stops and mode change ends active hold',()=>{mount();update({armed:true});fireEvent.keyDown(window,{key:'w'});fireEvent.keyDown(window,{key:' ',code:'Space'});expect(Socket.current.sent.at(-1)).toEqual({type:'command',command:'S'});fireEvent.click(screen.getByRole('button',{name:'Autonomous',exact:true}));expect(Socket.current.sent.at(-1)).toEqual({type:'command',command:'AUTO'});});
it('software emergency stop sends ESTOP and shows physical cutoff distinction',()=>{mount();fireEvent.click(screen.getByRole('button',{name:/SOFTWARE EMERGENCY STOP/}));expect(Socket.current.sent.at(-1)).toEqual({type:'command',command:'ESTOP'});expect(screen.getByText(/physical cutoff still required/)).toBeInTheDocument();});
it('requested cleaning stays distinct from applied state',()=>{mount();update({brushReq:true,brush:false});expect(screen.getByRole('button',{name:'Brushes OFF'})).toHaveAttribute('aria-pressed','true');expect(screen.getAllByText('OFF',{exact:true}).length).toBeGreaterThan(0);fireEvent.click(screen.getByRole('button',{name:'Brushes OFF'}));expect(Socket.current.sent.at(-1)).toEqual({type:'command',command:'BRUSH OFF'});});
it('stale telemetry disables movement and masks sensor values',()=>{mount();update({armed:true});act(()=>vi.advanceTimersByTime(1300));expect(screen.getByText('STALE TELEMETRY')).toBeInTheDocument();expect(screen.getByRole('button',{name:'Forward',exact:true})).toBeDisabled();expect(screen.queryByText('120')).not.toBeInTheDocument();});
it('disconnection disables controls and reports delivery uncertainty',()=>{mount();act(()=>Socket.current.onclose());expect(screen.getByRole('button',{name:'ARM',exact:true})).toBeDisabled();expect(screen.getByRole('alert')).toHaveTextContent('STOP delivery is unconfirmed');});
it('invalid server responses close control rather than populate invented state',()=>{mount();act(()=>Socket.current.onmessage({data:'{"connected":true}'}));expect(screen.getByRole('alert')).toHaveTextContent('Invalid server response');expect(Socket.current.readyState).toBe(3);});
it('camera failures remain explicit and create no fake stream',async()=>{mount();vi.stubGlobal('fetch',vi.fn(async()=>({ok:false,json:async()=>({error:'camera offline'})})));fireEvent.change(screen.getByLabelText('Camera address'),{target:{value:'192.168.50.20'}});await act(async()=>{fireEvent.click(screen.getByRole('button',{name:'Connect camera',exact:true}));});expect(screen.getByText(/camera offline/)).toBeInTheDocument();expect(screen.queryByAltText('Live ESP32-CAM MJPEG stream')).not.toBeInTheDocument();});
it('HoldControl releases on visibility/focus loss and does not extend stale intent',()=>{const send=vi.fn();const hold=new HoldControl(send);hold.start('L','key:a');vi.spyOn(document,'hasFocus').mockReturnValue(false);vi.advanceTimersByTime(100);expect(send).toHaveBeenLastCalledWith({type:'release'});const n=send.mock.calls.length;vi.advanceTimersByTime(300);expect(send).toHaveBeenCalledTimes(n);hold.release();});
it('never displays stale ARMED state or selected control mode as current',()=>{mount();update({armed:true});act(()=>vi.advanceTimersByTime(1300));expect(screen.queryByText('ARMED',{exact:true})).not.toBeInTheDocument();expect(screen.getByRole('button',{name:'Manual',exact:true})).not.toHaveClass('selected');expect(screen.getByRole('region',{name:'Navigation visualization'})).toHaveTextContent('No fresh firmware decision');});
it('displays invalid readings and prominent sensor fault disarm without inventing motion',()=>{mount();update({armed:false,nav:'SENSOR_FAULT',cm:[-1,100,70]});expect(screen.getByRole('alert')).toHaveTextContent('SENSOR_FAULT');expect(screen.getByRole('region',{name:'Navigation visualization'})).toHaveTextContent('Fresh readings alone never restart');expect(screen.getByRole('button',{name:'Forward',exact:true})).toBeDisabled();expect(screen.getAllByText('INVALID / STALE')).toHaveLength(1);});
it('discovers hotplugged ports automatically while preserving manual selection and never opens them',async()=>{
 let available=[{path:'/dev/mock-a',label:'A'},{path:'/dev/mock-b',label:'B'}];
 vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url==='/api/ports'?available:{count:0,capacity:10000,dropped:0,samples:[],events:[]}})));
 mount({...connected,connected:false,protocolReady:false,telemetry:null,receivedAt:null});
 fireEvent.change(screen.getByLabelText('Control source'),{target:{value:'hardware'}});await act(async()=>{});
 expect(screen.getByLabelText('Serial port')).toHaveValue('/dev/mock-a');fireEvent.change(screen.getByLabelText('Serial port'),{target:{value:'/dev/mock-b'}});
 await act(async()=>{vi.advanceTimersByTime(3000);});expect(screen.getByLabelText('Serial port')).toHaveValue('/dev/mock-b');
 available=[];await act(async()=>{vi.advanceTimersByTime(3000);});expect(screen.getByLabelText('Serial port')).toHaveValue('');expect(screen.getByRole('button',{name:/Connect rover/})).toBeDisabled();expect(Socket.current.sent.some(m=>m.type==='connect')).toBe(false);
});
it('camera status alone cannot claim live video and missing decoded frames time out',async()=>{
 mount();vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url.startsWith('/api/camera')?{ready:true,streaming:true,width:320,quality:14}:url==='/api/ports'?[]:{count:0,capacity:10000,dropped:0,samples:[],events:[]}})));
 fireEvent.change(screen.getByLabelText('Camera address'),{target:{value:'http://192.168.50.20'}});
 await act(async()=>{fireEvent.click(screen.getByRole('button',{name:'Connect camera',exact:true}));});
 await act(async()=>{vi.advanceTimersByTime(2000);});expect(screen.queryByText('LIVE CAMERA',{exact:true})).not.toBeInTheDocument();
 await act(async()=>{vi.advanceTimersByTime(10000);});expect(screen.getByText(/No decoded video received/)).toBeInTheDocument();expect(screen.queryByAltText('Live ESP32-CAM MJPEG stream')).not.toBeInTheDocument();
});
it('separates physical safety feedback from the firmware latch and matches the actual connected source',()=>{
 mount({...connected,simulation:false,port:'/dev/mock'});expect(screen.getByLabelText('Control source')).toHaveValue('hardware');update({armed:false,estop:true,healthy:true,nav:'ESTOP'});
 expect(screen.getByText('HIGH · healthy',{exact:true})).toBeInTheDocument();expect(screen.getByText('LATCHED',{exact:true})).toBeInTheDocument();
});
it('diagnostic USB remains connected with real ranges while all motor controls are unavailable',()=>{
 mount({...connected,simulation:false,port:'USB-BENCH-MOCK',telemetry:{...sample,armed:false,healthy:false,nav:'DISARMED',mode:'USB_BENCH_DIAGNOSTIC',motorCapable:false}});
 expect(screen.getByRole('status')).toHaveTextContent('USB BENCH DIAGNOSTIC · NO MOTOR POWER');
 expect(screen.getByText('120')).toBeInTheDocument();expect(screen.getByText('LOW · diagnostic input')).toBeInTheDocument();
 for(const name of ['ARM','Autonomous','Forward','Backward','Left','Right','CLEAN ON','Brushes ON','Conveyor ON'])expect(screen.getByRole('button',{name,exact:true})).toBeDisabled();
 fireEvent.keyDown(window,{key:'w',code:'KeyW'});expect(Socket.current.sent.some(m=>m.type==='hold')).toBe(false);
 expect(screen.getByRole('region',{name:'Navigation visualization'})).toHaveTextContent('ARM and AUTO are unavailable');
 expect(screen.getByRole('button',{name:/SOFTWARE EMERGENCY STOP/})).toBeEnabled();
 expect(screen.getByRole('button',{name:'Connect camera',exact:true})).toBeEnabled();
});
it('diagnostic software stop can be explicitly reset with LOW feedback and never offers ARM',()=>{
 mount({...connected,simulation:false,port:'USB-BENCH-MOCK',telemetry:{...sample,armed:false,healthy:false,estop:true,nav:'ESTOP',mode:'USB_BENCH_DIAGNOSTIC',motorCapable:false}});
 const reset=screen.getByRole('button',{name:'Reset firmware E-stop latch'});expect(reset).toBeEnabled();
 fireEvent.click(reset);expect(Socket.current.sent.at(-1)).toEqual({type:'command',command:'RESET'});
 expect(screen.getByRole('button',{name:'ARM',exact:true})).toBeDisabled();
 fireEvent.click(screen.getByRole('button',{name:/SOFTWARE EMERGENCY STOP/}));expect(Socket.current.sent.at(-1)).toEqual({type:'command',command:'ESTOP'});
});
it('shows MOTOR_OPERATION as inhibited until its commissioning record is accepted',()=>{
 mount({...connected,simulation:false,telemetry:{...sample,armed:false,healthy:false,nav:'DISARMED',mode:'MOTOR_OPERATION',motorCapable:true,commissioningReady:false,inhibit:'COMMISSIONING_REQUIRED'}});
 expect(screen.getByRole('status')).toHaveTextContent('OUTPUTS INHIBITED · COMMISSIONING REQUIRED');
 expect(screen.getByText('LOW · no physical interlock')).toBeInTheDocument();expect(screen.getByText('120')).toBeInTheDocument();
 for(const name of ['ARM','Autonomous','Forward','CLEAN ON'])expect(screen.getByRole('button',{name,exact:true})).toBeDisabled();
 expect(screen.getByRole('region',{name:'Operational state'})).toHaveTextContent('INHIBITED · COMMISSIONING REQUIRED');
 expect(screen.getByRole('button',{name:'Connect camera',exact:true})).toBeEnabled();
});
it('released MOTOR_OPERATION supports software arming/movement with raw GPIO27 LOW',()=>{
 mount({...connected,simulation:false,telemetry:{...sample,armed:false,healthy:false,nav:'DISARMED',mode:'MOTOR_OPERATION',motorCapable:true,commissioningReady:true,inhibit:'NONE'}});
 fireEvent.click(screen.getByRole('button',{name:'ARM',exact:true}));expect(Socket.current.sent.at(-1)).toEqual({type:'command',command:'ARM'});
 update({armed:true,healthy:false,nav:'MANUAL',mode:'MOTOR_OPERATION',motorCapable:true,commissioningReady:true,inhibit:'NONE'});
 fireEvent.keyDown(window,{key:'w',code:'KeyW'});expect(Socket.current.sent.at(-1)).toEqual({type:'hold',direction:'F'});
 update({armed:true,healthy:false,requested:1,applied:1,en:true,nav:'MANUAL',mode:'MOTOR_OPERATION',motorCapable:true,commissioningReady:true,inhibit:'NONE'});
 expect(screen.getByText('COMMANDED ACTIVE')).toBeInTheDocument();expect(screen.getByText('not measured')).toBeInTheDocument();
 update({armed:false,healthy:false,requested:0,applied:0,en:false,nav:'DISARMED',mode:'MOTOR_OPERATION',motorCapable:true,commissioningReady:true,inhibit:'COMMAND_TIMEOUT'});
 expect(screen.getByRole('button',{name:'Forward',exact:true})).toBeDisabled();expect(Socket.current.sent.at(-1)).toEqual({type:'release'});
});
