# Memory, identity, and continuity
**Upgrade contract • implements foundations, not an autonomous memory agent**

## One authority, several views

MemPalace remains the semantic memory authority. Keep the existing exact record envelopes, correction chains, source labels, read-back acknowledgment and isolated managed process. `SOUL.md` remains the initial identity authority. The operational SQLite database records proposals, receipts, schedules and world revisions; it is not a replacement search engine for the person's life.

The new `LegacyMemory` adapter calls the real existing Service. Its commit path is reached only through an authorized Entity tool invocation. It does not write to a mock Palace, silently discover another Palace, or invent successful storage during an outage. Actual model/Palace integration remains a live gate. [L3–L5]

Do not seed a new public companion with private Ada history. A public card is a reusable template; the private identity, its evolution and relationship memories are a separate installation. The public package includes generic demonstration text only.

## Evidence and derived memory

Keep these concepts distinct:

| Layer | Meaning | Authority |
|---|---|---|
| Original evidence | Exact source record or consented transcript | Source text, not automatically a true assertion |
| Candidate | A proposed extraction or correction | Unreviewed |
| Reflex | Small derived working cue | Derived and revocable |
| Heuristic | An inferred preference or useful pattern | Inference, not certainty |
| Narrative | A period summary or project recap | Lossy view linked to sources |
| Canon | A reviewed, scoped assertion | Accepted record with provenance and correction history |

`memory.py` implements `EvidenceRef`, `DerivedMemory`, `derive`, `revalidate`, and `canon_proposal`. It checks source identity, scope, activity, content hashes and visibility. It **does not prove the semantic truth of a generated summary**. A model can produce an inaccurate summary of authentic sources; human review or a separately evaluated verification step is still necessary.

The visibility of a derived item is the intersection of the visibility of all its sources. Combining a public note and a private letter does not produce a public summary. Revalidation fails if a source changes, is superseded, becomes inactive, or loses access. Legacy records without an ACL are treated as private to the owning adapter/requester, not globally visible. A future multi-user transport must bind that requester to authenticated identity; never accept an arbitrary caller-supplied identity.

### Runnable library example

```python
from lelock_entity.memory import derive, revalidate, canon_proposal

# palace_adapter implements fetch(record_id) using the actual owned Palace.
summary = derive(
    palace_adapter,
    [first_record_id, second_record_id],
    summary_text,
    scope="personal",
    requester=owner_id,
    tier="narrative",
    period="2026-W38",
)
revalidate(summary, palace_adapter, requester=owner_id)
proposal = canon_proposal(summary, palace_adapter, requester=owner_id)
# proposal['status'] is requires_review. This has NOT saved a memory.
```

Variable names in this example are application inputs, not bundled credentials or invented live data. The functions themselves are implemented and covered by synthetic evidence tests.

## Consolidation pipeline to build

After a completed turn, optionally queue candidate extraction. Do not interrupt the main conversation to run five hidden full-model calls. Retain source IDs, source hashes, scope, extractor/model version, period and explicit status on every result. A daily summary may feed a weekly narrative, but the weekly narrative must retain resolvable links to the original evidence, not only to the daily prose.

The intended flow is:

```text
consented source → extracted candidate → source/ACL validation
                → conflict check → policy-controlled review/commit
                → derived search view → retrieval with provenance
```

Start with deterministic overlap and explicit supersession checks. Do not claim a general contradiction detector merely because string comparisons exist. More ambitious semantic conflict detection needs its own evaluation set: changed preferences, dates, negation, hypothetical statements, sarcasm, fictional events and uncertainty.

A correction is a new record that supersedes a prior assertion. It is not deletion of the historical conversation. Downstream summaries referencing the old source become stale. Rebuild or exclude them from ordinary recall until revalidated.

## Retention and YOLO are different settings

Preserve the original `explicit`, `journal`, and `temporary` meanings. YOLO changes approval behavior for enabled actions, not transcript retention. Enabling YOLO must not silently turn on full chat archiving, passive audio recording or profile mining.

For a deliberately YOLO session with `memory.write`, a requested memory commit can execute without a second prompt. Its receipt says `policy:yolo`, not `human reviewed this sentence`. Autogenerated extraction should remain a candidate unless the operator has separately enabled a policy allowing canonical promotion. This distinction prevents a no-prompt coding session from rewriting identity or life history behind the scenes.

Temporary sessions must not attach the real private Palace. The included `demo` uses disposable directories and no Palace. The live `chat` and `serve` commands require an explicitly selected existing owned profile; they are not temporary-mode implementations.

## Identity evolution

`identity.py` implements an exact-hash identity update with a private history copy. The update is a file effect, not a capability grant. The active model prompt should be reloaded only at an explicit turn boundary or runtime restart, never partway through an action. Register identity editing as its own capability only after the existing runtime's reload behavior is tested; it is **not exposed by default** in this packet.

Persist a stable profile/entity ID separately from display names. Names, voices, avatars and interfaces may change without changing ownership of the underlying records. Do not change a profile ID just because an API provider changes. Do not promise behavioral equivalence across models; instead run continuity checks against the same selected identity and evidence.

## Schema and migration strategy

The existing `lelock.record/1` validates an exact set of keys. Do not add `visible_to`, `tier` or arbitrary metadata to it and expect old Service code to accept it. Introduce a versioned derived-record envelope and a migration adapter, then update validation, retrieval, export, correction and tests together. Before that migration, the included derived objects are library-level results, not silently stored canon.

Choose a single writer during migration. Export a synthetic fixture, stop the owned runtime, back up the whole owned home through the person's approved backup process, migrate a copy, validate record counts and hashes, and prove restart. Never run legacy and new processes against one home simultaneously merely because both use SQLite.

The source of each imported record must be visible. Private research artifacts, third-party lore, user assertions and model inferences must not all become `person-explicit`. The supplied patch prevents fictional companion lore from automatically becoming personal facts and supplies the correct scope for fictional imports. This deliberately narrows the old import path; it does not delete the companion catalog.

## Portability and recovery

The existing datachip is a **selected plaintext export**, not encryption and not a full disaster-recovery image. It omits credentials, operational receipts, workspace files and some history. Preserve that description. Add a versioned manifest before extending it with world snapshots, derived records or identity revisions.

A future encrypted archive should use a reviewed standard encryption implementation and separate key recovery, not a bespoke cipher or a SHA digest labeled encryption. Full recovery needs the owned home, compatible runtime/dependency versions, non-secret setup information and separate credential recovery. No automatic external upload is part of this packet.

## Acceptance

Verify real add/read-back, search/full fetch, correction, outage and restart against MemPalace. Add tests for inherited visibility, revoked access, stale narratives, scope separation, fictional versus real records, export exclusions, identity reload boundaries and no false save acknowledgment. Review companion experience with Kit: warmth and continuity matter, but a plausible recollection is not a passing factual test.
