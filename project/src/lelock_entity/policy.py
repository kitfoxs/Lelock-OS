"""Approval policy is not authentication, a sandbox, or a grant of new capabilities."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import threading
import time
import uuid
from .common import EntityError

class Mode(str, Enum):
    SAFE = "safe"
    TRUSTED = "trusted"
    YOLO = "yolo"

class Risk(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    EXTERNAL = "external"

@dataclass(frozen=True)
class Session:
    entity: str
    scope: str
    capabilities: frozenset[str]
    mode: Mode = Mode.SAFE
    auto_approve: frozenset[str] = frozenset()
    expires_at: float = field(default_factory=lambda: time.time() + 7200)
    ident: str = field(default_factory=lambda: uuid.uuid4().hex)
    parent: str | None = None
    depth: int = 0

    def __post_init__(self):
        object.__setattr__(self, "mode", Mode(self.mode))
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        object.__setattr__(self, "auto_approve", frozenset(self.auto_approve))
        if self.scope not in {"personal", "work", "fiction", "test"}:
            raise EntityError("Invalid session scope")
        if not self.auto_approve <= self.capabilities:
            raise EntityError("Auto-approval cannot grant a capability")

    def decision(self, capability: str, risk: Risk, now: float | None = None) -> str:
        now = time.time() if now is None else now
        if now >= self.expires_at:
            raise EntityError("Session expired; operator must open a new session")
        if capability not in self.capabilities:
            raise EntityError("Capability was not enabled by the operator")
        if risk == Risk.READ or self.mode == Mode.YOLO:
            return "execute"
        if self.mode == Mode.TRUSTED and capability in self.auto_approve:
            return "execute"
        return "propose"

    def child(self, capabilities: set[str], *, max_depth: int = 2) -> Session:
        if self.depth >= max_depth or not set(capabilities) <= self.capabilities:
            raise EntityError("Child depth/capability escalation refused")
        return Session(self.entity, self.scope, frozenset(capabilities), self.mode,
                       self.auto_approve & set(capabilities), self.expires_at,
                       parent=self.ident, depth=self.depth + 1)

class StopSignal:
    def __init__(self):
        self.event = threading.Event()
    def stop(self):
        self.event.set()
    def check(self):
        if self.event.is_set():
            raise EntityError("Session stopped by operator")

@dataclass
class Budget:
    """Shared by parent and children. Actual money/token billing is a separate live gate."""
    max_actions: int = 200
    max_output_bytes: int = 4_000_000
    seconds: float = 7200
    actions: int = 0
    output_bytes: int = 0
    started: float = field(default_factory=time.monotonic)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def reserve_action(self):
        with self._lock:
            if time.monotonic() - self.started >= self.seconds or self.actions >= self.max_actions:
                raise EntityError("Session action/time budget exhausted")
            self.actions += 1

    def record_output(self, count: int):
        with self._lock:
            self.output_bytes += count
            if self.output_bytes > self.max_output_bytes:
                raise EntityError("Session output budget exhausted; effect may already have occurred")
