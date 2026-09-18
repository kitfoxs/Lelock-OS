"""Operator-reviewed knowledge packs; durable pins, not executable plugins."""
from pathlib import Path
import threading
from lelock_entity.skills import SkillLibrary
from .common import atomic_json, private, strict_load

class Knowledge:
    def __init__(self,root):
        self.root=private(Path(root));self.path=self.root/'reviewed.json';self.lock=threading.RLock()
        self.packs=private(self.root/'packs')
        approved=strict_load(self.path.read_bytes()) if self.path.exists() else {}
        self.library=SkillLibrary(self.packs,approved)
    def inspect(self,name):
        with self.lock:s=self.library.inspect(name)
        return {'name':s.name,'description':s.description,'content':s.content,'sha256':s.sha256,
                'files':list(s.files),'capabilities_requested':list(s.capabilities_requested),'permissions_granted':[]}
    def approve(self,name,sha256):
        with self.lock:
            self.library.approve(name,sha256);atomic_json(self.path,self.library.approved)
        return {'approved':name,'sha256':sha256,'permissions_granted':[]}
    def load(self,name):
        with self.lock:return self.library.load(name)
