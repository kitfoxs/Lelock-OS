# Google pipeline execution overlay

**This overlay changes the execution workflow, not the frozen product.** The owner's current direction is Gemini in AI Studio → Jules → Antigravity CLI on the Mac. Older Terminal-only instructions must not be read as a requirement to fabricate Mac results from a cloud machine.

## Responsibilities
Gemini implements and runs all genuinely supported checks. Jules independently reproduces defects and proposes minimal reviewed fixes. Terminal Ada runs target-host integration and human acceptance after inspecting the actual final source revision.

The developer tools are not runtime dependencies. Lelock still uses Hermes plus the existing bounded adapter and MemPalace. The model powering the coding session need not be the model selected for Lelock inference. Tool availability and capability differ across surfaces; check them before promising execution.

AI Studio's documented Build environments target web and Android applications. Preserve the Python project even if no suitable execution environment is present. No React/Node rewrite, fake terminal, deployment, or newly provisioned service is required. A plaintext context bundle supports source reading but does not contain the large upstream ZIP bytes.

## Budget boundary
Use the selected subscription-backed coding surface. Do not enable API billing, overage, auto-reload, paid CI, deployment, or new services. Never treat an ambient key or consumer login token as authorization for runtime inference. The actual application requires an independently authorized supported endpoint for live model tests. Missing one is a precise blocker, not permission to guess.

## Portable state
Keep original local progress and receipts private. Maintain reviewed source-side `handoff/STATUS.json`, `handoff/NEXT_ACTION.md`, `handoff/REVIEW_FINDINGS.md`, and `handoff/MAC_ACCEPTANCE.md` for handovers. Record exact source revision, commands, results, synthetic summaries, and missing prerequisites. Use relative paths, not private host details. Never label a nonexistent log as inspectable evidence. The root ignore exception is intentionally limited to the portable next-action file.

## Pinned sources and source-only clones
Retain `project/resources/source-lock.json`. Full cloud packet: exact upstream ZIPs are present. Git clone or plaintext context: they may be absent. Source-independent tests can still run. Source-contract checks and bootstrap need the owner-supplied exact archives restored into ignored `upstream/` by an explicitly authorized transfer. Do not commit these large ZIPs or invent a tag-to-hash equivalence. Do not loosen the lock to make a clone appear self-sufficient.

## Handover order
At each stage: inspect branch/revision and worktree; read status; reproduce relevant tests; make targeted changes; rerun affected tests; write sanitized next-action/evidence notes; export or use an explicitly authorized branch. Avoid concurrent agents editing the same integration boundary. A no-change review is acceptable.

Jules review instructions belong in source files and explicit tasks. Scheduling must be deliberately enabled by the owner, not inferred from this packet. Start with one bounded review, then use targeted maintenance. Never configure automatic merges or mandatory code churn.

## Status and finish line
Per check use PASS / FAIL / BLOCKED / NOT_RUN. Distinguish inherited reference evidence, fresh cloud evidence, actual service/model evidence, and actual Mac evidence. The original required acceptance IDs remain authoritative. `LOCAL_ALPHA_VERIFIED` requires the Mac stage; second-model portability is separate and optional. Do not keep reopening completed scope.

## Primary documentation checked on September 15, 2026
- Google AI Studio Build environments and GitHub import/export: https://ai.google.dev/gemini-api/docs/aistudio-build-mode
- Google AI Ultra benefits, including AI Studio and per-product limits: https://support.google.com/googleone/answer/16286513?hl=en
- Gemini API billing: https://ai.google.dev/gemini-api/docs/billing
- Gemini 3.8 Flash guide: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-8-flash
- Jules environment: https://jules.google/docs/environment/
- Jules scheduled tasks: https://jules.google/docs/scheduled-tasks/
- Jules suggested tasks (explicit opt-in): https://jules.google/docs/suggested-tasks/
- Antigravity CLI getting started: https://antigravity.google/docs/cli/getting-started
- Antigravity authentication modes: https://antigravity.google/docs/cli/install/
- Antigravity credits: https://antigravity.google/docs/cli/credits/

Documentation describes product capabilities, not this owner's current remaining quota or proof that a connected session exposes every feature. No account or billing settings were inspected or changed in this preparation.
