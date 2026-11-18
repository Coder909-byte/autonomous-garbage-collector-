import {test,expect} from '@playwright/test';
import {sample} from '../../apps/rover-bridge/test/fixtures';
import type {BridgeState} from '../../packages/protocol/index';

test('bench telemetry keeps sensors/camera available and disables every motor control',async({page})=>{
 const commands:string[]=[];
 await page.routeWebSocket('**/api/control',socket=>{
  const state:BridgeState={connected:true,connecting:false,protocolReady:true,simulation:false,port:'MOCK-BENCH-ONLY',telemetry:{...sample,armed:false,healthy:false,nav:'DISARMED',mode:'USB_BENCH_DIAGNOSTIC',motorCapable:false},receivedAt:Date.now(),intent:null,logs:[],error:null};
  const publish=()=>{state.receivedAt=Date.now();socket.send(JSON.stringify(state));};
  socket.onMessage(raw=>{
   const message=JSON.parse(String(raw));commands.push(message.command??message.type);
   if(message.command==='ESTOP'){state.telemetry!.estop=true;state.telemetry!.nav='ESTOP';}
   if(message.command==='RESET'){state.telemetry!.estop=false;state.telemetry!.nav='DISARMED';}
   publish();
  });
  const timer=setInterval(publish,250);socket.onClose(()=>clearInterval(timer));publish();
 });
 await page.goto('/');
 await expect(page.getByRole('status')).toContainText('USB BENCH DIAGNOSTIC · NO MOTOR POWER');
 await expect(page.getByRole('region',{name:'Navigation visualization'})).toContainText('Front 120 cm');
 for(const name of ['ARM','Autonomous','Forward','Backward','Left','Right','CLEAN ON','Brushes ON','Conveyor ON'])await expect(page.getByRole('button',{name,exact:true})).toBeDisabled();
 await expect(page.getByRole('button',{name:'Connect camera',exact:true})).toBeEnabled();
 await page.keyboard.press('w');expect(commands).not.toContain('hold');
 await page.getByRole('button',{name:/SOFTWARE EMERGENCY STOP/}).click();
 await expect(page.getByText('LATCHED',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Reset firmware E-stop latch'}).click();
 await expect(page.locator('.telemetry-strip').getByText('CLEAR',{exact:true})).toBeVisible();
 expect(commands).toEqual(['ESTOP','RESET']);
 await page.screenshot({path:'artifacts/usb-bench-diagnostic/dashboard-bench.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'artifacts/usb-bench-diagnostic/dashboard-bench-mobile.png',fullPage:true});
});
