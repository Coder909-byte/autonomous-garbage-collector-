import {test,expect} from '@playwright/test';
import {sample} from '../../apps/rover-bridge/test/fixtures';
import type {BridgeState} from '../../packages/protocol/index';

test('motor commissioning and commanded-output states remain explicit without faking physical feedback',async({page})=>{
 const messages:Record<string,unknown>[]=[];
 let acceptTestRecord=()=>{};
 await page.routeWebSocket('**/api/control',socket=>{
  const state:BridgeState={connected:true,connecting:false,protocolReady:true,simulation:false,port:'HOST-MOTOR-FIXTURE',telemetry:{...sample,armed:false,healthy:false,nav:'DISARMED',mode:'MOTOR_OPERATION',motorCapable:true,commissioningReady:false,inhibit:'COMMISSIONING_REQUIRED'},receivedAt:Date.now(),intent:null,logs:[],error:null};
  const publish=()=>{state.receivedAt=Date.now();socket.send(JSON.stringify(state));};
  socket.onMessage(raw=>{
   const m=JSON.parse(String(raw));messages.push(m);
   if(m.command==='ARM'){state.telemetry!.armed=true;state.telemetry!.nav='MANUAL';}
   if(m.type==='hold'){state.telemetry!.requested=state.telemetry!.applied=1;state.telemetry!.en=true;}
   if(m.type==='release'){state.telemetry!.requested=state.telemetry!.applied=0;state.telemetry!.en=false;}
   if(m.command==='ESTOP'){state.telemetry!.estop=true;state.telemetry!.armed=false;state.telemetry!.requested=state.telemetry!.applied=0;state.telemetry!.en=false;state.telemetry!.nav='ESTOP';}
   if(m.command==='RESET'){state.telemetry!.estop=false;state.telemetry!.nav='DISARMED';}
   publish();
  });
  const timer=setInterval(publish,200);socket.onClose(()=>clearInterval(timer));publish();
  // This test-only incoming frame models a separately reviewed build, not a UI
  // commissioning switch. Production provides no such command or endpoint.
  acceptTestRecord=()=>{state.telemetry!.commissioningReady=true;state.telemetry!.inhibit='NONE';publish();};
 });
 await page.goto('/');await expect(page.getByRole('status')).toContainText('OUTPUTS INHIBITED');
 await expect(page.getByRole('button',{name:'ARM',exact:true})).toBeDisabled();
 await expect(page.getByRole('region',{name:'Navigation visualization'})).toContainText('Front 120 cm');
 await page.screenshot({path:'artifacts/motor-operation/dashboard-inhibited.png',fullPage:true});
 acceptTestRecord();
 await expect(page.getByRole('button',{name:'ARM',exact:true})).toBeEnabled();await page.getByRole('button',{name:'ARM',exact:true}).click();
 await page.keyboard.down('w');await expect(page.getByRole('region',{name:'Operational state'})).toContainText('COMMANDED ACTIVE');await page.keyboard.up('w');
 await expect(page.getByText('LOW · no physical interlock',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:/SOFTWARE EMERGENCY STOP/}).click();await expect(page.getByText('LATCHED',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Reset firmware E-stop latch'}).click();await expect(page.getByRole('button',{name:'Forward',exact:true})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Connect camera',exact:true})).toBeEnabled();
 expect(messages.some(m=>m.type==='hold')).toBe(true);
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'artifacts/motor-operation/dashboard-motor-mobile.png',fullPage:true});
});
