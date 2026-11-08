// Exercise the shipped browser script; only the DOM and network boundary are substituted.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('wuphf/web.html','utf8');
const elements={}, tests=[], timers=[], downloads=[];
function element(id){return elements[id]||(elements[id]={value:'',checked:false,disabled:false,hidden:false,textContent:'',files:[],children:[],attributes:{},setAttribute(name,value){this.attributes[name]=value},getAttribute(name){return this.attributes[name]},click(){downloads.push(this.download)},listeners:{},dataset:{},classList:{add(){},remove(){}},focus(){},select(){},replaceChildren(...children){this.children=children},addEventListener(type,fn){(this.listeners[type]??=[]).push(fn)},async dispatch(type){for(const fn of this.listeners[type]||[])await fn({preventDefault(){},target:this})}})}
for(const tag of html.matchAll(/<[^>]+\bid="([^"]+)"[^>]*>/g)){element(tag[1]).disabled=/\bdisabled\b/.test(tag[0]);}
for(const tag of html.matchAll(/<button[^>]+class="[^"]*\btest\b[^"]*"[^>]*>/g)){const b=element('test-'+tag[0].match(/data-channel="([^"]+)"/)[1]);b.disabled=/\bdisabled\b/.test(tag[0]);b.dataset.channel=tag[0].match(/data-channel="([^"]+)"/)[1];tests.push(b)}
const ctx={console,Date,Intl,Number,AbortController,setTimeout:(fn,ms)=>(timers.push({fn,ms}),timers.length),clearTimeout(){},setInterval:()=>1,confirm:()=>true,window:{confirm:()=>true},NodeFilter:{SHOW_TEXT:4},document:{body:{},documentElement:{},getElementById:element,querySelector:s=>element(s),querySelectorAll:s=>s==='.test'?tests:[],createTreeWalker:()=>({nextNode:()=>null}),createElement:()=>element('created-'+Math.random())}};
vm.createContext(ctx);vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1].replace(/boot\(\);\s*$/,''),ctx);
const originalBackgroundStatus=ctx.backgroundStatus;
const catalog=JSON.parse(fs.readFileSync('wuphf/translations.json'));
ctx.catalog=catalog;vm.runInContext('translations=catalog',ctx);
for(const [language,strings] of Object.entries(catalog))assert(!/OAuth|JSON/.test(strings.google_restriction),language+' normal Google setup must not require developer client files');
const googleWarnings=[...html.matchAll(/<p class="warning" data-i18n="google_restriction">([^<]+)<\/p>/g)];
assert.equal(googleWarnings.length,2);for(const warning of googleWarnings)assert.equal(warning[1],catalog.en.google_restriction,'Inline Google guidance must match the simplified English translation');

const calls=[];let failSave=false,failTest=false;
ctx.api=async(path,method,data)=>{calls.push([path,method,data]);if(path==='/api/settings'&&method==='POST'){if(failSave)throw Error('save failed');return {ok:true}}if(path==='/api/test'){if(failTest)throw Error('test failed');return {ok:true}}if(path==='/api/settings')return {advance_days:7,repeat_hours:24,language:'en',channels:{telegram:{chat_id:'123'}}};throw Error('Unexpected '+path)};
(async()=>{
 assert(tests.every(b=>b.disabled),'Tests must start disabled while settings are loading');
 assert(element('install').disabled,'Enable must start disabled');
 assert(element('calendar-download').disabled,'Calendar export starts unavailable until Codex data is complete');
 await ctx.settings();
 assert.equal(element('test-telegram').disabled,false);
 assert.equal(element('install').disabled,true,'Saved configuration is not evidence of an accepted test');
 element('telegram-chat').value='456';await element('settings').dispatch('input');
 assert(element('test-telegram').disabled,'Editing must block tests of the stale saved destination');
 const before=calls.length;await element('test-telegram').dispatch('click');assert.equal(calls.length,before,'Guard must prevent stale requests even when invoked programmatically');
 failSave=true;await element('settings').dispatch('submit');assert(element('test-telegram').disabled);assert.equal(element('settings-state').textContent,catalog.en.setup_unsaved);assert.equal(element('flash').dataset.error,'true');assert.equal(element('flash').getAttribute('role'),'alert');assert.equal(element('flash').getAttribute('aria-live'),'assertive');
 failSave=false;await element('settings').dispatch('submit');assert.equal(calls.at(-1)[2].channels.telegram.chat_id,'456');assert.equal(element('flash').dataset.error,'false');assert.equal(element('flash').getAttribute('role'),'status');assert.equal(element('flash').getAttribute('aria-live'),'polite');assert(/\.flash\[data-error="false"\]\s*\{[^}]*color:\s*var\(--accent\)/.test(html),'Successful status must use the existing blue accent');assert(!element('test-telegram').disabled);
 failTest=true;await element('test-telegram').dispatch('click');assert(element('install').disabled);assert.equal(element('test-state-telegram').textContent,catalog.en.test_failed);assert.equal(element('flash').dataset.error,'true');
 failTest=false;await element('test-telegram').dispatch('click');assert(!element('install').disabled);assert(element('test-state-telegram').textContent.includes('accepted'));assert(!element('test-state-telegram').textContent.includes('received'));
 element('telegram-token').value='new-secret';await element('settings').dispatch('input');assert(element('install').disabled);assert.equal(element('test-state-telegram').textContent,catalog.en.test_not_checked);
 await element('settings').dispatch('submit');
 element('setup-ack').checked=true;await element('setup-ack').dispatch('change');assert(!element('install').disabled,'Earlier manual receipt acknowledgement avoids forcing another message');
 element('use-gmail').checked=true;await element('settings').dispatch('change');await element('settings').dispatch('submit');ctx.renderGmail({state:'disconnected'});assert(element('test-gmail').disabled);assert(element('gmail-disconnect').disabled);
 ctx.renderGmail({state:'saved'});assert(!element('test-gmail').disabled);assert(!element('gmail-disconnect').disabled);
 ctx.renderGoogle({state:'disconnected',message:'Not connected'});assert(element('google-sync').disabled);assert(element('google-disconnect').disabled);
 ctx.renderGoogle({state:'saved'});assert(element('google-sync').disabled,'Incomplete Codex data cannot sync');
 ctx.renderStatus({count:0,complete:true,credits:[]});assert.equal(element('count').textContent,0);assert.equal(element('status-note').textContent,catalog.en.status_zero);assert(!element('google-sync').disabled);
 ctx.renderStatus({count:null,complete:false,credits:[{expires:null}]});assert.equal(element('count').textContent,'?');assert.equal(element('status-note').textContent,catalog.en.status_unavailable);assert.equal(element('dates').children[0].textContent,catalog.en.expiry_unknown);assert(element('google-sync').disabled);
 ctx.renderStatus({count:1,complete:true,credits:[{expires:'2026-11-20T12:00:00Z'}]});assert(/2026/.test(element('dates').children[0].textContent));assert(/UTC|GMT/.test(element('dates').children[0].textContent),'Expiry includes an explicit timezone');
 const normalApi=ctx.api;let release;
 ctx.api=async(path,...args)=>path==='/api/test'?new Promise(resolve=>{release=resolve}):normalApi(path,...args);
 element('use-gmail').checked=false;await element('settings').dispatch('change');await element('settings').dispatch('submit');
 const pending=element('test-telegram').dispatch('click');assert(element('test-telegram').disabled,'A pending test blocks duplicate sends');
 element('telegram-chat').value='789';await element('settings').dispatch('input');release({ok:true});await pending;
 assert(element('install').disabled,'A test of the old revision cannot verify an edited destination');assert.equal(element('test-state-telegram').textContent,catalog.en.test_not_checked);
 let saveRelease;ctx.api=async(path,method,...args)=>path==='/api/settings'&&method==='POST'?new Promise(resolve=>{saveRelease=resolve}):normalApi(path,method,...args);
 const saving=element('settings').dispatch('submit');element('telegram-token').value='newer-secret';await element('settings').dispatch('input');saveRelease({ok:true});await saving;
 assert(element('test-telegram').disabled,'An edit during save must remain unsaved');assert.equal(element('telegram-token').value,'newer-secret','A save must not erase a newer unsaved token');
 ctx.api=normalApi;await element('settings').dispatch('submit');
 element('use-gmail').checked=true;await element('settings').dispatch('change');await element('settings').dispatch('submit');ctx.renderGmail({state:'saved'});element('setup-ack').checked=true;await element('setup-ack').dispatch('change');assert(!element('install').disabled);
 let authRelease;ctx.api=()=>new Promise(resolve=>{authRelease=resolve});const auth=element('gmail-connect').onclick();assert(element('test-gmail').disabled,'Reauthorizing must invalidate earlier Gmail readiness immediately');assert(element('install').disabled);authRelease({ok:true});ctx.api=async()=>({state:'disconnected'});await auth;
 ctx.api=normalApi;ctx.renderGmail({state:'saved'});element('setup-ack').checked=true;await element('setup-ack').dispatch('change');
 let disconnectRelease;ctx.api=()=>new Promise(resolve=>{disconnectRelease=resolve});const disconnect=element('gmail-disconnect').onclick();assert(element('test-gmail').disabled,'Disconnecting blocks tests immediately');assert(element('install').disabled);disconnectRelease({ok:true});ctx.api=async()=>({state:'disconnected'});await disconnect;
 ctx.api=normalApi;ctx.backgroundStatus=()=>{};ctx.api=async()=>({count:0,complete:true,credits:[]});await ctx.status();assert(element('status-freshness').textContent.includes('Codex read at'));
 vm.runInContext('statusReadAt=Date.now()-1800001;renderStatus(lastStatus)',ctx);assert(element('status-freshness').textContent.includes(catalog.en.status_old));
 for(const provider of ['gmail','google']){
  const status=provider==='gmail'?'gmailStatus':'googleStatus',render=provider==='gmail'?'renderGmail':'renderGoogle';
  const action=provider==='gmail'?'test-gmail':'google-sync';
  ctx[render]({state:'saved'});
  let connectReject;
  const waiting=[];
  ctx.api=(path)=>{
   if(path==='/api/'+provider+'/status')return new Promise((resolve,reject)=>waiting.push({resolve,reject}));
   assert.equal(path,'/api/'+provider+'/connect');return new Promise((resolve,reject)=>{connectReject=reject});
  };
  const old=ctx[status](),oldFailure=ctx[status](),connecting=element(provider+'-connect').onclick();
  waiting[0].resolve({state:'saved'});waiting[1].reject(Error('outdated status failed'));await Promise.all([old,oldFailure]);
  assert(element(provider+'-connect').disabled,provider+' stale status must not restore Connect during authorization');
  assert(element(action).disabled,provider+' stale status must not restore test/sync during authorization');
  assert.equal(element(provider+'-status').textContent,catalog.en.google_connecting);
  connectReject(Error('authorization failed'));await connecting;
  assert.equal(element(provider+'-status').textContent,'authorization failed');assert(!element(provider+'-connect').disabled,'Failed authorization permits retry');
  ctx.api=async()=>({state:'connecting'});await ctx[status]();assert(element(provider+'-connect').disabled);
  const poll=timers.at(-1);assert.equal(poll.ms,2000);
  ctx.api=async()=>({state:'connected'});await poll.fn();await Promise.resolve();assert(!element(action).disabled,provider+' current polling recovers provider actions');
  let staleResolve,disconnectResolve;
  ctx.api=(path)=>{
   if(path==='/api/'+provider+'/disconnect')return new Promise(resolve=>{disconnectResolve=resolve});
   assert.equal(path,'/api/'+provider+'/status');return new Promise(resolve=>{staleResolve=resolve});
  };
  const stale=ctx[status](),disconnecting=element(provider+'-disconnect').onclick();
  disconnectResolve({ok:true});ctx.api=async()=>({state:'disconnected'});await disconnecting;
  staleResolve({state:'saved'});await stale;
  assert(element(action).disabled,provider+' pre-disconnect status must not restore authorization');assert(element(provider+'-disconnect').disabled);
  let oldPollCalls=0;ctx.api=async()=>{oldPollCalls++;return {state:'saved'}};await poll.fn();assert.equal(oldPollCalls,0,'A superseded poll must not make a new status request');
  let lateReject;ctx.api=()=>new Promise((resolve,reject)=>{lateReject=reject});const lateFailure=ctx[status]();
  ctx.api=async(path)=>path.endsWith('/connect')?{ok:true}:{state:'connected'};await element(provider+'-connect').onclick();
  lateReject(Error('old request failed'));await lateFailure;assert(!element(action).disabled,'Old failures must not erase successful reauthorization');
 }
 vm.runInContext("language='es'",ctx);ctx.renderStatus({count:0,complete:true,credits:[]});
 ctx.fetch=async()=>({ok:false,status:409,json:async()=>({error:catalog.es.api_incomplete_error})});
 await element('calendar-download').onclick();assert.equal(element('flash').textContent,catalog.es.api_incomplete_error,'A localized 409 must keep the actionable Refresh instruction');
 assert.equal(downloads.length,0,'A localized rejection must keep the setup page and skip download');
 vm.runInContext("language='en'",ctx);
 ctx.backgroundStatus=originalBackgroundStatus;
 element('setup-ack').checked=true;await element('setup-ack').dispatch('change');
 ctx.api=async()=>({scheduler:'disabled',last_check:null,check_status:'never',last_error:false,failures:[]});await ctx.backgroundStatus();
 assert(!element('install').disabled);assert(element('uninstall').disabled,'Disabled scheduler has no active job to disable');
 let scheduler='disabled';ctx.api=async(path)=>{if(path==='/api/install'){scheduler='enabled';return {ok:true}}if(path==='/api/uninstall'){scheduler='disabled';return {ok:true}}assert.equal(path,'/api/background');return {scheduler,last_check:null,check_status:'never',last_error:false,failures:[]}};
 await element('install').onclick();await Promise.resolve();assert(element('install').disabled,'Enabled scheduler must not offer Enable again');assert(!element('uninstall').disabled);assert.equal(element('setup-next').textContent,catalog.en.setup_checks_on);assert.equal(element('flash').dataset.error,'false','Enabling checks must be presented as success');
 await element('uninstall').onclick();await Promise.resolve();assert(!element('install').disabled);assert(element('uninstall').disabled);
 ctx.api=async()=>{throw Error('background unavailable')};await ctx.backgroundStatus();assert(!element('uninstall').disabled,'Unknown scheduler must still allow disabling an existing job');
 for(const action of ['install','uninstall'])for(const oldFails of [false,true])for(const freshFails of [false,true]){
  const before=action==='install'?'disabled':'enabled',after=action==='install'?'enabled':'disabled';
  const report=scheduler=>({scheduler,last_check:null,check_status:'never',last_error:false,failures:[]});
  ctx.renderBackground(report(before));
  let settleOld,active=0,maxActive=0,reads=0,posted=false;
  ctx.api=async(path)=>{
   if(path==='/api/'+action){posted=true;return {ok:true}}
   assert.equal(path,'/api/background');reads++;active++;maxActive=Math.max(maxActive,active);
   if(reads===1)return new Promise((resolve,reject)=>{settleOld=()=>{active--;oldFails?reject(Error('old poll failed')):resolve(report(before))}});
   assert(posted,'Fresh read must follow the successful scheduler action');active--;
   if(freshFails)throw Error('fresh poll failed');return report(after);
  };
  const old=ctx.backgroundStatus(),changing=element(action).onclick();await Promise.resolve();await Promise.resolve();
  assert(posted,action+' must be available in its starting state');assert.equal(reads,1,'Post-action refresh must wait for the old poll without overlap');
  settleOld();await old;await changing;
  assert.equal(reads,2,action+' must always get a fresh scheduler read after a pending poll');assert.equal(maxActive,1,'Scheduler reads must not overlap');
  if(freshFails){assert.equal(element('scheduler-status').textContent,catalog.en.scheduler_unknown);assert(!element('uninstall').disabled,'Unknown state must preserve the stop action');ctx.api=async()=>report(after);await ctx.backgroundStatus()}
  assert.equal(element('install').disabled,after==='enabled',action+' must use the fresh scheduler state');
  assert.equal(element('uninstall').disabled,after==='disabled',action+' must keep the correct stop action after an old success/error and refresh recovery');
 }

 ctx.renderStatus({count:0,complete:true,credits:[]});assert(!element('calendar-download').disabled,'Complete zero balance can export');
 ctx.URL={createObjectURL:()=> 'blob:calendar',revokeObjectURL(){}};
 ctx.fetch=async()=>({ok:true,blob:async()=>({})});await element('calendar-download').onclick();assert.deepEqual(downloads,['wuphf-resets.ics']);
 ctx.fetch=async()=>({ok:false,json:async()=>({error:'Reset details are incomplete; refresh before exporting.'})});await element('calendar-download').onclick();assert.equal(element('flash').textContent,catalog.en.api_incomplete_error);assert.equal(downloads.length,1,'Server rejection must not download raw JSON or navigate away');
 ctx.fetch=async()=>{throw Error('offline')};await element('calendar-download').onclick();assert.equal(element('flash').textContent,catalog.en.api_error);assert.equal(element('flash').dataset.error,'true','Download errors must retain the error announcement');assert(!element('calendar-download').disabled,'Download transport errors allow retry');
 ctx.renderStatus({count:null,complete:false,credits:[]});assert(element('calendar-download').disabled);await element('calendar-download').onclick();assert.equal(downloads.length,1);
 ctx.api=async()=>{throw Error('Codex unavailable')};await ctx.status();assert(element('calendar-download').disabled,'Failed Codex refresh must disable export');
 const unavailable=new Set(),calendarSaved=new Set();
 for(const language of Object.keys(catalog)){
  vm.runInContext('language='+JSON.stringify(language),ctx);
  ctx.renderStatus({count:null,complete:false,credits:[]});
  assert.equal(element('status-note').textContent,catalog[language].status_unavailable,'Unknown balance must name unavailable balance information');
  assert(catalog[language].status_unavailable);unavailable.add(catalog[language].status_unavailable);
  ctx.renderStatus({count:2,complete:false,credits:[]});assert.equal(element('status-note').textContent,catalog[language].status_incomplete,'A known count retains the narrower expiry-details guidance');
  for(const name of ['telegram','email','gmail','ntfy'])element('use-'+name).checked=false;
  await element('settings').dispatch('change');ctx.api=async()=>({ok:true});await element('settings').dispatch('submit');
  assert.equal(element('flash').textContent,catalog[language].saved_calendar,'Calendar-only saves must guide calendar use instead of a notification test');
  assert(catalog[language].saved_calendar);calendarSaved.add(catalog[language].saved_calendar);
 }
 assert.equal(unavailable.size,8);assert.equal(calendarSaved.size,8,'Calendar-only save guidance must be localized in all languages');
 vm.runInContext("language='en'",ctx);element('use-telegram').checked=true;await element('settings').dispatch('change');await element('settings').dispatch('submit');
 assert.equal(element('flash').textContent,catalog.en.saved,'Notification settings retain the send-test next step');
 console.log('Guided setup prevents stale sends and false readiness, recovers after save/test failures, and gates disconnected/incomplete actions.');
})().catch(e=>{console.error(e);process.exitCode=1});
