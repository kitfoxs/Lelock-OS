import test from 'node:test';import assert from 'node:assert/strict';
import {DirectComputer} from '../dist/service.js';
function setup(options={}){
 const files=new Map(),provisions=[],calls=[],saved=new Map();let sequence=0;
 const provider={
  describe:()=>({id:options.provider??'fake',capabilities:{graphical:true}}),
  provision:async(r,c)=>{provisions.push(r);return {id:'computer-'+r.botId,botId:options.wrongOwner?'other':r.botId,kind:'fake',providerRef:'ref-'+r.botId}},
  prepare:async()=>{},
  async *execute(c,r,x){calls.push({actor:c.botId,context:x.botId,request:r});yield {type:'stdout',data:'hello '+c.botId};if(!options.noExit)yield {type:'exit',code:0}},
  observe:async()=>({frameId:'f',image:new Uint8Array([1,2,3]),mimeType:'image/png',width:1,height:1,capturedAt:'now'}),
  act:async(c,r)=>({completed:options.partial?0:r.actions.length}),
  readFile:async(c,p)=>options.corrupt?new Uint8Array():files.get(c.botId+':'+p)??new Uint8Array(),
  writeFile:async(c,f)=>{files.set(c.botId+':'+f.path,f.content)},stop:async()=>{},
 };
 const service=new DirectComputer(provider,{path:a=>'/test-homes/'+a,load:async a=>saved.get(a),save:async(a,c)=>saved.set(a,c)},()=>String(++sequence),x=>Buffer.from(x).toString('base64'));
 return {service,provisions,calls,files,saved};
}
test('computer adapter has no inference runtime',()=>assert.equal(setup().service.describe().agent_runtime,false));
test('main character is the direct computer actor',async()=>{const {service,calls}=setup();const r=await service.call('execute',{actor:'Ada',arguments:{argv:['echo','hello']}});assert.equal(r.actor,'Ada');assert.equal(r.delegated,false);assert.equal(calls[0].context,'Ada')});
test('characters get different private computers',async()=>{const {service,provisions}=setup();await service.call('execute',{actor:'Ada',arguments:{argv:['true']}});await service.call('execute',{actor:'Rowan',arguments:{argv:['true']}});assert.deepEqual(provisions.map(x=>x.botId),['Ada','Rowan'])});
test('one private computer is reused by its character',async()=>{const {service,provisions}=setup();for(let i=0;i<2;i++)await service.call('execute',{actor:'Ada',arguments:{argv:['true']}});assert.equal(provisions.length,1)});
test('wrong returned owner fails closed',async()=>{const {service}=setup({wrongOwner:true});await assert.rejects(service.call('execute',{actor:'Ada',arguments:{argv:['true']}}),/another character/)});
test('host computer provider refused',()=>assert.throws(()=>setup({provider:'desktop'}),/Host computer/));
test('unverified remote backend refused',()=>assert.throws(()=>setup({provider:'e2b'}),/Remote/));
test('invalid actor cannot traverse home paths',async()=>await assert.rejects(setup().service.call('read',{actor:'../Ada',arguments:{path:'x'}}),/actor/));
test('relative file traversal refused',async()=>await assert.rejects(setup().service.call('read',{actor:'Ada',arguments:{path:'../x'}}),/relative/));
test('write is read back and isolated from helper',async()=>{const {service}=setup();await service.call('write',{actor:'Ada',arguments:{path:'x.txt',content:'hello'}});assert.equal((await service.call('read',{actor:'Ada',arguments:{path:'x.txt'}})).content,'hello');assert.equal((await service.call('read',{actor:'Rowan',arguments:{path:'x.txt'}})).content,'')});
test('missing command exit requires reconciliation',async()=>{const {service}=setup({noExit:true});await assert.rejects(service.call('execute',{actor:'Ada',arguments:{argv:['true']}}),/receipt/);await assert.rejects(service.call('write',{actor:'Ada',arguments:{path:'x',content:'a'}}),/Uncertain/)});
test('partial actions are not replayed as success',async()=>await assert.rejects(setup({partial:true}).service.call('act',{actor:'Ada',arguments:{actions_json:'[{"kind":"key","key":"Enter"}]'}}),/Partial/));
test('readback mismatch never reports verified',async()=>await assert.rejects(setup({corrupt:true}).service.call('write',{actor:'Ada',arguments:{path:'x',content:'hello'}}),/mismatch/));
test('screenshot preserves multimodal block',async()=>{const r=await setup().service.call('observe',{actor:'Ada',arguments:{}});assert.equal(r.content[0].type,'image');assert.equal(r.content[0].data,'AQID')});
test('unknown operations do not provision computers',async()=>{const {service,provisions}=setup();await assert.rejects(service.call('run-an-agent',{actor:'Ada',arguments:{}}));assert.equal(provisions.length,0)});
