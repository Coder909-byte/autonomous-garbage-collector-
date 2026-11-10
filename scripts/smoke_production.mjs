// Checks built production serving only. No serial connection or camera request.
import {spawn} from 'node:child_process';
import assert from 'node:assert/strict';
const child=spawn(process.execPath,['apps/rover-bridge/dist/apps/rover-bridge/src/server.js'],{stdio:['ignore','pipe','pipe']});
let log='';child.stdout.on('data',b=>log+=b);child.stderr.on('data',b=>log+=b);
try {
 let response;
 for(let i=0;i<50;i++){
  if(child.exitCode!==null)throw Error(log);
  try{response=await fetch('http://127.0.0.1:8787/');if(response.ok)break;}catch{}
  await new Promise(r=>setTimeout(r,100));
 }
 assert(response?.ok,'Production HTTP unavailable');
 const html=await response.text();assert(html.includes('<div id="root">'));assert(html.includes('Mission Control'));
 const asset=html.match(/src="([^"]+\.js)"/);assert(asset);
 assert((await fetch('http://127.0.0.1:8787'+asset[1])).ok);
 const state=await (await fetch('http://127.0.0.1:8787/api/state')).json();assert.equal(state.connected,false);assert.equal(state.protocolReady,false);assert.equal(state.telemetry,null);
 console.log('PASS: production dashboard, compiled asset and disarmed bridge API served on loopback; no hardware opened');
} finally {
 child.kill('SIGTERM');await new Promise(resolve=>{const kill=setTimeout(()=>{child.kill('SIGKILL');resolve();},2000);child.on('exit',()=>{clearTimeout(kill);resolve();});});
}
