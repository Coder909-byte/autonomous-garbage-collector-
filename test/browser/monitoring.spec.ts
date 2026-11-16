import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';

test('records firmware decisions and exports source-labelled diagnostics after disconnect',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await page.getByLabel('Scenario').selectOption('obstacle');await page.getByRole('button',{name:'Connect rover',exact:false}).click();
 await page.getByRole('button',{name:'ARM',exact:true}).click();await page.getByRole('button',{name:'Autonomous',exact:true}).click();
 const navigation=page.getByRole('region',{name:'Navigation visualization'});
 await expect(navigation).toContainText('Front 25 cm',{timeout:6000});
 await expect(page.getByRole('region',{name:'Diagnostics recording'})).toContainText('SIMULATION · SIMULATION');
 await page.screenshot({path:'artifacts/monitoring-validation/dashboard-navigation.png',fullPage:true});
 await page.getByRole('button',{name:'Disconnect rover',exact:true}).click();await expect(page.getByRole('button',{name:'ARM',exact:true})).toBeDisabled();
 const download=page.waitForEvent('download');await page.getByRole('link',{name:'Export JSON'}).click();const file=await download;
 const data=JSON.parse(await readFile((await file.path())!,'utf8'));expect(data.records.length).toBeGreaterThan(0);
 expect(data.records.filter((r:{event:string})=>r.event==='telemetry').every((r:{source:string})=>r.source==='simulation')).toBe(true);
 expect(data.records.some((r:{telemetry?:{cm:number[]}})=>r.telemetry?.cm[0]===25)).toBe(true);
 expect(data.records.some((r:{telemetry?:{requested:number;applied:number}})=>r.telemetry?.requested===1&&r.telemetry.applied===1)).toBe(true);
 const csvDownload=page.waitForEvent('download');await page.getByRole('link',{name:'Export CSV'}).click();const csv=await readFile((await (await csvDownload).path())!,'utf8');expect(csv).toContain('"requested","applied"');expect(csv).toContain('"simulation"');
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 expect(errors).toEqual([]);await page.screenshot({path:'artifacts/monitoring-validation/dashboard-trends-mobile.png',fullPage:true});
});

test('control-channel recovery never reconnects or rearms the simulator',async({page})=>{
 await page.addInitScript(()=>{const Original=window.WebSocket;window.WebSocket=class extends Original{constructor(url:string|URL,protocols?:string|string[]){super(url,protocols);(window as unknown as {controlSocket:WebSocket}).controlSocket=this;}};});
 await page.goto('/');await page.getByRole('button',{name:'Connect rover',exact:false}).click();await page.getByRole('button',{name:'ARM',exact:true}).click();
 await expect(page.getByRole('button',{name:'Forward',exact:true})).toBeEnabled();await page.evaluate(()=>(window as unknown as {controlSocket:WebSocket}).controlSocket.close());
 await expect(page.getByText('NO ROVER CONNECTED',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Forward',exact:true})).toBeDisabled();
 await page.getByRole('button',{name:'Connect rover',exact:false}).click();await expect(page.getByRole('button',{name:'ARM',exact:true})).toBeEnabled();await expect(page.getByRole('button',{name:'Forward',exact:true})).toBeDisabled();
});
