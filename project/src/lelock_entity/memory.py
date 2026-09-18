"""Evidence-backed derived memory. MemPalace remains the authority; summaries aren't facts."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Protocol
from .common import EntityError, digest, text

class EvidenceSource(Protocol):
    def fetch(self, ident: str) -> dict: ...

@dataclass(frozen=True)
class EvidenceRef:
    record_id: str
    sha256: str

@dataclass(frozen=True)
class DerivedMemory:
    schema: str
    text: str
    tier: str
    scope: str
    source_refs: tuple[EvidenceRef, ...]
    visible_to: frozenset[str]
    status: str = "candidate"
    period: str = ""
    conflicts_with: tuple[str, ...] = ()

    def export(self) -> dict:
        result = asdict(self)
        result["visible_to"] = sorted(self.visible_to)
        return result


def derive(source: EvidenceSource, ids: list[str], summary: str, *, scope: str,
           requester: str, tier: str = "heuristic", period: str = "") -> DerivedMemory:
    """Checks provenance/scope/visibility, NOT semantic truth of an LLM-generated summary."""
    if tier not in {"reflex", "heuristic", "narrative"} or not 1 <= len(ids) <= 100:
        raise EntityError("Invalid derived memory tier/source count")
    text(summary, 64_000)
    refs = []
    allowed = None
    for ident in dict.fromkeys(ids):
        record = source.fetch(ident)
        if record.get("id") != ident or record.get("scope") != scope or not record.get("active", True):
            raise EntityError("Missing, inactive or wrong-scope evidence")
        # Missing ACL does not mean public. Older records are visible only to the owning requester.
        visibility = set(record.get("visible_to", [requester]))
        if requester not in visibility:
            raise EntityError("Evidence not visible to requester")
        allowed = visibility if allowed is None else allowed & visibility
        refs.append(EvidenceRef(ident, digest(record)))
    return DerivedMemory("lelock.derived-memory/1", summary, tier, scope, tuple(refs),
                         frozenset(allowed), period=period)


def revalidate(memory: DerivedMemory, source: EvidenceSource, *, requester: str) -> None:
    if requester not in memory.visible_to:
        raise EntityError("Derived memory not visible to requester")
    for ref in memory.source_refs:
        record = source.fetch(ref.record_id)
        if not record.get("active", True) or record.get("scope") != memory.scope or digest(record) != ref.sha256:
            raise EntityError("Source changed or was superseded; rebuild derived memory")
        if requester not in set(record.get("visible_to", [requester])):
            raise EntityError("Source access revoked")


def canon_proposal(memory: DerivedMemory, source: EvidenceSource, *, requester: str) -> dict:
    revalidate(memory, source, requester=requester)
    if memory.conflicts_with:
        raise EntityError("Resolve conflicts before proposing canonical memory")
    return {"status": "requires_review", "kind": "canonical_memory_candidate", "derived": memory.export(),
            "warning": "Provenance validation is not factual verification. Commit only through EntityCore policy."}
