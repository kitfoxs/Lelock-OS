"""Actual legacy MemPalace integration; missing dependencies fail, never simulate memory."""
from pathlib import Path
from contextlib import ExitStack
from .common import BridgeError, private

class PalaceLinks:
    def __init__(self,root):self.root=Path(root);self.stack=ExitStack();self.links={}
    def open(self,entity,card,scope,workspace):
        if entity in self.links:return self.links[entity]
        from lelock.config import initialize
        from lelock.palace import ManagedPalace
        from lelock.service import Service
        from lelock_entity.legacy import LegacyMemory
        from lelock_entity.lifecycle import ProfileLease
        home=self.root/'palaces'/entity
        if not (home/'config.json').exists():
            initialize(home,workspace,name=card['name'][:80],person='Companion owner',relationship='custom',
               endpoint='http://127.0.0.1:9',model='not-used-by-tavern-gateway',scope=scope)
        # Gateway uses only memory from this profile; provider selection belongs to the gateway.
        with ExitStack() as pending:
            pending.enter_context(ProfileLease(home/'entity-v02'))
            rpc=pending.enter_context(ManagedPalace(home))
            service=Service(home,rpc)
            if service.scope!=scope:raise BridgeError('Palace scope mismatch')
            link=LegacyMemory(service)
            self.stack.enter_context(pending.pop_all())
            self.links[entity]=link
            return link
    def close(self):self.stack.close()
