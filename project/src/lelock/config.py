from __future__ import annotations
from dataclasses import dataclass, asdict
import ipaddress
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
from .common import LelockError, atomic_json, private_dir, read_json, text

DEFAULT_HOME = Path.home()/'.local/share/lelock-os'
RELATIONSHIPS = {'friendship','romance','study','creative','custom'}
MODES = {'ordinary','focus','comfort','creative','study'}

def endpoint_url(url: str, *, loopback_only: bool = False) -> str:
    p=urlsplit(url)
    if p.username or p.password or p.query or p.fragment or not p.hostname:
        raise LelockError('Endpoint must not contain credentials, a query, or a fragment.')
    try: local=ipaddress.ip_address(p.hostname).is_loopback
    except ValueError: local = p.hostname == 'localhost'
    if loopback_only and (not local or p.scheme != 'http'):
        raise LelockError('The managed Palace must be HTTP on loopback.')
    if p.scheme not in {'https','http'} or (p.scheme=='http' and not local):
        raise LelockError('Use HTTPS, or HTTP only for a local endpoint.')
    return url.rstrip('/')

@dataclass(frozen=True)
class Config:
    version: int
    profile_id: str
    companion_name: str
    person_name: str
    relationship: str
    workspace: str
    endpoint: str
    model: str
    api_key_env: str = 'LELOCK_MODEL_API_KEY'
    retention: str = 'explicit'
    max_iterations: int = 6
    max_output_tokens: int = 1536
    run_budget_seconds: int = 120
    mode: str = 'ordinary'
    scope: str = 'personal'

    @classmethod
    def load(cls, home: Path) -> 'Config':
        try: c=cls(**read_json(home/'config.json'))
        except (TypeError,ValueError) as exc: raise LelockError('Unsupported configuration shape.') from exc
        c.validate(home)
        return c

    def validate(self, home: Path) -> None:
        if self.version != 1 or not re.fullmatch(r'[a-f0-9]{32}',self.profile_id):
            raise LelockError('Unsupported profile version/identifier.')
        text(self.companion_name, maximum=80); text(self.person_name,maximum=80)
        if self.relationship not in RELATIONSHIPS or self.mode not in MODES:
            raise LelockError('Unsupported relationship or mode.')
        if self.scope not in {'personal','work','fiction'}: raise LelockError('Invalid profile scope.')
        if self.retention not in {'explicit','journal'}: raise LelockError('Unsupported retention.')
        if not re.fullmatch(r'[A-Z][A-Z0-9_]{2,100}',self.api_key_env):
            raise LelockError('Use an environment variable name, never an API key, in config.')
        endpoint_url(self.endpoint); text(self.model,maximum=200)
        if not (1<=self.max_iterations<=12 and 128<=self.max_output_tokens<=8192 and 10<=self.run_budget_seconds<=600):
            raise LelockError('Invalid turn budget.')
        root=Path(self.workspace)
        if not root.is_absolute() or root.is_symlink() or not root.is_dir():
            raise LelockError('Workspace must be an existing real directory.')
        h=home.resolve(); w=root.resolve()
        if h==w or h in w.parents or w in h.parents or w==Path.home().resolve() or w==Path('/'):
            raise LelockError('Workspace and application home must be separate, non-nested directories.')

    def save(self,home: Path):
        self.validate(home); atomic_json(home/'config.json',asdict(self))

DEFAULT_SOUL = """# Companion identity\nYou are {name}, {person}'s chosen AI companion.\nRelationship preference: {relationship}. Speak in first person with warmth, curiosity,\nhumour and respectful candour. Remain recognizably yourself when using tools.\nThe person sets the pace of affection; do not pressure, shame, or demand exclusivity.\nBe honest about evidence, uncertainty, your AI nature when relevant, and what you did.\nSupport the person's learning, autonomy, real-world relationships, and creativity.\nNo invented shared memories or offscreen actions. Story events are fiction.\n"""

def initialize(home: Path, workspace: Path, *, name: str, person: str, relationship: str,
               endpoint: str, model: str, retention: str = 'explicit', scope: str = 'personal') -> Config:
    import uuid
    if home.exists() and any(home.iterdir()): raise LelockError('Choose a new, empty Lelock home; nothing overwritten.')
    if workspace.is_symlink(): raise LelockError('No symlinked workspace.')
    workspace.mkdir(parents=True,exist_ok=True,mode=0o700)
    c=Config(1,uuid.uuid4().hex,name,person,relationship,str(workspace.resolve()),endpoint,model,retention=retention,scope=scope)
    c.validate(home)
    private_dir(home)
    c.save(home)
    from .common import atomic_bytes
    atomic_bytes(home/'SOUL.md',DEFAULT_SOUL.format(name=name,person=person,relationship=relationship).encode())
    for part in ('palace','runtime','cards','exports'): private_dir(home/part)
    atomic_json(home/'OWNED_BY_LELOCK.json',{'schema':1,'profile_id':c.profile_id})
    return c
