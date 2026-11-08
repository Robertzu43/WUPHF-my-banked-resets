const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('wuphf/web.html','utf8');
assert(html.includes('id="telegram-discover"'));
const match=html.match(/async function discoverTelegramChat\(\)\{[\s\S]*?\n\}/);
assert(match,'Telegram lookup function is missing');
const fields={'telegram-chat':{value:'',focus(){}},'telegram-token':{value:'123:secret'},'telegram-discover':{disabled:false}};
let calls=0, allow=true;const messages=[];
const ctx={$:id=>fields[id],window:{confirm:()=>allow},t:key=>key,flash:value=>messages.push(value),
 api:async(path,method,body)=>{calls++;assert.equal(path,'/api/telegram/discover');assert.equal(method,'POST');assert.equal(body.token,'123:secret');return {chat_id:'12345'}}};
vm.createContext(ctx);vm.runInContext(match[0],ctx);
(async()=>{
 assert.equal(calls,0);await ctx.discoverTelegramChat();assert.equal(fields['telegram-chat'].value,'12345');assert.equal(calls,1);assert.equal(fields['telegram-token'].value,'123:secret');
 allow=false;await ctx.discoverTelegramChat();assert.equal(calls,1);assert.equal(fields['telegram-chat'].value,'12345');
 allow=true;ctx.api=async()=>{throw Error('lookup failed')};await ctx.discoverTelegramChat();assert.equal(fields['telegram-chat'].value,'12345');assert.equal(fields['telegram-discover'].disabled,false);assert.equal(messages.at(-1),'lookup failed');
 console.log('Telegram lookup waits for a click, uses entered token, and preserves prior settings on cancellation or error.');
})().catch(e=>{console.error(e);process.exitCode=1});
