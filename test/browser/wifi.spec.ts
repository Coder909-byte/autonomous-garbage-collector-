import {test,expect} from '@playwright/test';
import {spawn} from 'node:child_process';
// Requires `npm run sim:build`; the host Wi-Fi stub listens on loopback only.
test('operator drives Wi-Fi bench firmware through the real bridge; key release stops',async({page})=>{
 const firmware=spawn('build/rover-motor-bench-release-wifi-sim',{env:{...process.env,ROVER_SIM_WIFI_PORT:'14777'}});
 try{
  await new Promise(r=>setTimeout(r,500));
  await page.goto('/');
  await page.getByLabel('Control source').selectOption('wifi');
  await expect(page.getByText('ROVER-CTRL')).toBeVisible();
  await page.getByLabel('Rover Wi-Fi address').fill('127.0.0.1:14777');
  await page.getByRole('button',{name:/Connect rover/}).click();
  await expect(page.getByText('Protocol ready')).toBeVisible({timeout:8000});
  await page.getByRole('button',{name:'ARM',exact:true}).click();
  await page.getByRole('button',{name:'CLEAN ON',exact:true}).click();
  await page.mouse.click(5,5);await page.keyboard.down('w');
  await expect(page.getByRole('region',{name:'Operational state'}).getByText('FORWARD',{exact:true})).toHaveCount(2);
  await page.keyboard.up('w');
  await expect(page.getByRole('region',{name:'Operational state'}).getByText('STOPPED',{exact:true})).toHaveCount(2);
 }finally{firmware.kill();}
});
