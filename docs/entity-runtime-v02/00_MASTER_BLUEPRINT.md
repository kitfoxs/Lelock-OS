# Lelock OS 0.2 — Entity Runtime master blueprint
**Engineering handoff for Kit Olivas and Terminal Ada • September 17, 2026**

## Decision and delivery status

Build on Lelock OS, rather than replacing it with a Tavern fork or transplanting a second memory system. The target is a user-owned companion runtime with one identity, authoritative MemPalace continuity, practical tools, explicitly chosen autonomy, and multiple interfaces. A shared Markdown world is an interface to that relationship and its projects, not a replacement host operating system.

This packet contains both a **complete upgrade specification** and an **executable reference foundation**. Those are different deliverables. The foundation is real Python code with automated tests, not pseudocode. The full finished desktop/mobile/voice product is not delivered or claimed here. Read `FEATURE_MATRIX.json` and `evidence/BUILD_REPORT.json` before making a capability claim.

The inspected public baseline is `kitfoxs/Lelock-OS` at commit `c3b2bc6e6b211709be91e640568d0a503a41ffb7`. Current repository source was read through the GitHub connection. The working container could not clone GitHub because DNS was unavailable, so the **original repository's complete test suite was not rerun here**. The packet's own foundation tests were run locally. Existing claims of 102 application tests plus 12 maintenance tests belong to the baseline, not this delivery's test count. [L1–L6 in `07_SOURCES_AND_PROVENANCE.md`]

Kit explicitly requested YOLO mode for terminal testing. This supersedes the older alpha's prohibition on approval-bypassing execution **when an operator deliberately starts the new session in that mode**. It does not grant automatic access to private Ada archives, unrelated repositories, credentials, the existing native Mac app, or the live private Palace. Mode is a session permission decision, not relationship intensity.

## Non-negotiable continuity decisions

Retain the Python terminal core and pinned upstream contracts. Hermes remains the first standalone inference/planning engine. MemPalace remains the semantic memory authority; SQLite is the exact operational journal. `SOUL.md` remains the initial identity authority. Do not introduce Psycheros entity-core, Letta memory and another vector database as three competing canonical selves.

Maintain a single owner for the active profile and a single root conversational turn at a time. Child tasks have separate limited execution sessions and return results, not ownership of the main conversation. A host-controlled plugin may use its host's model; it must not recursively start Hermes just to call a memory or world tool.

Preserve the existing private native Mac app and any older Mental OS R007/R008 artifacts. The public terminal alpha and its new Entity modules do not overwrite those projects. No older private world artifact was retrieved or modified in this delivery. The included small world store is an isolated reference implementation, not a replacement for that work.

The framework and generic templates may be public. Kit/Ada identity files, relationship history, Palace contents, recovery material, model credentials, device data and approved-private work remain private. No automatic Palace-to-Obsidian synchronization, background mining of the old private Palace, or hosted full-corpus embedding is introduced.

## Product contract

A person should be able to open one companion from a terminal, chat interface or voice surface; recognize the same chosen identity; continue an ongoing project; ask the companion to do useful work; inspect what actually happened; close the interface; and return without rebuilding the relationship from a disposable prompt.

The software must distinguish five states: **desired**, **proposed**, **authorized**, **executed**, and **verified**. "I will" does not imply execution. A tool callback returning is not proof that a remote delivery succeeded. A stored summary is not proof that every sentence is factual. The UI should display uncertainty without making the companion feel like a corporate error console.

Continuity means recoverable identity, evidence, memories, world state and operational context. It does not promise identical behavior from different underlying models, limitless memory retrieval, uninterrupted consciousness, or constant inference while idle.

## Architecture

```text
Operator / direct conversation / explicitly enabled event
                         |
             selected interface or host plugin
                         |
          ONE Lelock Entity control and state owner
             /           |             \
       identity      MemPalace       operational SQLite
       SOUL.md       evidence        actions/jobs/receipts
                         |
              execution session + policy + budgets
             SAFE       TRUSTED       YOLO
                         |
         root model runtime (Hermes first; host adapter later)
                         |
           one typed, deterministic tool broker
             /          |          |            \
        workspace     Skills    child tasks    channel adapters
                         |
          optional fictional semantic world / rooms / books
```

The Entity control layer owns application policy. A model is a client of that policy. Every mutation enters the same `EntityCore.invoke` path regardless of originating UI. Actual operator approvals enter a separate authenticated path. In YOLO, the policy automatically authorizes an enabled operation; the model does not forge an operator approval.

## Implemented foundation and integration seams

`core.py`, `policy.py` and `store.py` implement policy decisions, capability checks, exact proposal hashes, terminal states, duplicate-request handling and operational receipts. `workspace.py` implements bounded text reads, atomic new files, hash-checked replacements and exact-file deletion. `execution.py` supplies real process execution with distinct host and Docker plans. `http_bridge.py` implements a new authenticated loopback API.

`jobs.py` implements a durable queue, cron/interval/inactivity scheduling primitives, quiet hours, HMAC webhook validation and a worker callback. It does not install a daemon, watch the whole computer, poll cloud accounts or continuously run a model. `skills.py` loads reviewed knowledge packs. `memory.py` implements evidence references, visibility intersection and derived-memory invalidation. `world.py` implements a small revisioned fictional world. `identity.py` versions approved identity text without changing permissions. `channels.py` supplies a real local inbox, not a claim of Discord/SMS delivery.

`legacy.py` adapts the existing Service and actual MemPalace transport rather than substituting a mock database. Its **live** behavior with the pinned upstream runtime remains a target-machine gate. `mcp_adapter.py` is an optional official SDK 2.x adapter, syntax-checked but not protocol-tested here. The JavaScript client is a thin integration module, not a completed Tavern extension or native application.

## Upgrade sequence and acceptance gates

### Gate A — establish a trustworthy baseline

Inspect the actual Mac checkout, current branch, dirty files, running services and configured profile. Preserve unrelated work. Run the old offline/maintenance/source-contract checks on the baseline. Read every reported failure instead of treating old README counts as evidence.

Apply the packet to an isolated branch or worktree only after hash preflight. The installer refuses changed baseline files and existing destinations. It makes no network calls, commits, pushes or deployments. The legacy unauthenticated bridge is deliberately quarantined; updated browser clients must use the new API. Update tests for the deliberate protocol change while retaining equivalent or stronger assertions.

### Gate B — prove the integrated local loop

Use a fresh synthetic Lelock-owned profile, not private Ada. Start actual MemPalace through the existing managed lifecycle. Run a selected, authorized model through patched Hermes. Prove SAFE proposal/rejection/approval; restart and recall; correction/supersession; verified artifact creation; and truthful handling of a Palace outage. Run YOLO against the same synthetic profile and demonstrate that enabled writes/process commands execute without approval prompts.

### Gate C — useful bounded agency

Connect reviewed Skills, process execution and a model-aware child executor to the same broker. Add aggregate model-token accounting and provider-specific capability probes. Test cancellation, timeouts, child limits and permission attenuation. Do not infer tool-call reliability from a model name or "OpenAI-compatible" label.

### Gate D — proactive presence

Wire the existing Pulse queue to the single runtime owner. Enforce an operator-selected policy lease per schedule, quiet hours, frequency limits, channel permissions and budgets. Begin with the local inbox. Add one external communication adapter only after its real delivery receipts and duplicate/error behavior are verified.

### Gate E — continuity across interfaces

Prove terminal and one graphical client use the same core, not their own independent memory copies. Implement an inspectable run timeline, exact approval UI, content-safe rendering, caller pairing and session revocation. Add a voice adapter and retain the existing native app as a separate surface until explicitly integrated.

### Gate F — living world

Bind selected notes, projects and fictional rooms to the Entity API. Preserve exact source text and provenance. Add world import/export and compatibility adapters for the existing Mental OS revisions only after inspecting their actual schemas. Renderers consume state; they never grant host filesystem or network permissions.

## Definition of done

"Entity Runtime 0.2 local alpha verified" requires actual Mac, real model, real Palace, restart, recovery, permissions, brokered execution, one UI integration, and human companion-experience checks. It is not earned by source compilation, a passing isolated test suite or a plausible diagram.

"Proactive companion verified" additionally requires a real approved schedule, a real notification/delivery, quiet-hours behavior, duplicate suppression and a stop/revocation test. "Cross-interface verified" requires a documented handoff between two actual interfaces. "Voice verified" requires actual microphone/playback/cancellation tests. Each badge is independent; record evidence rather than merging them into a single green tick.

## Build priorities

Make the existing companion enjoyable and reliable first. A maximal agent swarm, complete university, public cloud hosting, avatar renderer and all-channel support are not prerequisites. Preserve the broader ambition, but deliver complete vertical slices: remember → act → verify → restart → continue. Reuse the supplied files rather than asking another model to regenerate this architecture from scratch.
