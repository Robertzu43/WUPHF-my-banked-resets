// Exercise the shipped browser script; only the DOM and network boundary are substituted.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('wuphf/web.html','utf8');
const elements={}, tests=[];
function element(id){return elements[id]||(elements[id]={value:'',checked:false,disabled:false,hidden:false,textContent:'',files:[],children:[],listeners:{},dataset:{},classList:{add(){},remove(){}},focus(){},select(){},replaceChildren(...children){this.children=children},addEventListener(type,fn){(this.listeners[type]??=[]).push(fn)},async dispatch(type){for(const fn of this.listeners[type]||[])await fn({preventDefault(){},target:this})}})}
for(const tag of html.matchAll(/<[^>]+\bid="([^"]+)"[^>]*>/g)){element(tag[1]).disabled=/\bdisabled\b/.test(tag[0]);}
for(const tag of html.matchAll(/<button[^>]+class="[^"]*\btest\b[^"]*"[^>]*>/g)){const b=element('test-'+tag[0].match(/data-channel="([^"]+)"/)[1]);b.disabled=/\bdisabled\b/.test(tag[0]);b.dataset.channel=tag[0].match(/data-channel="([^"]+)"/)[1];tests.push(b)}
const ctx={console,Date,Intl,Number,AbortController,setTimeout:()=>1,clearTimeout(){},setInterval:()=>1,confirm:()=>true,window:{confirm:()=>true},NodeFilter:{SHOW_TEXT:4},document:{body:{},documentElement:{},getElementById:element,querySelector:s=>element(s),querySelectorAll:s=>s==='.test'?tests:[],createTreeWalker:()=>({nextNode:()=>null}),createElement:()=>element('created-'+Math.random())}};
vm.createContext(ctx);vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1].replace(/boot\(\);\s*$/,''),ctx);
const catalog=JSON.parse(fs.readFileSync('wuphf/translations.json'));
ctx.catalog=catalog;vm.runInContext('translations=catalog',ctx);
const calls=[];let failSave=false,failTest=false;
ctx.api=async(path,method,data)=>{calls.push([path,method,data]);if(path==='/api/settings'&&method==='POST'){if(failSave)throw Error('save failed');return {ok:true}}if(path==='/api/test'){if(failTest)throw Error('test failed');return {ok:true}}if(path==='/api/settings')return {advance_days:7,repeat_hours:24,language:'en',channels:{telegram:{chat_id:'123'}}};throw Error('Unexpected '+path)};
(async()=>{
 assert(tests.every(b=>b.disabled),'Tests must start disabled while settings are loading');
 assert(element('install').disabled,'Enable must start disabled');
 await ctx.settings();
 assert.equal(element('test-telegram').disabled,false);
 assert.equal(element('install').disabled,true,'Saved configuration is not evidence of an accepted test');
 element('telegram-chat').value='456';await element('settings').dispatch('input');
 assert(element('test-telegram').disabled,'Editing must block tests of the stale saved destination');
 const before=calls.length;await element('test-telegram').dispatch('click');assert.equal(calls.length,before,'Guard must prevent stale requests even when invoked programmatically');
 failSave=true;await element('settings').dispatch('submit');assert(element('test-telegram').disabled);assert.equal(element('settings-state').textContent,catalog.en.setup_unsaved);
 failSave=false;await element('settings').dispatch('submit');assert.equal(calls.at(-1)[2].channels.telegram.chat_id,'456');assert(!element('test-telegram').disabled);
 failTest=true;await element('test-telegram').dispatch('click');assert(element('install').disabled);assert.equal(element('test-state-telegram').textContent,catalog.en.test_failed);
 failTest=false;await element('test-telegram').dispatch('click');assert(!element('install').disabled);assert(element('test-state-telegram').textContent.includes('accepted'));assert(!element('test-state-telegram').textContent.includes('received'));
 element('telegram-token').value='new-secret';await element('settings').dispatch('input');assert(element('install').disabled);assert.equal(element('test-state-telegram').textContent,catalog.en.test_not_checked);
 await element('settings').dispatch('submit');
 element('setup-ack').checked=true;await element('setup-ack').dispatch('change');assert(!element('install').disabled,'Earlier manual receipt acknowledgement avoids forcing another message');
 element('use-gmail').checked=true;await element('settings').dispatch('change');await element('settings').dispatch('submit');ctx.renderGmail({state:'disconnected'});assert(element('test-gmail').disabled);assert(element('gmail-disconnect').disabled);
 ctx.renderGmail({state:'saved'});assert(!element('test-gmail').disabled);assert(!element('gmail-disconnect').disabled);
 ctx.renderGoogle({state:'disconnected',message:'Not connected'});assert(element('google-sync').disabled);assert(element('google-disconnect').disabled);
 ctx.renderGoogle({state:'saved'});assert(element('google-sync').disabled,'Incomplete Codex data cannot sync');
 ctx.renderStatus({count:0,complete:true,credits:[]});assert.equal(element('count').textContent,0);assert.equal(element('status-note').textContent,catalog.en.status_zero);assert(!element('google-sync').disabled);
 ctx.renderStatus({count:null,complete:false,credits:[{expires:null}]});assert.equal(element('count').textContent,'?');assert.equal(element('status-note').textContent,catalog.en.status_incomplete);assert.equal(element('dates').children[0].textContent,catalog.en.expiry_unknown);assert(element('google-sync').disabled);
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
 console.log('Guided setup prevents stale sends and false readiness, recovers after save/test failures, and gates disconnected/incomplete actions.');
})().catch(e=>{console.error(e);process.exitCode=1});
