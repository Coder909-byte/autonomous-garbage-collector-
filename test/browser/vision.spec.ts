import {test,expect} from '@playwright/test';
import {spawn} from 'node:child_process';
// Requires `npm run sim:build`. Detections are posted exactly as vision/rover_vision.py does.
const post=(targets:unknown[])=>fetch('http://127.0.0.1:18787/api/vision',{method:'POST',headers:{'Content-Type':'application/json','X-Rover-Client':'vision'},body:JSON.stringify({detector:'test',targets})});
test('camera seek steers the Wi-Fi bench firmware toward garbage and the operator can take over',async({page})=>{
 const firmware=spawn('build/rover-motor-bench-release-wifi-sim',{env:{...process.env,ROVER_SIM_WIFI_PORT:'14778'}});
 let target:unknown[]=[];const feed=setInterval(()=>void post(target).catch(()=>{}),150);
 try{
  await new Promise(r=>setTimeout(r,500));
  expect((await fetch('http://127.0.0.1:18787/api/vision',{method:'POST',headers:{'Content-Type':'application/json','X-Rover-Client':'vision',Origin:'http://evil.example'},body:'{}'})).status).toBe(403);
  await page.goto('/');
  await expect(page.getByTestId('detection-status')).toContainText('nothing in view');
  await page.getByLabel('Control source').selectOption('wifi');
  await page.getByLabel('Rover Wi-Fi address').fill('127.0.0.1:14778');
  await page.getByRole('button',{name:/Connect rover/}).click();
  await expect(page.getByText('Protocol ready')).toBeVisible({timeout:8000});
  const seek=page.getByRole('button',{name:'Camera seek',exact:true});
  await expect(seek).toBeDisabled();
  await page.getByRole('button',{name:'ARM',exact:true}).click();
  target=[{label:'bottle',conf:0.82,cx:0.5,cy:0.7,w:0.2,h:0.25}];
  await expect(page.getByTestId('detection-status')).toContainText('bottle 82%');
  await seek.click();
  await expect(seek).toHaveAttribute('aria-pressed','true');
  await expect(page.getByRole('status').filter({hasText:'APPROACH'})).toContainText('Collecting bottle');
  await expect(page.getByRole('region',{name:'Operational state'}).getByText('FORWARD',{exact:true})).toHaveCount(2);
  await page.screenshot({path:'artifacts/vision-validation/dashboard-camera-seek.png',fullPage:true});
  await page.getByRole('button',{name:'Manual',exact:true}).click();
  await expect(seek).toHaveAttribute('aria-pressed','false');
  await expect(page.getByRole('region',{name:'Operational state'}).getByText('STOPPED',{exact:true})).toHaveCount(2);
 }finally{clearInterval(feed);firmware.kill();}
});
