const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('wuphf/web.html','utf8');
assert(html.includes('id="ntfy-legacy"'));
assert(html.includes('id="settings-save" disabled'));
assert(!html.includes('id="ntfy-generate"'));
const show=html.match(/function showLegacyNtfy\(channel\)\{[\s\S]*?\n\}/);
const retain=html.match(/function retainLegacyNtfy\(channels\)\{[\s\S]*?\n\}/);
assert(show&&retain,'legacy migration controls missing');
assert(html.includes('retainLegacyNtfy(c)'));
const fields={'ntfy-legacy':{hidden:true},'use-ntfy':{checked:false}};
const ctx={legacyNtfy:null,$:id=>fields[id]};vm.createContext(ctx);vm.runInContext(show[0]+'\n'+retain[0],ctx);
ctx.showLegacyNtfy(undefined);let data={};ctx.retainLegacyNtfy(data);assert(fields['ntfy-legacy'].hidden);assert(!('ntfy' in data));
const existing={url:'https://example.test',topic:'old-topic'};ctx.showLegacyNtfy(existing);data={};ctx.retainLegacyNtfy(data);
assert(!fields['ntfy-legacy'].hidden);assert(fields['use-ntfy'].checked);assert.deepEqual(data.ntfy,existing);
fields['use-ntfy'].checked=false;data={};ctx.retainLegacyNtfy(data);assert(!('ntfy' in data));ctx.showLegacyNtfy(undefined);assert(fields['ntfy-legacy'].hidden);
ctx.showLegacyNtfy(null);data={};ctx.retainLegacyNtfy(data);assert(!fields['ntfy-legacy'].hidden);assert('ntfy' in data);assert.equal(data.ntfy,null);
console.log('New setup hides ntfy; existing settings remain until explicitly disabled.');
const loadSettings=html.match(/async function settings\(\)\{[^\n]*\}/);
const submitHandler=html.match(/\$\('settings'\)\.addEventListener\('submit',async e=>\{[^\n]*\}\);/);
assert(loadSettings&&submitHandler,'settings flow is missing');
let submitted, handler;const elements={};
const element=id=>elements[id]||(elements[id]={value:'',checked:false,hidden:false,addEventListener(type,fn){if(type==='submit')handler=fn}});
const formCtx={settingsLoaded:false,settingsDirty:false,setupBusy:false,settingsRevision:0,testResults:{},renderSetup(){element('settings-save').disabled=!formCtx.settingsLoaded},legacyNtfy:null,language:'en',translations:{en:{}},$:element,applyLanguage(){},toggle(){},flash(){},
 api:async(path,method,payload)=>{if(path==='/api/settings'&&method==='POST'){submitted=payload;return {ok:true}}
 return {advance_days:7,repeat_hours:24,channels:{ntfy:{url:'https://example.test',topic:'existing'}}}}};
vm.createContext(formCtx);vm.runInContext(show[0]+'\n'+retain[0]+'\n'+loadSettings[0]+'\n'+submitHandler[0],formCtx);
(async()=>{
 await formCtx.settings();assert.equal(element('settings-save').disabled,false);assert(!element('ntfy-legacy').hidden);assert(element('use-ntfy').checked);
 element('use-email').checked=true;element('email-host').value='smtp.example.test';element('email-port').value='465';element('email-user').value='name';element('email-from').value='a@example.test';element('email-to').value='b@example.test';
 await handler({preventDefault(){}});assert.equal(submitted.channels.ntfy.topic,'existing');assert.equal(submitted.channels.ntfy.url,'https://example.test');assert.equal(submitted.channels.email.host,'smtp.example.test');
 element('use-ntfy').checked=false;const save=formCtx.api;formCtx.api=async()=>{throw Error('save failed')};await handler({preventDefault(){}});assert(!element('ntfy-legacy').hidden);formCtx.api=save;
 await handler({preventDefault(){}});assert(!('ntfy' in submitted.channels));assert(element('ntfy-legacy').hidden);
 element('settings-save').disabled=true;formCtx.api=async()=>{throw Error('load failed')};try{await formCtx.settings()}catch(e){}assert(element('settings-save').disabled);
 console.log('Saving other settings preserves legacy configuration; disabling removes it only on save.');
})().catch(e=>{console.error(e);process.exitCode=1});
