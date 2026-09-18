import test from 'node:test';import assert from 'node:assert/strict';
import {Client,Controller,MODULE,localBase} from '../core.mjs';
function fixture(){
 const registered=new Map(),requests=[],messages=[];
 const c={extensionSettings:{[MODULE]:{base:'http://127.0.0.1:8781'}},characters:[{name:'Ada',avatar:'ada.png',data:{name:'Ada'}},{name:'Rowan',avatar:'rowan.png',data:{name:'Rowan'}}],
  characterId:0,chatId:'chat',chat:[],saveSettingsDebounced(){},saveChat:async()=>{},eventSource:{emit:async()=>{}},eventTypes:{},
  registerFunctionTool:x=>registered.set(x.name,x),unregisterFunctionTool:n=>registered.delete(n),isToolCallingSupported:()=>true,
  addOneMessage:m=>messages.push(m),setExtensionPrompt(){}};
 const client={async request(path,body,op){requests.push({path,body,op});
  if(path==='/v2/bindings')return {entity:body.card.name,created:true,name:body.card.name};
  if(path.endsWith('/status'))return {provider:'sillytavern',config:{provider:'sillytavern'}};
  if(path.endsWith('/tools'))return {tools:[{name:'lelock_write_text',description:'write',parameters:{type:'object'}}]};
  if(path.endsWith('/invoke'))return {status:'done',result:{written:true}};
  if(path.endsWith('/turns'))return {state:'completed',result:{text:'Hello from the actual selected character',name:'Ada'}};
  return {};
 }};
 return {c,client,requests,registered,messages,controller:new Controller(()=>c,client)};
}
test('initial partial settings are completed',()=>{const {controller}=fixture();assert.ok(controller.settings().client_id);assert.deepEqual(controller.settings().bindings,{})});
test('remote bridge URL refused',()=>assert.throws(()=>localBase('https://example.com')));
test('credentials in bridge URL refused',()=>assert.throws(()=>localBase('http://u:p@localhost:8781')));
test('card binding does not contain provider tokens',async()=>{const f=fixture();await f.controller.bind();assert.equal(f.controller.binding().entity,'Ada');assert.equal(JSON.stringify(f.c.extensionSettings).includes('token'),false)});
test('tools dynamically register from server schema',async()=>{const f=fixture();await f.controller.bind();await f.controller.refresh();assert.ok(f.registered.has('ll03_lelock_write_text'))});
test('tool closure retains selected actor',async()=>{const f=fixture();await f.controller.bind();await f.controller.refresh();const t=f.registered.get('ll03_lelock_write_text');await t.action({path:'a',content:'b'});assert.equal(f.requests.at(-1).path,'/v2/entities/Ada/invoke')});
test('stale character closure is denied',async()=>{const f=fixture();await f.controller.bind();await f.controller.refresh();const t=f.registered.get('ll03_lelock_write_text');f.c.characterId=1;await assert.rejects(t.action({path:'a',content:'b'}),/changed/)});
test('character change clears prior tools',async()=>{const f=fixture();await f.controller.bind();await f.controller.refresh();f.controller.clear();assert.equal(f.registered.size,0)});
test('group chat cannot quietly reuse previous character',()=>{const f=fixture();f.c.groupId='g';assert.throws(()=>f.controller.selected(),/group/)});
test('account mode appends one user and one assistant message',async()=>{const f=fixture();await f.controller.bind();f.controller.binding().provider='codex';await f.controller.send('hello');assert.equal(f.c.chat.length,2);assert.equal(f.c.chat[1].extra.lelock_v03.entity,'Ada')});
test('disable cleans registered tools',async()=>{const f=fixture();await f.controller.bind();await f.controller.refresh();f.controller.disable();assert.equal(f.registered.size,0)});
test('unsupported host tools are not falsely registered',async()=>{const f=fixture();f.c.isToolCallingSupported=()=>false;await f.controller.bind();await f.controller.refresh();assert.equal(f.registered.size,0)});

test('private pairing file keeps tokens in client, not host settings',()=>{
 const c=Client.fromPairing({base:'http://127.0.0.1:8781',agent_token:'a'.repeat(40),operator_token:'o'.repeat(40)},async()=>{});assert.equal(c.base,'http://127.0.0.1:8781');
});
test('private pairing refuses remote service or extra credential fields',()=>{
 assert.throws(()=>Client.fromPairing({base:'https://remote.invalid',agent_token:'a'.repeat(40),operator_token:'o'.repeat(40)}));
 assert.throws(()=>Client.fromPairing({base:'http://127.0.0.1:8781',agent_token:'a'.repeat(40),operator_token:'o'.repeat(40),provider_token:'never'}));
});
