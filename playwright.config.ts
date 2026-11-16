import {defineConfig} from '@playwright/test';
// Isolate tests from an operator tab's automatic WebSocket reconnection.
const env={ROVER_BRIDGE_PORT:'18787',ROVER_DASHBOARD_PORT:'15173'};
export default defineConfig({testDir:'test/browser',workers:1,use:{baseURL:'http://127.0.0.1:15173',viewport:{width:1440,height:1100},launchOptions:{executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}},webServer:[{command:'npm run bridge',url:'http://127.0.0.1:18787/api/state',env,reuseExistingServer:false},{command:'npm run dashboard',url:'http://127.0.0.1:15173',env,reuseExistingServer:false}],reporter:[['list']]});
