const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('wuphf/web.html','utf8');
assert(html.includes('id="telegram-pair"'));
assert(html.includes('id="telegram-discover"'));
const pairing=html.match(/async function createTelegramPairing\(\)\{[\s\S]*?\n\}/);
const discover=html.match(/async function discoverTelegramChat\(\)\{[\s\S]*?\n\}/);
assert(pairing&&discover,'Telegram pairing functions are missing');
const fields={'telegram-chat':{value:'',focus(){}},'telegram-token':{value:'123:secret'},'telegram-discover':{disabled:false},'telegram-pair':{disabled:false},'telegram-phrase':{value:'',focus(){},select(){}}};
let calls=[], allow=true;const messages=[];
const ctx={$:id=>fields[id],window:{confirm:()=>allow},t:key=>key,flash:value=>messages.push(value),
 api:async(path,method,body)=>{calls.push(path);assert.equal(method,'POST');if(path==='/api/telegram/pair')return {phrase:'WUPHF-proof'};assert.equal(body.token,'123:secret');return {chat_id:'12345'}}};
vm.createContext(ctx);vm.runInContext(pairing[0]+'\n'+discover[0],ctx);
(async()=>{
 assert.equal(calls.length,0);await ctx.createTelegramPairing();assert.equal(fields['telegram-phrase'].value,'WUPHF-proof');
 await ctx.discoverTelegramChat();assert.equal(fields['telegram-chat'].value,'12345');assert.equal(fields['telegram-phrase'].value,'');assert.equal(fields['telegram-token'].value,'123:secret');
 allow=false;await ctx.discoverTelegramChat();assert.equal(calls.length,2);assert.equal(fields['telegram-chat'].value,'12345');
 allow=true;ctx.api=async()=>{throw Error('lookup failed')};await ctx.discoverTelegramChat();assert.equal(fields['telegram-chat'].value,'12345');assert.equal(fields['telegram-discover'].disabled,false);assert.equal(messages.at(-1),'lookup failed');
 console.log('Telegram pairing and lookup require explicit actions and preserve prior settings on cancellation or error.');
})().catch(e=>{console.error(e);process.exitCode=1});
