import {test,expect} from '@playwright/test';
// Camera mocks are isolated browser test fixtures; never shipped as a real feed.
test('camera network failure stays disconnected',async({page})=>{
 await page.route('**/api/camera',r=>r.fulfill({json:{ip:'192.168.50.20'}}));
 await page.route('**/api/camera/status',r=>r.fulfill({status:502,json:{error:'TEST MOCK: camera Wi-Fi unavailable'}}));
 await page.goto('/');await page.getByLabel('Camera address').fill('192.168.50.20');await page.getByRole('button',{name:'Connect camera',exact:true}).click();
 await expect(page.getByText('TEST MOCK: camera Wi-Fi unavailable',{exact:false})).toBeVisible();await expect(page.getByText('No camera connected')).toBeVisible();await expect(page.getByAltText('Live ESP32-CAM MJPEG stream')).toHaveCount(0);
});
