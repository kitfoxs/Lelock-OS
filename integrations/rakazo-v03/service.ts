/** Direct computer operations only. No Pi/LLM/delegation dependency. MIT: Kit Olivas & Ada Marie. */
export interface Computer {id:string;botId:string;kind:string;providerRef:string;fresh?:boolean}
export interface Context {operationId:string;traceId:string;spaceId:string;userId:string;botId:string;runId:string;signal:AbortSignal}
export interface Provider {
 describe(): {id:string;capabilities:{graphical:boolean;[key:string]:unknown};[key:string]:unknown};
 provision(r:{botId:string;homePath:string;providerRef?:string;providerKind?:string},c:Context):Promise<Computer>;
 prepare(c:Computer,x:Context):Promise<void>;
 execute(c:Computer,r:{argv:string[];cwd?:string;timeoutMs?:number},x:Context):AsyncIterable<{type:string;data?:string;code?:number}>;
 observe(c:Computer,x:Context):Promise<{frameId:string;image:Uint8Array;mimeType:string;width:number;height:number;capturedAt:string}>;
 act(c:Computer,r:{actions:unknown[];observe?:boolean},x:Context):Promise<{completed:number;observation?:unknown}>;
 readFile(c:Computer,path:string,x:Context,opts?:{maxBytes?:number}):Promise<Uint8Array>;
 writeFile(c:Computer,file:{path:string;content:Uint8Array},x:Context):Promise<void>;
 stop(c:Computer,x:Context):Promise<void>;
}
export interface Homes {
 path(actor:string):string;
 load(actor:string):Promise<Computer|undefined>;
 save(actor:string,computer:Computer):Promise<void>;
}
function actorId(value:unknown):string {
 if(typeof value!=='string'||!/^[-_a-zA-Z0-9]{1,100}$/.test(value))throw Error('Invalid actor');return value;
}
function relative(value:unknown):string {
 if(typeof value!=='string'||!value||value.includes('\\')||value.startsWith('/')||value.includes('\0')||value.split('/').some(x=>!x||x==='.'||x==='..'))throw Error('Expected relative private-home path');return value;
}
function record(value:unknown):Record<string,unknown> {
 if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Expected object');return value as Record<string,unknown>;
}
function exact(obj:Record<string,unknown>,keys:string[]) {if(Object.keys(obj).some(k=>!keys.includes(k)))throw Error('Unexpected field')}
export class DirectComputer {
 private busy=new Set<string>();private computers=new Map<string,Computer>();private interrupted=new Set<string>();private controllers=new Map<string,AbortController>();
 constructor(private provider:Provider,private homes:Homes,private uid:()=>string,
             private image64:(v:Uint8Array)=>string,private allowRemote=false) {
   const id=provider.describe().id;
   if(/desktop|this-mac|host-aware/.test(id))throw Error('Host computer is not an isolated Private Computer');
   if(!/^(docker|fake)$/.test(id))throw Error('Remote provisioning needs explicit operator enablement');
 }
 describe(){return {protocol:'lelock-rakazo/1',provider:this.provider.describe().id,actor_mode:'direct',private_computers:true,agent_runtime:false}}
 async call(operation:string,raw:unknown) {
  const p=record(raw);exact(p,['actor','arguments']);const actor=actorId(p.actor),args=record(p.arguments);
  if(!['execute','observe','act','read','write','stop'].includes(operation))throw Error('Unknown computer operation');
  if(this.busy.has(actor)){
   if(operation!=='stop')throw Error('Character computer already has an active operation');
   this.controllers.get(actor)?.abort();const c=this.computers.get(actor);
   if(!c)throw Error('Provisioning is still in flight; wait for its reference before stopping');
   await this.provider.stop(c,{operationId:this.uid(),traceId:this.uid(),spaceId:'lelock-private',userId:'local-operator',botId:actor,runId:this.uid(),signal:AbortSignal.timeout(15000)});
   return {actor,stopped:true,reconciliation_required:true};
  }
  if(this.interrupted.has(actor)&&operation!=='stop')throw Error('Uncertain operation: operator must inspect/stop before continuing');
  this.busy.add(actor);
  const abort=new AbortController();this.controllers.set(actor,abort);const timer=setTimeout(()=>abort.abort(),150000);
  const ctx:Context={operationId:this.uid(),traceId:this.uid(),spaceId:'lelock-private',userId:'local-operator',botId:actor,runId:this.uid(),signal:abort.signal};
  let effect=false;
  try {
   let computer=this.computers.get(actor);
   if(operation==='stop') {
    exact(args,[]);computer=computer??await this.homes.load(actor);
    if(computer&&computer.botId!==actor)throw Error('Stored reference belongs to another character');
    if(computer)await this.provider.stop(computer,ctx);
    this.interrupted.delete(actor);this.computers.delete(actor);
    return {actor,stopped:true,already_absent:!computer};
   }
   if(!computer){
    const saved=await this.homes.load(actor);
    if(saved&&saved.botId!==actor)throw Error('Stored computer belongs to another character');
    computer=await this.provider.provision({botId:actor,homePath:this.homes.path(actor),providerRef:saved?.providerRef,providerKind:saved?.kind},ctx);
    if(computer.botId!==actor)throw Error('Provider returned a computer owned by another character');
    // Save opaque reference before fallible setup; never lose ownership on prepare failure.
    await this.homes.save(actor,computer);this.computers.set(actor,computer);
    try{await this.provider.prepare(computer,ctx)}catch(e){this.interrupted.add(actor);throw e}
   }
   switch(operation){
    case 'execute': {
     exact(args,['argv','timeoutMs']);const argv=args.argv;
     if(!Array.isArray(argv)||!argv.length||argv.length>80||argv.some(x=>typeof x!=='string'||x.length>64000||x.includes('\0')))throw Error('Invalid argv');
     const timeoutMs=args.timeoutMs??60000;
     if(!Number.isInteger(timeoutMs)||Number(timeoutMs)<1||Number(timeoutMs)>120000)throw Error('Invalid timeout');
     effect=true;let stdout='',stderr='',exit:number|undefined;
     for await(const event of this.provider.execute(computer,{argv,timeoutMs:Number(timeoutMs)},ctx)){
      if(event.type==='stdout')stdout+=event.data??'';
      if(event.type==='stderr')stderr+=event.data??'';
      if(event.type==='exit')exit=event.code;
      if(stdout.length+stderr.length>250000){abort.abort();throw Error('Computer output limit; effect uncertain')}
     }
     if(exit===undefined)throw Error('No exit receipt; effect uncertain');
     return {actor,computer:computer.id,exit_code:exit,stdout,stderr,delegated:false};
    }
    case 'observe': {
     exact(args,[]);const frame=await this.provider.observe(computer,ctx);
     if(!['image/png','image/jpeg'].includes(frame.mimeType)||frame.image.byteLength>2_000_000)throw Error('Unsupported or oversized frame');
     return {actor,frame_id:frame.frameId,width:frame.width,height:frame.height,content:[{type:'image',mimeType:frame.mimeType,data:this.image64(frame.image)}]};
    }
    case 'act': {
     exact(args,['actions_json']);if(typeof args.actions_json!=='string'||args.actions_json.length>64000)throw Error('Expected bounded action JSON');
     const actions=JSON.parse(args.actions_json);
     if(!Array.isArray(actions)||!actions.length||actions.length>20)throw Error('Expected 1–20 actions');
     for(const rawAction of actions){const a=record(rawAction);if(!['key','pointer','clipboard','scroll','wait','open','launch'].includes(String(a.kind)))throw Error('Unknown action kind')}
     effect=true;const result=await this.provider.act(computer,{actions,observe:false},ctx);
     if(result.completed!==actions.length)throw Error('Partial computer action; inspect before repeating');
     return {actor,completed:result.completed,delegated:false};
    }
    case 'read': {
     exact(args,['path']);const data=await this.provider.readFile(computer,relative(args.path),ctx,{maxBytes:250000});
     if(data.byteLength>250000)throw Error('File exceeds output limit');
     return {actor,path:args.path,content:new TextDecoder('utf-8',{fatal:true}).decode(data)};
    }
    case 'write': {
     exact(args,['path','content']);const path=relative(args.path);
     if(typeof args.content!=='string'||args.content.length>200000)throw Error('Content too large');
     const bytes=new TextEncoder().encode(args.content);effect=true;
     await this.provider.writeFile(computer,{path,content:bytes},ctx);
     const got=await this.provider.readFile(computer,path,ctx,{maxBytes:bytes.length+1});
     if(got.length!==bytes.length||got.some((x,i)=>x!==bytes[i]))throw Error('Readback mismatch');
     return {actor,path,bytes:bytes.length,verified:true,delegated:false};
    }

   }
  }catch(e){if(effect)this.interrupted.add(actor);throw e}
  finally{clearTimeout(timer);this.busy.delete(actor);this.controllers.delete(actor)}
 }
}
