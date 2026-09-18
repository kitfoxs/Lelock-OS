"""One authorization/receipt path for CLI, web, MCP, scheduled and delegated tool calls."""
from __future__ import annotations
from dataclasses import dataclass
import json
import threading
import uuid
from typing import Callable
from .common import EntityError, canonical, digest, text, validate
from .policy import Session, Risk, StopSignal, Budget
from .store import Store

@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    capability: str
    risk: Risk
    schema: dict
    handler: Callable[[dict, Session], dict]
    version: str = "1"

    def manifest(self) -> dict:
        return {"name": self.name, "description": self.description, "capability": self.capability,
                "risk": self.risk.value, "schema": self.schema, "version": self.version}

class EntityCore:
    def __init__(self, store: Store, session: Session, *, budget: Budget | None = None,
                 stop: StopSignal | None = None):
        self.store = store
        self.session = session
        self.budget = budget or Budget()
        self.stop = stop or StopSignal()
        self.tools: dict[str, Tool] = {}
        self.sessions = {session.ident: session}
        self._lock = threading.RLock()

    def register(self, tool: Tool):
        if tool.name in self.tools:
            raise EntityError("Duplicate tool registration")
        self.tools[tool.name] = tool

    def register_child(self, parent: Session, capabilities: set[str]) -> Session:
        if self.sessions.get(parent.ident) is not parent:
            raise EntityError("Unregistered parent session")
        child = parent.child(capabilities)
        self.sessions[child.ident] = child
        return child

    def _session(self, session: Session | None) -> Session:
        actor = session or self.session
        if self.sessions.get(actor.ident) is not actor:
            raise EntityError("Unregistered session object")
        return actor

    def schemas(self, session: Session | None = None) -> list[dict]:
        actor = self._session(session)
        return [{"name": t.name, "description": t.description, "parameters": t.schema}
                for t in self.tools.values() if t.capability in actor.capabilities]

    def invoke(self, name: str, arguments: dict, *, request_id: str | None = None,
               session: Session | None = None) -> dict:
        with self._lock:
            self.stop.check()
            actor = self._session(session)
            tool = self.tools.get(name)
            if tool is None:
                raise EntityError("Tool is not registered")
            validate(tool.schema, arguments)
            # Copy after validation: caller cannot mutate approval content behind our back.
            arguments = json.loads(canonical(arguments))
            decision = actor.decision(tool.capability, tool.risk)
            if tool.risk == Risk.READ:
                self.budget.reserve_action()
                result = tool.handler(arguments, actor)
                self.budget.record_output(len(canonical(result).encode()))
                self.store.event("tool.read", {"tool": name, "session": actor.ident,
                                               "result_sha256": digest(result)})
                return {"status": "done", "result": result}
            rid = text(request_id or uuid.uuid4().hex, 150)
            payload = {"arguments": arguments, "manifest_sha256": digest(tool.manifest())}
            row = self.store.propose(entity=actor.entity, session=actor.ident, tool=name, payload=payload,
                    request_key=actor.entity + ":" + actor.ident + ":" + rid, expires=actor.expires_at)
            if row["state"] != "pending":
                return {"status": row["state"], "action_id": row["id"], "replayed": True}
            if decision == "propose":
                return {"status": "pending_approval", "action_id": row["id"],
                        "digest": row["digest"], "tool": name, "arguments": arguments}
            return self._execute(row, actor, approved_by="policy:" + actor.mode.value)

    def approve(self, action_id: str, expected_digest: str) -> dict:
        """OPERATOR API. This method is never exposed as a model tool or agent-token route."""
        with self._lock:
            row = self.store.get(action_id)
            actor = self.sessions.get(row["session"])
            if actor is None:
                raise EntityError("Old session approval refused; inspect/re-propose deliberately")
            if row["digest"] != expected_digest:
                raise EntityError("Approval digest does not match reviewed content")
            return self._execute(row, actor, approved_by="operator")

    def _execute(self, row: dict, actor: Session, approved_by: str) -> dict:
        self.stop.check()
        if row["state"] != "pending":
            raise EntityError("Action is no longer pending")
        tool = self.tools.get(row["tool"])
        if tool is None:
            raise EntityError("Tool no longer registered")
        actor.decision(tool.capability, tool.risk)  # Recheck permissions and expiry at commit.
        payload = json.loads(row["payload"])
        if payload["manifest_sha256"] != digest(tool.manifest()):
            raise EntityError("Tool contract changed; re-propose for new review")
        validate(tool.schema, payload["arguments"])
        self.budget.reserve_action()
        self.store.claim(row["id"], row["digest"], actor.entity, actor.ident)
        try:
            self.stop.check()
            result = tool.handler(payload["arguments"], actor)
            self.budget.record_output(len(canonical(result).encode()))
            metadata = {"tool": tool.name, "approved_by": approved_by, "result_sha256": digest(result)}
            self.store.finish(row["id"], "done", metadata)
            return {"status": "done", "action_id": row["id"], "result": result}
        except BaseException as exc:
            # A timeout/crash/failed readback might occur AFTER an effect. Never auto-replay.
            self.store.finish(row["id"], "needs_review", {"tool": tool.name, "error_type": type(exc).__name__})
            raise

    def reject(self, action_id: str):
        row = self.store.get(action_id)
        if row["session"] not in self.sessions or row["entity"] != self.session.entity:
            raise EntityError("Action belongs to another session")
        self.store.reject(action_id, row["entity"], row["session"])
        return {"status": "rejected", "action_id": action_id}

    def status(self, session: Session | None = None):
        actor = self._session(session)
        return {"entity": actor.entity, "scope": actor.scope,
                "mode": actor.mode.value, "expires_at": actor.expires_at,
                "capabilities": sorted(actor.capabilities), "stopped": self.stop.event.is_set(),
                "actions_used": self.budget.actions, "output_bytes": self.budget.output_bytes}
