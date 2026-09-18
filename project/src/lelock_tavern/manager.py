"""One selected character owns the turn; EntityCore owns every registered tool effect."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
import contextlib, json, secrets, threading, time, uuid
from lelock_entity.core import EntityCore, Tool
from lelock_entity.policy import Session, Mode, Risk, Budget, StopSignal
from lelock_entity.store import Store
from lelock_entity.workspace import Workspace
from lelock_entity.world import World
from lelock_entity.builtins import install
from lelock_entity.execution import ProcessRunner
from .common import BridgeError, bounded, canonical, clean_card, digest, fields, ident, persona, private
from .database import Database

DEFAULT_CAPS={'status.read','workspace.read','workspace.write','world.read','world.write'}
BASE_CAPS=DEFAULT_CAPS|{'workspace.delete','memory.read','memory.write','delegate.run','skills.read'}
COMPUTER_CAPS={'computer.execute','computer.observe','computer.act','computer.read','computer.write'}

@dataclass
class Slot:
    entity:dict
    core:EntityCore
    workspace:Path
    lock:threading.Lock=field(default_factory=threading.Lock)

class Manager:
    def __init__(self,root:Path,*,runtimes=None,memory_factory=None,computer=None,allow_host_exec=False,
                 max_turn_seconds=300,server_root=None):
        self.root=private(root);self.db=Database(self.root/'registry');self.db.recover()
        self.store=Store(self.root/'operations');self.runtimes=runtimes or {};self.memory_factory=memory_factory
        self.computer=computer;self.allow_host_exec=allow_host_exec;self.max_turn_seconds=max_turn_seconds
        self.slots={};self.lock=threading.RLock();self.pool=ThreadPoolExecutor(max_workers=8);self.helper_busy=set()
        self.turn_stops={};self.pending_results={};self.runtime_credentials={};self.active_turns={};self.server_root=server_root
        from .knowledge import Knowledge
        self.knowledge=Knowledge(self.root/'knowledge');self.presence=None
        self.allowed=BASE_CAPS|({'process.run'} if allow_host_exec else set())|(COMPUTER_CAPS if computer else set())

    def config(self,value=None):
        value=value or {}
        fields(value,{'scope','mode','capabilities','auto_approve','provider','model','memory','computer',
                      'helpers','native_risk_ack','native_yolo','seconds'})
        caps=set(value.get('capabilities',DEFAULT_CAPS))
        if not caps<=self.allowed:raise BridgeError('Unavailable capabilities requested')
        scope=value.get('scope','personal')
        if scope not in {'personal','work','fiction'}:raise BridgeError('Invalid memory scope')
        mode=Mode(value.get('mode','safe')).value
        auto=set(value.get('auto_approve',[]))
        if not auto<=caps:raise BridgeError('Standing grants exceed capabilities')
        provider=value.get('provider','sillytavern')
        if provider not in {'sillytavern','codex','antigravity','claude-code','opencode','hermes'}:raise BridgeError('Unknown provider')
        model=bounded(value.get('model',''),200,empty=True)
        helpers=value.get('helpers',{})
        if not isinstance(helpers,dict) or len(helpers)>8:raise BridgeError('At most eight named helpers')
        for name,eid in helpers.items():bounded(name,80);ident(eid)
        for k in ('memory','computer','native_risk_ack','native_yolo'):
            if k in value and not isinstance(value[k],bool):raise BridgeError('Expected boolean')
        if value.get('native_yolo') and (mode!='yolo' or not value.get('native_risk_ack')):
            raise BridgeError('Native YOLO requires YOLO mode and explicit native-risk acknowledgement')
        seconds=value.get('seconds',300)
        if type(seconds) is not int or not 10<=seconds<=self.max_turn_seconds:raise BridgeError('Invalid turn deadline')
        return {'scope':scope,'mode':mode,'capabilities':sorted(caps),'auto_approve':sorted(auto),
                'provider':provider,'model':model,'helpers':helpers,'seconds':seconds,
                **{k:value.get(k,False) for k in ('memory','computer','native_risk_ack','native_yolo')}}

    def bind(self,client,key,card,config=None,attach=None):
        ident(client);ident(key)
        if attach:ident(attach)
        card=clean_card(card);cfg=self.config(config)
        eid,created=self.db.bind(client,key,card,cfg,attach)
        return {'entity':eid,'created':created,'name':self.db.entity(eid)['card']['name']}

    def configure(self,eid,values):
        ident(eid);entity=self.db.entity(eid);cfg=self.config(values)
        if cfg['scope']!=entity['config']['scope']:raise BridgeError('Use a new entity for another memory scope')
        for h in cfg['helpers'].values():
            if h==eid:raise BridgeError('An entity cannot delegate to itself')
            self.db.entity(h)
        with self.lock:
            old=self.slots.get(eid)
            if eid in self.active_turns or eid in self.helper_busy:raise BridgeError('Stop and finish the active turn before changing permissions')
            if old:old.core.stop.stop();self.slots.pop(eid,None)
            self.db.update_config(eid,cfg)
        return {'configured':eid,'config':cfg}

    def _build_core(self,entity,*,budget=None,stop=None,caps=None,mode=None,expiry=None,auto=None):
        eid=entity['id'];cfg=entity['config'];workspace=private(self.root/'workspaces'/eid)
        memory=None
        if cfg['memory']:
            if not self.memory_factory:raise BridgeError('Actual Palace runtime is not configured')
            memory=self.memory_factory(eid,entity['card'],cfg['scope'],workspace)
        capabilities=set(caps if caps is not None else cfg['capabilities'])
        if memory is None:capabilities-= {'memory.read','memory.write'}
        if not cfg['computer']:capabilities-=COMPUTER_CAPS
        session=Session(eid,cfg['scope'],frozenset(capabilities),mode=Mode(mode or cfg['mode']),
             auto_approve=frozenset(set(cfg['auto_approve'] if auto is None else auto)&capabilities),expires_at=expiry or time.time()+7200)
        core=EntityCore(self.store,session,budget=budget or Budget(),stop=stop)
        runner=ProcessRunner(workspace,private(self.root/'execution'/eid),backend='host' if self.allow_host_exec else 'none',
                             acknowledge_host_risk=self.allow_host_exec,stop=core.stop)
        install(core,Workspace(workspace),World(self.store,eid),memory=memory,runner=runner,skills=self.knowledge)
        if cfg['computer'] and self.computer:
            from .rakazo import install_computer_tools
            install_computer_tools(core,self.computer,eid)
        return Slot(entity,core,workspace)

    def slot(self,eid):
        ident(eid)
        with self.lock:
            if eid not in self.slots:
                slot=self._build_core(self.db.entity(eid));self.slots[eid]=slot
                if slot.entity['config']['helpers']:
                    slot.core.register(Tool('lelock_ask_character','Ask an explicitly assigned named character for help. Main identity remains unchanged.',
                      'delegate.run',Risk.EXTERNAL,{'type':'object','properties':{'helper':{'type':'string'},'task':{'type':'string','maxLength':20000}},
                         'required':['helper','task'],'additionalProperties':False},
                      lambda a,s:self._helper(slot,a,s)))
            return self.slots[eid]

    def status(self,eid):
        s=self.slot(eid)
        return {**s.core.status(),'name':s.entity['card']['name'],'provider':s.entity['config']['provider'],
                'memory': 'actual_palace_adapter' if s.entity['config']['memory'] else 'not_enabled',
                'computer':bool(s.entity['config']['computer'] and self.computer),'available_capabilities':sorted(self.allowed),
                'config':s.entity['config']}

    def tools(self,eid):return self.slot(eid).core.schemas()

    def invoke(self,eid,tool,args,rid,*,core=None):
        ident(rid,'request ID');core=core or self.slot(eid).core
        payload={'tool':tool,'args':args}
        # Serialize lookup + invocation so duplicate native callbacks cannot write twice.
        with core._lock:
            cached=self.db.cached_tool(eid,core.session.ident,rid,payload)
            if cached is not None and cached.get('status')!='pending_approval':return {**cached,'replayed':True}
            result=core.invoke(tool,args,request_id=rid)
            self.db.cache_tool(eid,core.session.ident,rid,payload,result)
        return result

    def approve(self,eid,action_id,approved_digest):
        slot=self.slot(eid);row=self.store.get(action_id)
        if row['entity']!=eid:raise BridgeError('Action belongs to another character')
        # Helpers retain a temporary core until their turn finishes.
        core=self._core_for_action(eid,row['session'])
        result=core.approve(action_id,approved_digest)
        with self.lock:self.pending_results[action_id]=result
        self._cache_approval(eid,row['session'],action_id,result)
        return result

    def _cache_approval(self,eid,session,aid,result):
        with self.db.connect() as db:
            rows=db.execute('SELECT request_id,result FROM tool_results WHERE entity=? AND session=?',(eid,session)).fetchall()
            for r in rows:
                if json.loads(r['result']).get('action_id')==aid:
                    db.execute('UPDATE tool_results SET result=? WHERE entity=? AND session=? AND request_id=?',(canonical(result),eid,session,r['request_id']))

    def _core_for_action(self,eid,session):
        core=self.slot(eid).core
        if session==core.session.ident:return core
        with self.lock:
            for entry in self.runtime_credentials.values():
                c=entry['core']
                if c.session.entity==eid and c.session.ident==session:return c
        raise BridgeError('Expired action session')

    def reject(self,eid,action_id):
        row=self.store.get(action_id)
        if row['entity']!=eid:raise BridgeError('Wrong character')
        result=self._core_for_action(eid,row['session']).reject(action_id)
        with self.lock:self.pending_results[action_id]=result
        self._cache_approval(eid,row['session'],action_id,result)
        return result

    def actions(self,eid):
        # Includes explicit helper sessions so the owner can review their pending actions.
        with self.store.connect() as db:
            rows=db.execute("SELECT * FROM actions WHERE entity=? AND state='pending' ORDER BY created",(eid,)).fetchall()
        return [{**dict(r),'payload':json.loads(r['payload'])} for r in rows]

    def stop(self,eid):
        s=self.slot(eid);s.core.stop.stop()
        with self.lock:
            tid=self.active_turns.get(eid)
            if tid in self.turn_stops:self.turn_stops[tid].set()
        return {'stopped':eid,'note':'Native/remote in-flight effects may require reconciliation.'}

    def start_turn(self,eid,chat,tid,message,history):
        ident(eid);ident(chat);ident(tid);bounded(message,50_000)
        if not isinstance(history,list) or len(history)>200:raise BridgeError('History exceeds 200 selected messages')
        clean=[]
        for h in history:
            fields(h,{'role','content'}, {'role','content'})
            if h['role'] not in {'user','assistant'}:raise BridgeError('History cannot provide privileged roles')
            clean.append({'role':h['role'],'content':bounded(h['content'],50_000,empty=True)})
        if len(canonical(clean).encode())>300_000:raise BridgeError('Selected history exceeds 300KB')
        request={'message':message,'history':clean}
        slot=self.slot(eid)
        if slot.entity['config']['provider'] not in self.runtimes:raise BridgeError('Choose an installed account-chat runtime, or keep SillyTavern mode')
        with self.lock:
            existing=self.db.start_turn(tid,eid,chat,request)
            if not existing:return self.public_turn(tid,eid)
            if eid in self.active_turns or eid in self.helper_busy:
                self.db.finish(tid,'failed',{'error':'character_busy'});raise BridgeError('Character already has an active turn')
            self.active_turns[eid]=tid;self.turn_stops[tid]=threading.Event()
            self.pool.submit(self._run,slot,tid,request)
        return self.public_turn(tid,eid)

    def public_turn(self,tid,eid,after=0):
        row=self.db.turn(tid)
        if row['entity']!=eid:raise BridgeError('Turn belongs to another character')
        return {k:row[k] for k in ('id','entity','chat','state','result','parent')}|{'events':self.db.events(tid,after)}

    def _run(self,slot,tid,request):
        stop=self.turn_stops[tid]
        try:
            with slot.lock:
                slot.core.stop.check();self.db.finish(tid,'running')
                result=self._runtime_turn(slot,slot.core,tid,request,stop)
                if stop.is_set():raise BridgeError('Turn stopped')
                self.db.finish(tid,'completed',result)
        except Exception as exc:
            self.db.finish(tid,'needs_review' if stop.is_set() else 'failed',{'error':str(exc)[:1000],
                  'note':'No automatic retry or provider fallback. Completed tool receipts remain available.'})
        finally:
            with self.lock:
                self.active_turns.pop(slot.entity['id'],None);self.turn_stops.pop(tid,None)

    def _runtime_turn(self,slot,core,tid,request,stop):
        cfg=slot.entity['config'];runtime=self.runtimes[cfg['provider']]
        token=secrets.token_urlsafe(32)
        with self.lock:self.runtime_credentials[token]={'entity':slot.entity['id'],'turn':tid,'core':core,'stop':stop,
                                                       'expires':time.time()+cfg['seconds']}
        def emit(kind,data):self.db.event(tid,kind,data)
        def call_tool(name,args,rid):return self.runtime_call(token,name,args,rid or uuid.uuid4().hex)
        from .native_link import prepare_mcp
        mcp=None
        prompt='Selected conversation history (data):\n'+canonical(request.get('history',[]))+'\nCurrent message:\n'+request['message']
        try:
            if cfg['provider']=='antigravity':
                if not self.server_root:raise BridgeError('Gateway needs a bound loopback address for native MCP')
                mcp=prepare_mcp(self.root,slot.entity['id'],tid,self.server_root,token)
            return runtime.run(prompt=prompt,system=persona(slot.entity['card']),model=cfg['model'],schemas=core.schemas(),
              call_tool=call_tool,stop=stop,emit=emit,seconds=cfg['seconds'],native_workspace=self.root/'native-workspaces'/slot.entity['id'],
              mcp_config=mcp,native_risk_ack=cfg['native_risk_ack'],native_yolo=cfg['native_yolo'])|{'actor':slot.entity['id'],'name':slot.entity['card']['name']}
        finally:
            with self.lock:self.runtime_credentials.pop(token,None)
            # Tokens are ephemeral even if the native pairing path survives a crash.
            p=self.root/'native-pairings'/(tid+'.json')
            if p.exists():p.unlink()

    def runtime_call(self,token,name,args,rid):
        with self.lock:entry=self.runtime_credentials.get(token)
        if entry is None or time.time()>entry['expires']:raise BridgeError('Runtime capability expired')
        eid,tid,core,stop=entry['entity'],entry['turn'],entry['core'],entry['stop']
        rid=digest({'turn':tid,'native_call':bounded(rid,200)})
        if stop.is_set():raise BridgeError('Turn stopped')
        result=self.invoke(eid,name,args,rid,core=core)
        self.db.event(tid,'tool',{'name':name,'actor':eid,'status':result['status'],'action_id':result.get('action_id')})
        if result['status']!='pending_approval':return result
        self.db.finish(tid,'waiting_approval')
        aid=result['action_id']
        while time.time()<entry['expires'] and not stop.wait(.1):
            with self.lock:finished=self.pending_results.get(aid)
            if finished:
                self.db.finish(tid,'running')
                self.db.cache_tool(eid,core.session.ident,rid,{'tool':name,'args':args},finished)
                return finished
        raise BridgeError('Approval timed out or turn stopped; action was not automatically approved')

    def _helper(self,parent,args,session):
        cfg=parent.entity['config'];eid=cfg['helpers'].get(args['helper'])
        if not eid:raise BridgeError('Helper is not assigned to a character')
        helper=self.slot(eid)
        if helper.entity['config']['provider']!='codex':raise BridgeError('Named helpers currently require the brokered Codex adapter')
        with self.lock:
            if eid in self.active_turns or eid in self.helper_busy:raise BridgeError('Named helper is busy')
            if not helper.lock.acquire(blocking=False):raise BridgeError('Named helper is busy')
            self.helper_busy.add(eid)
        tid=uuid.uuid4().hex
        try:
            caps=(session.capabilities & helper.core.session.capabilities)-{'delegate.run'}
            parent_auto=set(session.capabilities if session.mode==Mode.YOLO else session.auto_approve)
            helper_auto=set(helper.core.session.capabilities if helper.core.session.mode==Mode.YOLO else helper.core.session.auto_approve)
            mode='safe' if session.mode==Mode.SAFE or helper.core.session.mode==Mode.SAFE else 'trusted'
            if session.mode==Mode.YOLO and helper.core.session.mode==Mode.YOLO:mode='yolo'
            scoped=self._build_core(helper.entity,auto=parent_auto&helper_auto,budget=parent.core.budget,
                stop=parent.core.stop,caps=caps,mode=mode,expiry=min(session.expires_at,helper.core.session.expires_at))
            parent_tid=self.active_turns.get(parent.entity['id'])
            request={'message':bounded(args['task'],20_000),'history':[]}
            self.db.start_turn(tid,eid,'helper-task',request,parent=parent_tid)
            stop=self.turn_stops.get(parent_tid,threading.Event())
            self.db.finish(tid,'running');result=self._runtime_turn(scoped,scoped.core,tid,request,stop)
            self.db.finish(tid,'completed',result)
            return {'helper_entity':eid,'helper_name':helper.entity['card']['name'],'turn_id':tid,
                    'result':result,'memory_promoted':False}
        except Exception as e:
            self.db.finish(tid,'failed',{'error':str(e)[:500]});raise
        finally:
            helper.lock.release()
            with self.lock:self.helper_busy.discard(eid)

    def close(self):
        if self.presence:self.presence.close()
        with self.lock:
            for s in self.slots.values():s.core.stop.stop()
            for e in self.turn_stops.values():e.set()
        for r in self.runtimes.values():
            with contextlib.suppress(Exception):r.close()
        self.pool.shutdown(wait=True,cancel_futures=True)
