const fs=require('fs'), vm=require('vm'), assert=require('assert');
const html=fs.readFileSync('wuphf/web.html','utf8');
assert(html.includes('id="ntfy-generate"'));
const source=html.match(/function generateNtfyTopic\(\)\{[\s\S]*?\n\}/)[0];
const topic={value:'',focus(){this.focused=true}}, messages=[];
let allow=true, randomCalls=0;
const ctx={Uint8Array,window:{crypto:{getRandomValues(buffer){randomCalls++;buffer.fill(42);return buffer}},confirm:()=>allow},
  $:id=>{assert.equal(id,'ntfy-topic');return topic},t:key=>key,flash:value=>messages.push(value)};
vm.createContext(ctx);vm.runInContext(source,ctx);
ctx.generateNtfyTopic();
assert.equal(topic.value,'wuphf-'+ '2a'.repeat(16));assert.equal(randomCalls,1);assert(topic.focused);
allow=false;topic.value='existing';ctx.generateNtfyTopic();assert.equal(topic.value,'existing');assert.equal(randomCalls,1);
allow=true;ctx.window.crypto=undefined;ctx.generateNtfyTopic();assert.equal(topic.value,'existing');assert.equal(messages.at(-1),'ntfy_crypto_error');
console.log('ntfy generation uses secure randomness and preserves declined or failed replacements.');
