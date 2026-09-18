import {Client,Controller,MODULE} from './core.mjs';
let controller,section,timer,lastConfig;const subscriptions=[];
const context=()=>globalThis.SillyTavern.getContext();
function notice(text){const n=section?.querySelector('[data-notice]');if(n)n.textContent=String(text)}
function el(tag,text,props={}){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;Object.assign(e,props);return e}
function button(text,fn){const b=el('button',text,{type:'button'});b.onclick=async()=>{b.disabled=true;try{await fn()}catch(e){notice(e.message)}finally{b.disabled=false}};return b}
function labeled(label,input){const l=el('label',label);l.append(input);return l}
function select(options){const s=el('select');for(const [value,label]of options)s.append(el('option',label,{value}));return s}
function settings(){const c=context();c.extensionSettings[MODULE]??={base:'http://127.0.0.1:8781'};return c.extensionSettings[MODULE]}
async function load(){
 if(!controller)return;
 try{
  const status=await controller.refresh();if(!status){notice('Select and bind a character.');return}
  lastConfig=status.config;
  section.querySelector('[data-mode]').value=status.config.mode;
  section.querySelector('[data-provider]').value=status.provider;
  section.querySelector('[data-model]').value=status.config.model;
  section.querySelector('[data-memory]').checked=status.config.memory;
  section.querySelector('[data-computer]').checked=status.config.computer;
  section.querySelector('[data-native-risk]').checked=status.config.native_risk_ack;
  section.querySelector('[data-native-yolo]').checked=status.config.native_yolo;
  section.querySelector('[data-helpers]').value=JSON.stringify(status.config.helpers,null,2);
  const caps=section.querySelector('[data-caps]');caps.replaceChildren();
  for(const cap of status.available_capabilities){const x=el('input',undefined,{type:'checkbox',value:cap,checked:status.config.capabilities.includes(cap)});caps.append(labeled(cap,x))}
  notice(`${status.name} • ${status.mode} • ${status.provider} • memory: ${status.memory}`);
 }catch(e){notice(e.message)}
}
async function reviews(){
 if(!controller||document.hidden)return;
 try{
  const out=await controller.client.request('/v2/operator/actions',undefined,true);
  const area=section.querySelector('[data-actions]');area.replaceChildren();
  for(const a of out.actions){
   const row=el('article');row.append(el('strong',`${a.entity}: ${a.tool}`));
   row.append(el('pre',JSON.stringify(a.payload.arguments,null,2)));
   row.append(button('Approve exactly this',async()=>{await controller.client.request(`/v2/operator/entities/${a.entity}/approve`,{action_id:a.id,digest:a.digest},true);await reviews()}));
   row.append(button('Reject',async()=>{await controller.client.request(`/v2/operator/entities/${a.entity}/reject`,{action_id:a.id},true);await reviews()}));
   area.append(row);
  }
 }catch(e){notice(e.message)}
}
function mount(){
 if(document.getElementById('lelock_v03_panel'))return;
 section=el('section',undefined,{id:'lelock_v03_panel'});section.append(el('h3','Lelock Character Agents'));
 const base=el('input',undefined,{value:settings().base??'http://127.0.0.1:8781',placeholder:'Gateway address'});
 const code=el('input',undefined,{type:'password',placeholder:'One-time pairing code',autocomplete:'off'});
 section.append(labeled('Gateway ',base),labeled('Pairing ',code));
 section.append(button('Pair gateway',async()=>{
  const client=await Client.pair(base.value,code.value);code.value='';controller?.disable();controller=new Controller(context,client,notice);
  const s=controller.settings();s.base=base.value;context().saveSettingsDebounced();await load();
 }));
 const pairFile=el('input',undefined,{type:'file',accept:'.json,application/json'});
 pairFile.onchange=async()=>{try{
  const file=pairFile.files?.[0];if(!file)return;if(file.size>8192)throw Error('Pairing file too large');
  const client=Client.fromPairing(JSON.parse(await file.text()));controller?.disable();controller=new Controller(context,client,notice);
  base.value=client.base;controller.settings().base=client.base;context().saveSettingsDebounced();await load();
 }catch(e){notice(e.message)}finally{pairFile.value=''}};
 section.append(labeled('Reconnect from private gateway pairing file ',pairFile));
 section.append(button('Bind selected character',async()=>{if(!controller)throw Error('Pair first');await controller.bind();await load()}));
 const attach=el('input',undefined,{placeholder:'Existing entity ID (optional)'});
 section.append(labeled('Explicit reattach ',attach),button('Attach selected card',async()=>{if(!controller)throw Error('Pair first');await controller.bind(attach.value);await load()}));
 const provider=select([['sillytavern','Keep SillyTavern model + tools'],['codex','Account Chat: ChatGPT / Codex'],['antigravity','Account Chat: Google Antigravity'],['claude-code','Claude Code: native application'],['opencode','OpenCode: native application'],['hermes','Hermes: native application']]);provider.dataset.provider='';
 const mode=select([['safe','SAFE: review effects'],['trusted','TRUSTED: standing grants'],['yolo','YOLO: enabled tools, no per-action prompts']]);mode.dataset.mode='';
 const model=el('input',undefined,{placeholder:'Native model ID; blank uses provider default'});model.dataset.model='';
 section.append(labeled('Runtime ',provider),labeled('Autonomy ',mode),labeled('Model ',model));
 const models=el('select');models.append(el('option','Choose an entitled Codex model',{value:''}));models.onchange=()=>{model.value=models.value};section.append(models);
 section.append(button('Sign in to ChatGPT / Codex',async()=>{
  if(!controller)throw Error('Pair first');const a=await controller.client.request('/v2/accounts/codex/login',{},true);
  if(a.authUrl){const u=new URL(a.authUrl);if(u.protocol!=='https:')throw Error('Unexpected provider auth URL');
   const link=el('a','Open official sign-in',{href:u.href,target:'_blank',rel:'noopener noreferrer'});section.querySelector('[data-login]').replaceChildren(link)}
  notice('Complete the provider sign-in, then refresh models. Your provider tokens remain in Codex.');
 }));
 const login=el('div');login.dataset.login='';section.append(login);
 section.append(button('Check account / list models',async()=>{
  if(!controller)throw Error('Pair first');const a=await controller.client.request('/v2/accounts/codex/status',undefined,true);
  if(!a.signed_in)throw Error('Codex is not signed in');const r=await controller.client.request('/v2/accounts/codex/models',undefined,true);
  models.replaceChildren(el('option','Provider default',{value:''}));for(const m of r.models)models.append(el('option',m.label,{value:m.id}));notice(`Codex account connected (${a.plan??a.type}).`);
 }));
 section.append(button('Open selected native login',async()=>{
  if(!controller)throw Error('Pair first');const r=await controller.client.request('/v2/native/login',{provider:provider.value},true);
  notice(r.launched?'Complete sign-in in the native application.':r.command??r.note);
 }));
 for(const [label,key]of [['Enable actual MemPalace (requires installed Palace runtime)','memory'],['Enable this character’s Rakazo computer','computer'],['Acknowledge native Antigravity tool/host permissions','native-risk'],['Also skip native Antigravity prompts (YOLO only)','native-yolo']]){
  const c=el('input',undefined,{type:'checkbox'});c.setAttribute('data-'+key,'');section.append(labeled(label,c));
 }
 const capArea=el('div');capArea.dataset.caps='';section.append(el('h4','Explicit tool capabilities'),capArea);
 const helpers=el('textarea',undefined,{rows:3,placeholder:'{"Rowan": "entity-id-from-roster"}'});helpers.dataset.helpers='';section.append(labeled('Named character helpers ',helpers));
 section.append(button('Show entity roster',async()=>{const r=await controller.client.request('/v2/operator/entities',undefined,true);section.querySelector('[data-roster]').textContent=JSON.stringify(r.entities,null,2)}));
 const roster=el('pre');roster.dataset.roster='';section.append(roster);
 section.append(button('Save permissions and runtime',async()=>{
  if(!controller||!lastConfig)throw Error('Bind a character first');const capabilities=[...capArea.querySelectorAll('input:checked')].map(x=>x.value);
  const config={...lastConfig,mode:mode.value,provider:provider.value,model:model.value,
   capabilities,auto_approve:mode.value==='trusted'?capabilities:[],helpers:JSON.parse(helpers.value||'{}'),
   memory:section.querySelector('[data-memory]').checked,computer:section.querySelector('[data-computer]').checked,
   native_risk_ack:section.querySelector('[data-native-risk]').checked,native_yolo:section.querySelector('[data-native-yolo]').checked};
  await controller.configure(config);await load();
 }));
 section.append(button('Refresh / reconnect character',load));
 section.append(button('STOP selected character',async()=>{await controller.stop();notice('Stopped. Save permissions again to start a fresh session.')}));
 section.append(button('STOP its computer',async()=>{const b=controller.binding();await controller.client.request(`/v2/operator/entities/${b.entity}/computer-stop`,{},true);notice('Computer stop requested.')}));
 section.append(button('Lelock Send (uses the main chat textbox)',sendBox));
 section.append(button('Sign out of Codex',async()=>{
  if(!controller)throw Error('Pair first');if(controller.busy)throw Error('Stop the active turn before signing out');
  await controller.client.request('/v2/accounts/codex/logout',{},true);notice('Codex signed out. Other native accounts were not changed.');
 }));
 section.append(button('Show Codex quota',async()=>{if(!controller)throw Error('Pair first');const r=await controller.client.request('/v2/accounts/codex/quotas',undefined,true);section.querySelector('[data-result]').textContent=JSON.stringify(r,null,2)}));
 section.append(button('Show last turn result',async()=>{
  if(!controller?.lastTurn)throw Error('No turn in this browser session');const t=controller.lastTurn;
  const r=await controller.client.request(`/v2/entities/${t.entity}/turns/${t.id}`);
  section.querySelector('[data-result]').textContent=JSON.stringify(r.result??r,null,2);
 }));
 const result=el('pre');result.dataset.result='';section.append(result);
 section.append(el('h4','Reviewed Skills'));
 const skillName=el('input',undefined,{placeholder:'Pack directory name'});let reviewed;
 section.append(labeled('Skill ',skillName),button('Inspect skill',async()=>{
  reviewed=await controller.client.request('/v2/operator/skills/inspect',{name:skillName.value},true);
  result.textContent=JSON.stringify(reviewed,null,2);
 }),button('Approve inspected skill hash',async()=>{
  if(!reviewed)throw Error('Inspect exact skill content first');await controller.client.request('/v2/operator/skills/approve',{name:reviewed.name,sha256:reviewed.sha256},true);reviewed=undefined;notice('Skill pinned. Grant skills.read to this character to expose the tool.');
 }));
 section.append(el('h4','Optional Pulse — scheduled account usage'));
 const pulsePrompt=el('textarea',undefined,{rows:2,placeholder:'An authorized task for this same character'});
 const interval=el('input',undefined,{type:'number',min:'600',value:'3600'});
 section.append(labeled('Scheduled task ',pulsePrompt),labeled('Interval seconds ',interval));
 section.append(button('Authorize for one hour',async()=>{
  const b=controller.binding();const r=await controller.client.request(`/v2/operator/entities/${b.entity}/schedules`,{prompt:pulsePrompt.value,interval:Number(interval.value),ttl:3600},true);result.textContent=JSON.stringify(r,null,2);
 }),button('Show schedules',async()=>{
  const b=controller.binding();const r=await controller.client.request(`/v2/operator/entities/${b.entity}/schedules`,undefined,true);result.textContent=JSON.stringify(r,null,2);
 }),button('Show local inbox',async()=>{
  const b=controller.binding();const r=await controller.client.request(`/v2/entities/${b.entity}/inbox`);result.textContent=JSON.stringify(r,null,2);
 }));
 const sid=el('input',undefined,{placeholder:'Schedule ID'});section.append(labeled('Disable schedule ',sid),button('Disable schedule',async()=>{
  const b=controller.binding();const r=await controller.client.request(`/v2/operator/entities/${b.entity}/schedule-disable`,{id:sid.value},true);result.textContent=JSON.stringify(r,null,2);
 }));
 const n=el('p','Pair the gateway, bind a character, then choose its runtime.');n.dataset.notice='';n.setAttribute('role','status');section.append(n);
 const actions=el('div');actions.dataset.actions='';section.append(el('h4','Exact action review — all bound characters'),actions);
 (document.getElementById('extensions_settings')??document.body).append(section);
 const adjacent=button('Lelock Send',sendBox);adjacent.id='lelock_v03_send';document.getElementById('send_but')?.parentElement?.append(adjacent);
 timer=setInterval(reviews,1000);
}
async function sendBox(){
 if(!controller)throw Error('Pair Lelock first');const box=document.getElementById('send_textarea');if(!box)throw Error('SillyTavern chat textbox not found');
 const text=box.value;box.value='';try{await controller.send(text)}catch(e){if(!box.value)box.value=text;throw e}
}
export function onActivate(){
 if(!globalThis.SillyTavern?.getContext)throw Error('SillyTavern context API required');
 const c=context();const changed=()=>{controller?.clear();void load()};
 for(const name of ['CHAT_CHANGED','CHARACTER_EDITED','MAIN_API_CHANGED','CHATCOMPLETION_MODEL_CHANGED']){
  const type=c.eventTypes?.[name];if(type){c.eventSource.on(type,changed);subscriptions.push([type,changed])}
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
}
export function onDisable(){
 controller?.disable();clearInterval(timer);for(const [t,f]of subscriptions)context().eventSource.removeListener(t,f);subscriptions.length=0;
 section?.remove();document.getElementById('lelock_v03_send')?.remove();controller=undefined;
}
globalThis.lelockV03Intercept=async function(chat,size,abort,type){
 if(!controller||controller.disabled)return;let b;try{b=controller.binding()}catch{return}if(!b)return;
 if(b.provider==='sillytavern'){await controller.recall();return}
 // Never accidentally bill the SillyTavern API when Account Chat/native-only mode is selected.
 abort(true);
 if(!['codex','antigravity'].includes(b.provider)){notice('This provider uses its native application; it is not a Tavern subscription proxy.');return}
 if(type&&type!=='normal'){notice('Use Lelock Send for Account Chat; swipe/regenerate/impersonate are not yet verified.');return}
 const last=[...context().chat].reverse().find(m=>m.is_user&&!m.is_system);
 try{await controller.send(last?.mes??'',{alreadyAdded:true})}catch(e){notice(e.message)}
};
