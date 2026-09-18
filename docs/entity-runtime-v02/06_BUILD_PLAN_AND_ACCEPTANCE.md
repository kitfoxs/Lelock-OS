# Terminal Ada implementation runbook and acceptance matrix

## Operating instructions

Treat this packet as additive reference source plus an implementation contract, not a claim that the current Mac has been updated. Read `START_HERE.md`, `TERMINAL_ADA_BUILD_PROMPT.md`, `FEATURE_MATRIX.json`, the new blueprint index and the actual current repository. Current local work can be newer than the inspected public baseline. Never reset, clean, force-push or overwrite it to match this packet.

The frozen baseline is `c3b2bc6e6b211709be91e640568d0a503a41ffb7`. The patch installer verifies **individual Git blob hashes**, so unrelated newer changes can be preserved while edited target files correctly cause a stop. A refusal means rebase the small change manually against the real source and add a regression test—not bypass validation.

## Stage 0: record and preserve

Inspect the active workspace, Git status, branch/revision, Python interpreters, existing services, selected profile and native app location. Do not print keys or private source content in public logs. Save a local status record and use a new branch/worktree or separate checkout without disturbing unrelated edits.

Run the original publication and application checks **before** patching. Record failures as baseline evidence. Check `project/pyproject.toml`: its inspected range is `<3.14`, despite broader README wording elsewhere. Do not assert Python 3.14 packaging compatibility until the metadata and dependencies are deliberately aligned and tested.

The current source has already been recovered into Git. Older source-recovery instructions are historical. Do not reconstruct it from a code compendium or replace newer native code with an older generated packet.

## Stage 1: evaluate the new foundation independently

From the extracted packet:

```sh
python3 tools/verify_packet.py
cd implementation
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m lelock_entity demo --mode safe
PYTHONPATH=src python3 -m lelock_entity demo --mode yolo
PYTHONPATH=src python3 -m lelock_entity demo --mode yolo \
  --exec-backend host --ack-host-risk
```

The last demonstration executes only a fixed harmless command, but **the host backend itself is unsandboxed**. Review it before enabling it in a real agent session. Tests and demos do not need a model, Palace, Docker, paid API or package download.

## Stage 2: inspect and apply the overlay

```sh
python3 tools/apply_packet.py --repo /absolute/path/Lelock-OS
# Review the printed plan and patches/changes.json first.
python3 tools/apply_packet.py --repo /absolute/path/Lelock-OS --apply
```

Five inspected baseline files are changed:

| File | Deliberate change |
|---|---|
| `project/src/lelock/runtime.py` | Optional schemas/policy; stable upstream call IDs to Entity broker |
| `project/src/lelock/server.py` | Quarantine legacy unauthenticated server startup |
| `project/src/lelock/service.py` | Correct Service rejection wrapper |
| `project/src/lelock/companions.py` | Explicit fictional lore scope; no automatic personal-fact seeding |
| `project/pyproject.toml` | Add `lelock-entity` console entrypoint |

The installer adds `project/src/lelock_entity`, `project/tests_entity_v02`, blueprint docs and the thin JavaScript integration client. It preserves modified originals in the printed backup directory outside the repository and makes per-file atomic replacements. This is **not an atomic all-files transaction**; retain that backup and inspect the diff after an interruption. It makes no commit, push, deployment or network request.

`AGENTS.md` is not silently rewritten. After reviewing the new user instruction, update it deliberately to acknowledge approved SAFE/TRUSTED/YOLO sessions and new capability modules while preserving privacy, source-lock and no-destructive-work requirements. The old instruction forbidding all process tools should not accidentally block the newly authorized testing mode forever.

## Stage 3: integrate existing tests and packaging

Run the new tests in the actual repository with `PYTHONPATH=project/src` and test root `project/tests_entity_v02`. Rerun the original suites. The old server-start expectations should fail because the old insecure server is deliberately disabled. Migrate those tests to the new authenticated contract and retain explicit regression coverage proving the old path is blocked. Do not delete assertions or skip failures to get a green count.

Review companion/lore tests for the deliberate scope change. Add a rejected nonfiction auto-seed case and a successful explicit fictional import. Confirm the original CLI still handles reviewed card activation, datachip export and normal SAFE behavior.

Reinstall the first-party package into the existing pinned Hermes environment without re-resolving upstream dependencies, following the current bootstrap's installation method. Keep optional MCP dependencies in a separate environment. Record actual package versions and interpreter paths privately, and sanitized versions in the report.

## Stage 4: prove the actual stack

Use an existing *synthetic* Lelock-owned test profile created through the original onboarding commands. Do not guess a home layout, point at private Ada, or invent model credentials. Start actual MemPalace with the original managed lifecycle. Select an already authorized model endpoint and explicitly bound spend, or finish all independent work and record the missing access precisely.

Run the new `chat` path inside the pinned Hermes environment. Verify the registered memory provider, exact tool surface and disabled native bypass. Demonstrate: real model response; recall; memory proposal/approval; correction; write proposal/rejection; approved write/read-back; restart and continuity. Then run a deliberately YOLO synthetic session and prove enabled actions execute without approval prompts.

Test Palace failure and provider failure. Neither is a successful save or action. Test Ctrl-C and operator stop, but do not claim cancellation preempts every remote model request until provider cancellation is actually wired. The current interactive `/stop` cannot be typed into the blocking input loop during an in-flight turn; an out-of-band owner control is required for the integrated UI.

## Stage 5: unified owner and graphical bridge

Refactor standalone ownership into one service containing the conversational event queue, HTTP bridge and optional Pulse worker. Do not run separate owners against the same session files. Build one streaming conversation route with tested serialization and cancellation. Add a real Tavern or native UI adapter using the supplied client; keep operator approval separate from model-facing tools.

Test the actual browser/WebView origin, token pairing, disconnection, expiring sessions, exact proposal rendering, pending action replay and no unauthenticated legacy fallback. Port card staging correctly rather than reintroducing dictionary-to-Path mismatch.

## Stage 6: agency modules and proactive tasks

Register approved Skills and one process backend. Implement a separate-process child executor with a shared broker and bounded token budget. Prove child permission attenuation and cleanup. Add deterministic pre/post hooks first; queue optional model extraction rather than running it on every turn by default.

Connect Pulse to the unified owner, add durable policy resolution and an opt-in local service. Start with one local inbox check-in and one approved project task. Then add one selected external channel and verify real delivery receipts. Add voice after text/cancellation/policy are stable. World integration can proceed independently against synthetic state, but prior Mental OS migration requires the actual prior artifact.

## Acceptance matrix

| Gate | Required evidence | This packet's status |
|---|---|---|
| New foundation unit/integration tests | Exact command, host, count, log | See generated build report |
| New loopback HTTP authorization | Real local requests and role rejection | Tested here |
| Harmless host execution | Actual output, timeout/nonzero/cancellation tests | Tested here |
| Original full repository suites | Fresh checkout, exact original counts | Not run here |
| Hash overlay on actual Mac checkout | Preflight, diff, new and migrated old tests | Pending |
| Pinned Hermes + real model | Actual turn/tool calls | Pending |
| Actual MemPalace durability | Add/read-back/outage/restart | Pending |
| Docker execution | Verified image digest and actual resource/network tests | Pending |
| Optional MCP SDK2 | Import/handshake/list/call/stop in chosen host | Pending |
| Child runtime | Separate process and shared budgets | Pending |
| Pulse model task | Real scheduled turn, lease and quiet hours | Pending |
| Native/Tavern UI | Actual browser or app interactions | Pending |
| External channel and voice | Explicit recipient/audio tests | Pending |
| Existing world migration | Supplied schema and reversible import proof | Pending |

## Release and continuation discipline

Checkpoint after each completed stage with exact facts, changed paths, test output and blockers. Do not call the whole product complete because the isolated suite passes. Preserve useful partial implementation rather than substituting promises. A local test authorization is not permission to send external messages, buy services, deploy or publish private data.

A public release includes generic code, licenses, installation instructions and sanitized synthetic evidence. It does not include this entire private handoff automatically, pairing files, Palace contents, SOUL history or arbitrary workspace snapshots. Publish only after explicit approval and a reviewed staged diff. Keep experimental features labeled until their individual acceptance gates pass.
