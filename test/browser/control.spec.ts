import {test,expect} from '@playwright/test';
test('operator drives real C++ simulator, releases, cleans, switches modes and latches stop',async({page})=>{
 await page.goto('/');await expect(page.getByRole('button',{name:'Connect rover',exact:false})).toBeEnabled();
 await expect(page.getByText('No camera connected')).toBeVisible();
 await page.getByRole('button',{name:'Connect rover',exact:false}).click();await expect(page.getByText('SIMULATION MODE',{exact:true}).first()).toBeVisible();
 await expect(page.getByRole('button',{name:'ARM',exact:true})).toBeEnabled();await page.getByRole('button',{name:'ARM',exact:true}).click();
 const forward=page.getByRole('button',{name:'Forward',exact:true});await expect(forward).toBeEnabled();
 await page.getByRole('button',{name:'CLEAN ON',exact:true}).click();await expect(page.getByRole('button',{name:'Brushes OFF'})).toHaveAttribute('aria-pressed','true');
 await page.keyboard.down('w');await expect(page.getByRole('region',{name:'Operational state'}).getByText('FORWARD',{exact:true})).toHaveCount(2);await page.keyboard.up('w');await expect(page.getByRole('region',{name:'Operational state'}).getByText('STOPPED',{exact:true})).toHaveCount(2);
 await page.getByRole('button',{name:'Autonomous',exact:true}).click();await expect(page.getByRole('region',{name:'Operational state'}).getByText('CRUISE',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Manual',exact:true}).click();await expect(page.getByRole('region',{name:'Operational state'}).getByText('STOPPED',{exact:true})).toHaveCount(2);
 await page.getByRole('button',{name:/SOFTWARE EMERGENCY STOP/}).click();await expect(page.getByText('LATCHED',{exact:true})).toBeVisible();await expect(forward).toBeDisabled();
 await page.screenshot({path:'artifacts/dashboard-simulation.png',fullPage:true});
});
test('browser blur and pointer release stop; reconnect remains disarmed',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Connect rover',exact:false}).click();await page.getByRole('button',{name:'ARM',exact:true}).click();
 const button=page.getByRole('button',{name:'Forward',exact:true});await expect(button).toBeEnabled();const box=await button.boundingBox();await page.mouse.move(box!.x+20,box!.y+20);await page.mouse.down();await expect(page.getByRole('region',{name:'Operational state'}).getByText('FORWARD',{exact:true})).toHaveCount(2);await page.mouse.up();await expect(page.getByRole('region',{name:'Operational state'}).getByText('STOPPED',{exact:true})).toHaveCount(2);
 await page.keyboard.down('d');await expect(page.getByRole('region',{name:'Operational state'}).getByText('RIGHT',{exact:true})).toHaveCount(2);await page.evaluate(()=>window.dispatchEvent(new Event('blur')));await expect(page.getByRole('region',{name:'Operational state'}).getByText('STOPPED',{exact:true})).toHaveCount(2);await page.keyboard.up('d');
 await page.getByRole('button',{name:'Disconnect rover',exact:true}).click();await page.getByRole('button',{name:'Connect rover',exact:false}).click();await expect(page.getByRole('button',{name:'ARM',exact:true})).toBeEnabled();await expect(button).toBeDisabled();
});
test('responsive disconnected station has no horizontal overflow',async({page})=>{await page.setViewportSize({width:390,height:844});await page.goto('/');await expect(page.getByText('No camera connected')).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:'artifacts/dashboard-mobile.png',fullPage:true});});
