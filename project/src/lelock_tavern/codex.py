"""Official Codex app-server route. No auth.json parsing, token copying, or direct subscription HTTP."""
from __future__ import annotations
import os, queue, threading, time
from pathlib import Path
from .common import BridgeError, canonical, private
from .jsonl import RPC

class Codex:
    def __init__(self,state:Path,argv=None):
        home=private(state/'codex-home');cwd=private(state/'codex-empty-workspace')
        env={k:v for k,v in os.environ.items() if k in {'PATH','HOME','LANG','TMPDIR','SYSTEMROOT'}}
        env['CODEX_HOME']=str(home)
        # Deliberately no API key environment: never silently turn subscription exhaustion into a bill.
        self.calls={};self.events={};self.overflow=set();self.lock=threading.Lock()
        self.rpc=RPC(argv or ['codex','app-server'],cwd=cwd,env=env,on_request=self._call,on_event=self._event)
        self.rpc.request('initialize',{'clientInfo':{'name':'lelock-tavern','version':'0.3.0'},'capabilities':{'experimentalApi':True}})
        self.rpc.notify('initialized')
        self.cwd=cwd
    def account(self):
        r=self.rpc.request('account/read',{'refreshToken':False})
        # No raw secrets forwarded. Return only documented account summary.
        a=(r or {}).get('account') or {}
        return {'signed_in':a.get('type')=='chatgpt','type':a.get('type'),'plan':a.get('planType')}
    def login(self,device=False):
        r=self.rpc.request('account/login/start',{'type':'chatgptDeviceCode' if device else 'chatgpt'})
        return {k:r[k] for k in ('type','loginId','authUrl','verificationUrl','userCode') if k in r}
    def logout(self):return self.rpc.request('account/logout')
    def quotas(self):
        r=self.rpc.request('account/rateLimits/read')
        return {k:r[k] for k in ('rateLimits','rateLimitsByLimitId') if k in r}
    def models(self):
        models=[];cursor=None
        for _ in range(20):
            r=self.rpc.request('model/list',{'cursor':cursor,'limit':100,'includeHidden':False})
            models.extend(r.get('data',[]));cursor=r.get('nextCursor')
            if not cursor:break
        return [{'id':m.get('model') or m.get('id'),'label':m.get('displayName') or m.get('model') or m.get('id')} for m in models]
    def _event(self,method,params):
        thread=params.get('threadId')
        with self.lock:q=self.events.get(thread)
        if q is not None:
            try:q.put_nowait((method,params))
            except queue.Full:
                with self.lock:self.overflow.add(thread)  # Fail the turn rather than silently lose its completion receipt.
    def _call(self,method,p):
        if method!='item/tool/call':raise BridgeError('Native built-in approval is not a Lelock approval')
        with self.lock:callback=self.calls.get(p.get('threadId'))
        if callback is None:raise BridgeError('No active character owns this native thread')
        result=callback(p['tool'],p['arguments'],str(p.get('callId') or p.get('itemId') or ''))
        # Preserve screenshots as real multimodal content, not base64 embedded in prose.
        body=result.get('result',{})
        images=body.get('content',[]) if isinstance(body,dict) else []
        sanitized={**result,'result':{k:v for k,v in body.items() if k!='content'}} if isinstance(body,dict) else result
        items=[{'type':'inputText','text':canonical(sanitized)}]
        for c in images:
            if c.get('type')=='image' and c.get('mimeType') in {'image/png','image/jpeg'}:
                items.append({'type':'inputImage','imageUrl':'data:'+c['mimeType']+';base64,'+c['data']})
        return {'contentItems':items,'success':result.get('status')=='done'}
    def run(self,*,prompt,system,model,schemas,call_tool,stop,emit,seconds=300,**_):
        if not self.account()['signed_in']:raise BridgeError('Sign in to ChatGPT / Codex first')
        if model and model not in {m['id'] for m in self.models()}:raise BridgeError('Model is not in this account runtime catalog')
        specs=[{'type':'function','name':s['name'],'description':s['description'],'inputSchema':s['parameters']} for s in schemas]
        params={'cwd':str(self.cwd),'sandbox':'read-only','approvalPolicy':'untrusted',
          'baseInstructions':system,'ephemeral':True,'dynamicTools':specs,
          'config':{'features.shell_tool':False,'features.unified_exec':False,'features.skill_mcp_dependency_install':False,
                    'web_search':'disabled','history.persistence':'none'}}
        if model:params['model']=model
        thread=self.rpc.request('thread/start',params)['thread']['id']
        events=queue.Queue(maxsize=4096)
        with self.lock:self.calls[thread]=call_tool;self.events[thread]=events
        turn=None;deadline=time.monotonic()+seconds;answer=[]
        try:
            started=self.rpc.request('turn/start',{'threadId':thread,'input':[{'type':'text','text':prompt}]})
            turn=started['turn']['id']
            while True:
                if stop.is_set() or time.monotonic()>deadline:
                    try:self.rpc.request('turn/interrupt',{'threadId':thread,'turnId':turn},timeout=5)
                    finally:raise BridgeError('Turn interrupted; verify effects before retrying')
                if thread in self.overflow:
                    self.rpc.request('turn/interrupt',{'threadId':thread,'turnId':turn},timeout=5)
                    raise BridgeError('Codex event queue overflowed; reconcile recorded effects')
                if self.rpc.stopped.is_set():raise BridgeError('Codex disconnected during the turn')
                try:method,p=events.get(timeout=.1)
                except queue.Empty:continue
                if method=='item/agentMessage/delta':emit('text',{'text':p.get('delta','')})
                elif method=='item/completed' and p.get('item',{}).get('type')=='agentMessage':
                    # The completed message is authoritative; streamed deltas are display-only.
                    item=p['item']
                    if item.get('phase')!='commentary':answer.append(item.get('text',''))
                elif method=='turn/completed':
                    if p['turn'].get('status')!='completed':raise BridgeError('Codex turn did not complete')
                    return {'text':'\n'.join(answer),'provider':'codex','thread_id':thread,'actor_mode':'direct'}
                elif method=='error':emit('provider_notice',{'message':'Codex reported an error; no alternate model was selected.'})
        finally:
            with self.lock:self.calls.pop(thread,None);self.events.pop(thread,None);self.overflow.discard(thread)
    def close(self):self.rpc.close()
