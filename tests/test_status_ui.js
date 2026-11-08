const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('wuphf/web.html','utf8');
const elements={};
const element=()=>({textContent:'',children:[],disabled:false,classList:{remove(){},add(){}},replaceChildren(...children){this.children=children}});
const snapshot={count:2,complete:true,credits:[{expires:'2026-11-20T12:00:00Z'}]};
const ctx={Date,lastStatus:null,lastBackground:null,lastGoogle:null,lastGmail:null,language:'en',textNodes:[],placeholders:[],
  $:id=>elements[id]||(elements[id]=element()),locale:()=>ctx.language,
  t:(key)=>ctx.language+':'+key,backgroundStatus(){},renderSetup(){},statusReadAt:null,api:async()=>snapshot,
  document:{documentElement:{},querySelector:()=>element(),querySelectorAll:()=>[],createElement:()=>element()}};
vm.createContext(ctx);
for(const pattern of [/function dateTime\(value\)\{[^\n]*\}/,/function applyLanguage\(\)\{[\s\S]*?\n\}/,/function renderStatus\(s\)\{[\s\S]*?\n\}/,/async function status\(\)\{[^\n]*\}/]){
  vm.runInContext(html.match(pattern)[0],ctx);
}
(async()=>{
  await ctx.status();
  assert.equal(elements.count.textContent,2);
  assert.equal(elements.dates.children.length,1);
  assert.equal(elements['status-note'].textContent,'en:status_connected');
  ctx.api=async()=>{throw Error('Codex unavailable')};
  await ctx.status();
  assert.equal(elements['status-note'].textContent,'Codex unavailable');
  ctx.language='es';ctx.applyLanguage();
  assert.equal(elements['status-note'].textContent,'Codex unavailable','Changing language must preserve the failed refresh state');
  assert.equal(ctx.lastStatus,null);
  assert.equal(elements.count.textContent,'?');
  assert.equal(elements.dates.children.length,0);
  assert.equal(elements.refresh.disabled,false);
  ctx.api=async()=>({count:1,complete:true,credits:[]});
  await ctx.status();
  assert.equal(elements.count.textContent,1);
  assert.equal(elements['status-note'].textContent,'es:status_connected');
  console.log('Failed refresh clears cached reset data and remains failed across language changes until recovery.');
})().catch(e=>{console.error(e);process.exitCode=1});
