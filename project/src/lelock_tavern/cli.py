"""Start the actual gateway, not a demonstration. No subscription is purchased or model queried on startup."""
from __future__ import annotations
import argparse, contextlib, json, os, signal, sys, threading
from pathlib import Path
from lelock_entity.lifecycle import ProfileLease
from .common import BridgeError, atomic_json, private
from .providers import catalog

class LazyCodex:
    def __init__(self,root):self.root=root;self.instance=None;self.lock=threading.Lock()
    def get(self):
        with self.lock:
            if self.instance is None:
                from .codex import Codex
                self.instance=Codex(self.root)
            return self.instance
    def account(self):return self.get().account()
    def login(self,device=False):return self.get().login(device)
    def models(self):return self.get().models()
    def logout(self):return self.get().logout()
    def quotas(self):return self.get().quotas()
    def run(self,**kwargs):return self.get().run(**kwargs)
    def close(self):
        if self.instance:self.instance.close()

def main():
    p=argparse.ArgumentParser(description='Lelock v0.3 Tavern gateway')
    p.add_argument('command',choices=['serve','doctor']);p.add_argument('--state',type=Path,default=Path.home()/'.local/share/lelock-tavern-v03')
    p.add_argument('--port',type=int,default=8781);p.add_argument('--origin',action='append',default=[])
    p.add_argument('--allow-host-exec',action='store_true',help='Enable unsandboxed OS-user command capability')
    p.add_argument('--enable-pulse',action='store_true',help='Allow explicitly authorized recurring model turns to a local inbox')
    p.add_argument('--rakazo-command-json',help='Operator-owned JSON argv for the supplied Rakazo sidecar')
    args=p.parse_args()
    if args.command=='doctor':print(json.dumps({'providers':catalog(),'note':'Availability is not a signed-in or live-tool test.'},indent=2));return
    root=private(args.state.expanduser().absolute())
    from .manager import Manager
    from .http_server import Server
    from .antigravity import Antigravity
    from .memory_link import PalaceLinks
    from .native_link import launch_native_login
    from .rakazo import RakazoComputer
    stopped=threading.Event();signal.signal(signal.SIGINT,lambda *_:stopped.set());signal.signal(signal.SIGTERM,lambda *_:stopped.set())
    with ProfileLease(root/'owner'):
        computer=RakazoComputer(json.loads(args.rakazo_command_json)) if args.rakazo_command_json else None
        palace=PalaceLinks(root)
        manager=Manager(root,runtimes={'codex':LazyCodex(root/'providers'),'antigravity':Antigravity()},
                        memory_factory=palace.open,computer=computer,allow_host_exec=args.allow_host_exec)
        from .presence import Presence
        manager.presence=Presence(manager,enabled=args.enable_pulse)
        server=Server(manager,port=args.port,origins=args.origin,native_login=lambda x:launch_native_login(root,x)).start()
        manager.presence.start()
        atomic_json(root/'operator-pairing.json',{'base':server.base,'agent_token':server.agent_token,'operator_token':server.operator_token})
        print('Lelock gateway:',server.base,'\nOne-time pairing code:',server.pair_code,
              '\nPair in the extension within ten minutes. This is a local developer service.',flush=True)
        try:stopped.wait()
        finally:
            # Keep HTTP alive while native turns are cancelled so waiting MCP callbacks can exit.
            manager.close();server.close();palace.close()
            if computer:computer.close()
if __name__=='__main__':main()
