"""Direct selected-character computer tools. This module never launches a Pi agent."""
from pathlib import Path
from .common import BridgeError, ident
from .jsonl import RPC
from lelock_entity.core import Tool
from lelock_entity.policy import Risk

class RakazoComputer:
    def __init__(self,argv,cwd=None):
        self.rpc=RPC(argv,cwd=cwd)
        hello=self.rpc.request('describe')
        if hello.get('protocol')!='lelock-rakazo/1':raise BridgeError('Wrong Rakazo adapter protocol')
        self.description=hello
    def call(self,actor,operation,args):
        ident(actor)
        # actor comes from the authenticated EntityCore registration closure, never model arguments.
        return self.rpc.request('computer/'+operation,{'actor':actor,'arguments':args},timeout=180)
    def close(self):self.rpc.close()

def install_computer_tools(core,computer,actor):
    s={'type':'string'}
    defs=[
     ('lelock_computer_run','Execute a command on YOUR assigned Rakazo Private Computer. No other agent is asked to act.',
      'computer.execute',Risk.EXECUTE,'execute',{'argv':{'type':'array','items':s,'minItems':1,'maxItems':80},
       'timeoutMs':{'type':'integer','minimum':1,'maximum':120000}},['argv']),
     ('lelock_computer_observe','See YOUR Rakazo computer screen. Requires a vision-capable runtime.',
      'computer.observe',Risk.READ,'observe',{},[]),
     ('lelock_computer_act','Operate YOUR computer. actions_json encodes a bounded array of pointer/key/scroll/wait/open/launch actions.',
      'computer.act',Risk.WRITE,'act',{'actions_json':s},['actions_json']),
     ('lelock_computer_read','Read a UTF-8 file from YOUR private computer home.',
      'computer.read',Risk.READ,'read',{'path':s},['path']),
     ('lelock_computer_write','Write a UTF-8 file in YOUR private computer home.',
      'computer.write',Risk.WRITE,'write',{'path':s,'content':s},['path','content'])]
    for name,description,cap,risk,op,props,required in defs:
        core.register(Tool(name,description,cap,risk,{'type':'object','properties':props,'required':required,'additionalProperties':False},
             lambda args,session,operation=op:computer.call(actor,operation,args)))
