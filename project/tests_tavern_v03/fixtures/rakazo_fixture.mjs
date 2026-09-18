/** Uses production DirectComputer against a disposable FILE adapter, not real Rakazo/Docker. */
import {fileURLToPath,pathToFileURL} from 'node:url';
import {existsSync} from 'node:fs';
const here=fileURLToPath(new URL('.',import.meta.url));
const servicePath=[new URL('../overlay/integrations/rakazo-v03/dist/service.js',import.meta.url),new URL('../../../integrations/rakazo-v03/dist/service.js',import.meta.url)].find(u=>existsSync(u));
if(!servicePath)throw Error('Compile the included Rakazo service first');
const {DirectComputer}=await import(servicePath.href);
import {createInterface} from 'node:readline';import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';import {randomUUID} from 'node:crypto';
const root=process.argv[2];const files=new Map();
const provider={describe:()=>({id:'fake',capabilities:{graphical:false}}),
 provision:async r=>{await mkdir(path.join(root,r.botId),{recursive:true});return {id:r.botId,botId:r.botId,kind:'fake',providerRef:r.botId}},
 prepare:async()=>{},
 async *execute(c,r,ctx){yield {type:'stdout',data:'Scripted executor for '+ctx.botId};yield {type:'exit',code:0}},
 readFile:async(c,p)=>new Uint8Array(await readFile(path.join(root,c.botId,p))),
 writeFile:async(c,f)=>await writeFile(path.join(root,c.botId,f.path),f.content),
 stop:async()=>{},observe:async()=>{throw Error('No fixture screen')},act:async()=>{throw Error('No fixture screen')}
};
const service=new DirectComputer(provider,{path:a=>path.join(root,a),load:async()=>undefined,save:async()=>{}},randomUUID,x=>Buffer.from(x).toString('base64'));
const lines=createInterface({input:process.stdin,crlfDelay:Infinity});
for await(const line of lines){const m=JSON.parse(line);try{const result=m.method==='describe'?service.describe():await service.call(m.method.slice(9),m.params);console.log(JSON.stringify({id:m.id,result}))}catch{console.log(JSON.stringify({id:m.id,error:{code:-32000,message:'fixture failure'}}))}}
