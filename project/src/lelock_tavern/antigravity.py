"""Native agy stream protocol with workspace MCP. Native permissions are an additional boundary."""
from __future__ import annotations
import os, queue, time
from pathlib import Path
from .common import BridgeError, atomic_json, private
from .jsonl import JsonlProcess

class Antigravity:
    def close(self):pass  # Each run owns and closes its process.
    def __init__(self,argv=None):self.argv=argv or ['agy']
    def run(self,*,prompt,system,model,schemas,call_tool,stop,emit,seconds=300,
            native_workspace=None,mcp_config=None,native_risk_ack=False,native_yolo=False,**_):
        if not native_risk_ack:raise BridgeError('Antigravity native tools need explicit host-risk acknowledgement')
        if native_workspace is None or mcp_config is None:raise BridgeError('Scoped MCP workspace missing')
        workspace=private(Path(native_workspace));config_path=workspace/'.agents'/'mcp_config.json'
        # Own generated workspace only; never overwrite the user\'s global agy config.
        atomic_json(config_path,{'mcpServers':{'lelock':mcp_config}})
        argv=self.argv+['--input-format','stream-json','--output-format','stream-json']
        if model:argv+=['--model',model]
        if native_yolo:argv+=['--dangerously-skip-permissions']
        env={k:v for k,v in os.environ.items() if k in {'PATH','HOME','LANG','TMPDIR','SYSTEMROOT','PYTHONPATH'}}
        # HOME deliberately stays the user's native-login home. We do not inspect or copy cached credentials.
        wire=JsonlProcess(argv,cwd=workspace,env=env);deadline=time.monotonic()+seconds
        try:
            wire.send({'event':'user','message':{'content':system+'\n\n'+prompt}})
            while True:
                if stop.is_set() or time.monotonic()>deadline:raise BridgeError('Native turn interrupted; effects may have occurred')
                try:e=wire.receive(.1)
                except queue.Empty:continue
                if e is None or isinstance(e,BaseException):raise BridgeError('agy ended without a successful result')
                if e.get('event')=='init':emit('provider_notice',{'message':'Antigravity native permissions apply alongside Lelock tool policy.'})
                if e.get('event')=='step_update':
                    s=e.get('step_update',{})
                    if s.get('step_type')=='agent_response':emit('text',{'text':s.get('text_delta','')})
                    if s.get('step_type')=='tool':emit('native_tool',{'name':s.get('tool_name'),'state':s.get('state')})
                if e.get('event')=='result':
                    r=e.get('result',{})
                    if r.get('status')!='SUCCESS':raise BridgeError('Antigravity requires login, approval, quota, or recovery; inspect its native client')
                    return {'text':r.get('response',''),'provider':'antigravity','conversation_id':r.get('conversation_id'),
                            'usage':r.get('usage',{}),'actor_mode':'direct'}
        finally:wire.close()
