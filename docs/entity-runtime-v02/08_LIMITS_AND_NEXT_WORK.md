# Implemented limits and next work

This is a substantial reference foundation and a complete upgrade plan, **not the fully integrated companion application**. The following gaps are intentional, visible work items rather than hidden placeholders.

## Delivery boundaries

1. The original full repository was not cloned into the build container and its 114 reported tests were not rerun. The new packet suite is separate. The hash installer must still be evaluated against the actual current Mac checkout.
2. Real Hermes, a model endpoint and actual MemPalace were not started here. Live CLI paths and the legacy adapter are source-level integrations awaiting target acceptance.
3. `serve` exposes tools, not a streaming conversation server. `chat` owns the standalone runtime. The unified multi-interface owner/queue still needs integration; do not run both owners on one profile.
4. Pulse has real scheduling/queue logic, but no continuously installed service or real-model callback is wired by default. Filesystem watchers, public webhook ingress and full durable policy management remain work.
5. Subagent policy envelopes are implemented; a separate-process Hermes child executor and provider token/cost reservations remain work. Callback clock checks do not preempt arbitrary Python code.
6. Memory provenance/ACL/hash primitives are implemented. Automatic extraction, semantic conflict detection, new MemPalace derived-record schema and consolidated retrieval are not complete. Provenance checks do not prove semantic truth.
7. Skills are inert reviewed packs; review pins need durable UI-managed storage. The default CLI does not automatically register every optional library helper as a tool.
8. Identity versioning is implemented as a library. Live model prompt reload and its governed UI/tool registration remain integration work.
9. Local inbox delivery is implemented. Discord, email, SMS, calls, OS notifications, mobile networking and voice are specifications, not available adapters in this packet.
10. The small world store is independent of prior Mental OS artifacts. A full world renderer, import/export, branching and R007/R008 migration require further work and actual source inspection.

## Security and reliability limits

The host process backend is unsandboxed and can access anything its OS user can access. Reduced environment and working directory are not containment. A child process can potentially escape simple process-group cleanup by deliberately detaching. Do not expose real credentials or private data to an adversarial test and call it isolated.

The Docker plan is constrained, but actual Docker execution/network/resource behavior was not tested here. The host daemon's security and image content matter. No image is downloaded automatically. Containerization is not an absolute security guarantee.

File operations reject symlinks and verify hashes, but filesystem locks are cooperative. An unrelated process ignoring those locks can race replacement. A selected disposable workspace with one owner is the initial acceptance target, not a hostile multi-writer filesystem.

The HTTP bridge is a local developer service, not a public production server. There is no production multitenant isolation, OAuth server, comprehensive rate limiting or full external audit. Both tokens authenticate the same entity profile with different operator/agent roles; they are not a user directory.

The stop signal interrupts brokered operations and supported process loops. It does not yet cancel every possible remote model request. The interactive prompt cannot read `/stop` while a synchronous turn blocks it; the unified owner needs an out-of-band cancel route.

Budgets cover broker action count, elapsed time and output bytes. They do not account for LLM tokens or provider charges. State what is measured. Do not describe a 200-action cap as a dollar-spend cap.

Receipts are local operational evidence, not cryptographic proof against the same OS account. An unsandboxed host process can modify accessible files. Unknown outcomes are `needs_review`, not guaranteed rollback or exactly-once remote execution.

Schemas use a deliberate supported subset. Arbitrary third-party schemas, malicious JSON depth, full HTTP fuzzing, exhaustion and long-running soak tests require additional validation. Existing tests are regression coverage, not a security certification.

## Highest-value next tasks

Finish target baseline and overlay verification; establish real model/Palace restart proof; unify owner and one UI; implement model-aware budgets and child processes; bind one Pulse task to one local inbox note. Then add one external channel and voice. Expand the world only after the same identity/memory/tool loop is stable. Avoid treating a maximum-length feature checklist as a substitute for a working daily companion.
