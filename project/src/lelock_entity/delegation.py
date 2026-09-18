"""Child-task envelope and capability attenuation. Executor adapters remain trusted code."""
from __future__ import annotations
from dataclasses import dataclass
import time
import uuid
from .common import EntityError, canonical, digest, text
from .core import EntityCore
from .policy import Session

@dataclass(frozen=True)
class ChildTask:
    ident: str
    parent_session: str
    session: Session
    prompt: str
    deadline: float

class Delegator:
    def __init__(self, core: EntityCore):
        self.core = core

    def run(self, prompt: str, capabilities: set[str], executor, *, parent: Session | None = None,
            seconds: float = 120) -> dict:
        """executor(task, call_tool) must use a separate supported runtime process for real Hermes children.

        This synchronous interface does not preempt arbitrary Python callbacks. Production runtime
        adapters must enforce task.deadline, cancellation and model token reservations themselves.
        """
        self.core.stop.check()
        parent = parent or self.core.session
        parent.decision("delegate.run", self._risk())
        text(prompt, 20_000)
        if not 0 < seconds <= 600:
            raise EntityError("Child deadline exceeds configured bound")
        child = self.core.register_child(parent, capabilities)
        task = ChildTask(uuid.uuid4().hex, parent.ident, child, prompt, min(time.time() + seconds, child.expires_at))
        self.core.store.event("child.started", {"task_id": task.ident, "parent": parent.ident, "session": child.ident,
                                               "capabilities": sorted(capabilities)})
        def call_tool(name: str, arguments: dict, request_id: str | None = None):
            if time.time() >= task.deadline:
                raise EntityError("Child task expired")
            return self.core.invoke(name, arguments, request_id=request_id, session=child)
        try:
            self.core.budget.reserve_action()
            result = executor(task, call_tool)
            if time.time() >= task.deadline:
                raise EntityError("Child returned after deadline")
            if len(canonical(result).encode()) > 200_000:
                raise EntityError("Child result too large")
            self.core.store.event("child.completed", {"task_id": task.ident, "result_sha256": digest(result)})
            return {"task_id": task.ident, "result": result, "authority": "untrusted_task_result",
                    "promoted_to_memory": False}
        finally:
            # Child authority is not left available after task completion or exception.
            self.core.sessions.pop(child.ident, None)

    @staticmethod
    def _risk():
        from .policy import Risk
        return Risk.READ  # Tool exposure/approval of delegation itself belongs to the parent registry.
