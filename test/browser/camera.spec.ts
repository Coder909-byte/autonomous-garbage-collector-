import {test,expect} from '@playwright/test';
// Camera mocks are isolated browser test fixtures; never shipped as a real feed.
test('camera network failure stays disconnected',async({page})=>{
 await page.route('**/api/camera',r=>r.fulfill({json:{ip:'192.168.50.20'}}));
 await page.route('**/api/camera/status',r=>r.fulfill({status:502,json:{error:'TEST MOCK: camera Wi-Fi unavailable'}}));
 await page.goto('/');await page.getByLabel('Camera address').fill('192.168.50.20');await page.getByRole('button',{name:'Connect camera',exact:true}).click();
 await expect(page.getByText('TEST MOCK: camera Wi-Fi unavailable',{exact:false})).toBeVisible();await expect(page.getByText('No camera connected')).toBeVisible();await expect(page.getByAltText('Live ESP32-CAM MJPEG stream')).toHaveCount(0);
});
test('decodes a test-only multipart camera fixture, downloads JPEG and disconnects',async({page})=>{
 await page.goto('/');
 const jpeg=Buffer.from(await page.evaluate(()=>{const canvas=document.createElement('canvas');canvas.width=320;canvas.height=240;const ctx=canvas.getContext('2d')!;ctx.fillStyle='#153349';ctx.fillRect(0,0,320,240);ctx.fillStyle='white';ctx.font='20px sans-serif';ctx.fillText('TEST FIXTURE ONLY',45,120);return canvas.toDataURL('image/jpeg').split(',')[1];}),'base64');
 await page.route('**/api/camera',r=>r.fulfill({json:{ip:'192.168.50.20'}}));
 await page.route('**/api/camera/status',r=>r.fulfill({json:{ready:true,streaming:true,width:320,quality:14}}));
 await page.route('**/api/camera/stream',r=>r.fulfill({contentType:'multipart/x-mixed-replace;boundary=roverframe',body:Buffer.concat([Buffer.from(`--roverframe\r\nContent-Type: image/jpeg\r\nContent-Length: ${jpeg.length}\r\n\r\n`),jpeg,Buffer.from('\r\n--roverframe--\r\n')])}));
 await page.route('**/api/camera/snapshot',r=>r.fulfill({contentType:'image/jpeg',body:jpeg}));
 await page.getByLabel('Camera address').fill('http://192.168.50.20:81/stream');await page.getByRole('button',{name:'Connect camera',exact:true}).click();
 const image=page.getByAltText('Live ESP32-CAM MJPEG stream');await expect(image).toBeVisible();await expect.poll(()=>image.evaluate(img=>(img as HTMLImageElement).naturalWidth)).toBe(320);
 await expect(page.getByText('LIVE CAMERA',{exact:true})).toBeVisible({timeout:5000});
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Snapshot',exact:true}).click();expect((await download).suggestedFilename()).toMatch(/^rover-snapshot-.*\.jpg$/);
 await page.getByRole('button',{name:'Disconnect camera',exact:true}).click();await expect(image).toHaveCount(0);await expect(page.getByText('DISCONNECTED',{exact:true})).toBeVisible();
});
