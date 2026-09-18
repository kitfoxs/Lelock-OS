/** Run with Rakazo's installed tsx: pnpm exec tsx integrations/lelock-v03/entry.mjs */
import {createInterface} from 'node:readline';
import {mkdir,readFile,writeFile,rename,lstat} from 'node:fs/promises';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
// Actual Rakazo factory, not an invented public REST endpoint and NOT the Pi runtime.
import {createSandboxProvider} from '../../packages/adapters/src/sandbox-factory.ts';
import {DirectComputer} from './service.ts';
const root=process.env.LELOCK_RAKAZO_HOME;
if(!root||!path.isAbsolute(root))throw Error('Set a new absolute LELOCK_RAKAZO_HOME');
const kind=process.env.LELOCK_RAKAZO_PROVIDER??'docker';
if(kind!=='docker')throw Error('Live sidecar requires an actual isolated computer provider');
const provider=createSandboxProvider(kind,{
 supervisorUrl:process.env.SANDBOX_SUPERVISOR_URL??'http://127.0.0.1:7091',supervisorToken:process.env.SANDBOX_SUPERVISOR_TOKEN,
 e2bApiKey:process.env.E2B_API_KEY,daytonaApiKey:process.env.DAYTONA_API_KEY,
 boxApiKey:process.env.BOX_API_KEY,dataDir:root
});
await mkdir(root,{recursive:true,mode:0o700});
if((await lstat(root)).isSymbolicLink())throw Error('Linked home root refused');
const homes={
 path:actor=>path.join(root,'homes',actor),
 async load(actor){await mkdir(path.join(root,'homes',actor),{recursive:true,mode:0o700});
  if((await lstat(path.join(root,'homes',actor))).isSymbolicLink())throw Error('Linked character home refused');
  try{return JSON.parse(await readFile(path.join(root,actor+'.json'),'utf8'))}catch(e){if(e.code==='ENOENT')return undefined;throw e}},
 async save(actor,value){const target=path.join(root,actor+'.json');const tmp=target+'.'+randomUUID();
  await mkdir(path.join(root,'homes',actor),{recursive:true,mode:0o700});
  await writeFile(tmp,JSON.stringify(value),{mode:0o600,flag:'wx'});await rename(tmp,target)}
};
const service=new DirectComputer(provider,homes,randomUUID,x=>Buffer.from(x).toString('base64'));
const lines=createInterface({input:process.stdin,crlfDelay:Infinity});
const respond=value=>process.stdout.write(JSON.stringify(value)+'\n');
for await(const line of lines){
 if(line.length>2_000_000){respond({id:null,error:{code:-32600,message:'Request too large'}});continue}
 let m;
 try{m=JSON.parse(line)}catch{respond({id:null,error:{code:-32700,message:'Invalid JSON'}});continue}
 // Independent actors may progress concurrently; DirectComputer fences each private computer.
 void(async()=>{
  try{
   const result=m.method==='describe'?service.describe():m.method?.startsWith('computer/')?await service.call(m.method.slice(9),m.params):(()=>{throw Error('Unknown method')})();
   respond({id:m.id,result});
  }catch(e){respond({id:m.id,error:{code:-32000,message:String(e.message).slice(0,500)}})}
 })();
}
