const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const html = fs.readFileSync('wuphf/web.html', 'utf8');
const render = html.match(/function renderBackground\(s\)\{[\s\S]*?\n\}/)[0];
const poll = html.match(/async function backgroundStatus\(\)\{[^\n]*\}/)[0];
const elements = {};
let timer, timeout, calls = 0;
const states = [
  {scheduler:'enabled',last_check:100,check_status:'recent',last_error:false,failures:['gmail']},
  {scheduler:'disabled',last_check:100,check_status:'stale',last_error:false,failures:['gmail']}
];
const ctx = {renderSetup(){},Date, Number, AbortController, lastBackground:null, backgroundTimer:null, backgroundInFlight:false,
  $:id=>elements[id]||(elements[id]={textContent:''}),
  t:(key,values={})=>key+(values.channels?' '+values.channels:''),locale:()=> 'en',
  api:async()=>states[calls++], setTimeout:(fn,ms)=>(ms===60000?timer=fn:timeout=fn,1),clearTimeout:()=>{}};
vm.createContext(ctx);vm.runInContext(html.match(/function dateTime\(value\)\{[^\n]*\}/)[0]+'\n'+render+'\n'+poll,ctx);
(async()=>{
  await ctx.backgroundStatus();
  assert.equal(elements['scheduler-status'].textContent,'scheduler_enabled');
  assert.equal(elements['background-failures'].textContent,'notify_failed gmail');
  assert.equal(typeof timer,'function');
  await timer();
  assert.equal(calls,2);
  assert.equal(elements['scheduler-status'].textContent,'scheduler_disabled');
  assert.equal(elements['background-check-status'].textContent,'check_stale');
  let release; let concurrent=0;
  ctx.api=()=>{concurrent++;return new Promise(resolve=>{release=resolve})};
  const first=ctx.backgroundStatus();
  await ctx.backgroundStatus();
  assert.equal(concurrent,1);
  release(states[1]); await first;
  ctx.api=(path,method,data,signal)=>new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(new Error('timeout'))));
  const hung=ctx.backgroundStatus();
  assert.equal(typeof timeout,'function');
  timeout(); await hung;
  assert.equal(elements['scheduler-status'].textContent,'scheduler_unknown');
  console.log('Background polling updates scheduler, age and channel failures without overlapping or hanging.');
})().catch(e=>{console.error(e);process.exitCode=1});
