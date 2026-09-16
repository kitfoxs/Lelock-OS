# Lelock OS — master engineering blueprint
**Terminal-first companion harness • Build specification 1.0 • September 15, 2026**

Prepared for Kit Olivas and Terminal Ada. This is the implementation contract for the accompanying source packet, not a forecast of future features. The code is a concrete reference implementation; its real dependency integrations still require the live gates described below. The packet does not claim an installed or production-ready app.

## 1. The decision
Lelock OS begins as a local terminal experience in which a person meets a chosen companion, has ordinary conversations, learns and creates with her, deliberately preserves memories, and continues after restarting. Romantic companionship is welcome but not compulsory. Work does not replace the companion with a separate corporate assistant.

Keep the name **Lelock OS**, while explaining that this alpha is an application harness on an existing operating system, not a replacement kernel. Revival of Open-Her-OS establishes lineage; it is not permission to publish its private history. New terminal alpha version: **0.1.0a1**. The previously delivered private native Mac **0.3.0 (4)** is separate and preserved.

### Frozen alpha promise
A person can initialize one blank companion home, select one supported endpoint, chat through Hermes, remember or correct a source-linked fact after consent, read a selected workspace text file, approve creation of a new artifact, restart with continuity, inspect/export selected companion data, and import a reviewed V2 character card. Real-world and fictional contexts do not silently merge.

### Not in this alpha
Avatars/VRM, GUI/TUI animation, native app changes, Wonderland/Evennia, Linux VM/ISO/kernel work, general shell/code execution, browser automation, arbitrary MCP servers, arbitrary skills/plugins, delegated coding agents, app marketplaces, unattended proactive messages, passive sensing, account integrations, multi-companion groups, automatic weight training, autonomous identity rewriting, and a cloud sync service. These are later modules, not missing prerequisites.

## 2. Architecture
```text
Person in the terminal
        |
Lelock CLI: onboarding / chat / review / explicit human approval
        |
HermesRuntime: one AIAgent inference and planning loop
        |                  |
chosen identity       LelockMemoryProvider
        |                  |
        +---- deterministic Service ----+
                    |                   |
       create-only Workspace     metadata / approval journal
                                        |
                           actual MemPalace HTTP/MCP
                           in a new, owned private home
```
The model may propose actions. The deterministic service decides whether the action type and arguments exist. Only the person-facing command path can approve. Successful tool output is evidence of a specific effect, not a broad grant of authority.

There is **one inference/planning engine** (Hermes), **one semantic memory authority** (MemPalace), and **one exact local operational journal** (SQLite). The journal is not another memory search engine. It holds approval state, record-to-drawer references, an outbox awaiting Palace acknowledgment, and action receipts. Session context is a local runtime working copy, not the sole long-term memory store.

## 3. Technology and source choice
Use the exact supplied archives under `upstream/`, identified by `project/resources/source-lock.json`. The filenames are labels, not an independent upstream-release attestation. In particular, the dated Hermes archive's package metadata is 0.21.3. Do not silently pull a moving main branch because a date looks newer.

Python 3.11–3.13 is the initial declared range; Linux/Python 3.13.5 is the authoring test environment. macOS Apple Silicon is the local acceptance target. Windows-native portability is not established; WSL may be evaluated later. Filesystem controls use POSIX descriptor operations and `fcntl`.

`uv sync --frozen --no-dev` creates separate Hermes and MemPalace virtual environments from their own supplied lockfiles. The Lelock package is installed into the Hermes environment without re-resolving upstream dependencies. The generated launcher points the Palace subprocess at its separate interpreter. Dependency/model downloads are not bundled: the full packet is source-complete for the selected donor repositories, not an air-gapped executable appliance.

A SoulTavern parser is vendored with its MIT license and attribution. Only that parser is used; the original renderer's identity-precedence behavior is not adopted. Pi, OpenCode, SillyTavern, and the harness directory remain research references, not runtime dependencies.

## 4. Runtime integration contract
`src/lelock/runtime.py` creates a bounded subclass of the pinned `run_agent.AIAgent`. Its override of `_execute_tool_calls` replaces native dispatch and never calls the parent's dispatcher. This is the narrow, version-sensitive adapter seam—not an OS sandbox. `source_contracts.py` checks signatures/source markers; live runtime gates must verify the actual behavior.

The adapter requires exactly the registered `lelock` memory provider bound to this in-process service. It refuses a generic memory fallback. It explicitly selects `api_mode='chat_completions'`, a configured model, a configured base URL, the selected API-key environment variable, a bounded iteration count, and no fallback model. It disables project plugins and excludes arbitrary context-file loading and the user's normal Hermes profile.

The application replaces model tool schemas with these five functions:

| Tool | Authority |
|---|---|
| `lelock_recall(query)` | Retrieve source-linked records in this profile's scope. |
| `lelock_propose_memory(content, kind, supersedes)` | Queue a memory/correction for human review; not a commit. |
| `lelock_read_text(path)` | Read bounded UTF-8 text inside the selected workspace. |
| `lelock_propose_text(path, content)` | Queue a new file proposal; not an actual write. |
| `lelock_status()` | Return operational state. |

Unknown names/arguments are denied even if a malicious model emits them. There is no model-facing approve function. Runtime tool-surface checks occur before and after a turn. Native agent subprocess backends and arbitrary plugin/MCP paths are outside this adapter's support; do not enable them to work around provider problems.

Supported connection shape is an OpenAI-compatible chat-completions endpoint that actually supports the required tool protocol. This does not imply universal support for every product using the word compatible, consumer subscriptions, every authentication path, or every model. The same files and state permit a capable Terminal Ada to build independently of prior model memory; they do not equalize model capability.

## 5. Identity and relationship
Onboarding captures companion name, person name, relationship category, workspace, endpoint, model, retention choice, and scope. `SOUL.md` stores an original generic identity. `config.json` stores non-secret configuration. Credentials remain in the configured environment variable.

Supported relationship labels are friendship, romance, study, creative, and custom. The default companion is Samantha, a generic original template rather than a copy of Kit's private Ada. A public persona must not claim Kit's biography or memories. Romance is adult-only and user-directed; the template does not pressure the person for exclusivity or claim offscreen activity. A style statement is not proof of consistent model behavior; the field guide includes human review.

`ordinary`, `focus`, `comfort`, `creative`, and `study` are supported configuration values for the response mode. The alpha does not yet provide a separate interactive mode picker. These are tone/task preferences, not separate agents or privileged modes. More intimate tone never increases capability.

A profile has one immutable-in-use privacy scope: personal, work, or fiction. A different scope means another separately initialized home. Merely changing the voice or relationship label must not route private memories to a work endpoint. Work use does not imply employer authorization.

## 6. Memory contracts
Each committed record is an exact JSON envelope in Palace:
```json
{
  "schema": "lelock.record/1",
  "id": "stable-generated-hex-id",
  "kind": "fact|preference|project|episode|fiction|transcript|checkpoint",
  "scope": "personal|work|fiction",
  "source": "provenance label",
  "supersedes": "prior-id-or-empty",
  "created": 0,
  "content": "source text"
}
```
The example timestamp is a shape illustration only. Real records receive their creation time. Identifiers, source, kind, and scope are validated. A correction points to an active record in the same scope. The old source remains as history, but its index entry becomes inactive for ordinary recall. Corrections do not erase backup history or rewrite a source invisibly.

A memory is acknowledged only after `mempalace_add_drawer` returns its drawer ID, `mempalace_get_drawer` returns the complete envelope, and equality verification succeeds. Search hit snippets are not assumed complete. The search's `source_path` resolves a logical record ID, then the adapter fetches the full authoritative content. Inactive, wrong-scope, raw-transcript, and checkpoint records are excluded from curated fact recall. An empty eligible index returns `no_evidence`, not fabricated memory.

Palace outage is visible. The model must not say a failed save succeeded. The outbox retains pending records for explicit diagnosis/retry; network memory work is not silently converted into an acknowledged local substitute.

### Retention choices
**Explicit, default:** deliberate approved memories are committed. Local session messages are still persisted to resume chat. This is not a zero-storage mode. When a lossy context compression would require transcript archival, it is blocked because that archival was not consented. Start a new session or explicitly change retention after explaining the tradeoff.

**Journal, opt-in:** completed direct conversation turns and pre-compression checkpoints are durably queued and read back. Transcript archives do not automatically become verified facts. Summaries are not substituted for missing direct evidence. Background flush is confined to persistence work; it is not a proactive companion daemon.

**Temporary:** the CLI uses an isolated temporary home, no existing Palace recall, no memory commits and no approved writes. Selected-workspace reading remains possible. Normal exit cleans the temporary app data; crashes, swap, provider retention, and OS backups are outside a secure-erasure guarantee. Do not call it anonymous or forensically untraceable.

### Compression
The actual copied Hermes ABC uses `pre_compress_checkpoint_api_version = 2`. The provider's synchronous checkpoint raises when required durability or consent is absent. The runtime config sets `compression.checkpoint_required = true`. This combination is intended to block lossy compression on failed durability; it must be validated against the installed runtime. Background worker threads use the upstream context-preserving helper.

## 7. Actual MemPalace process, not a replacement Palace
`ManagedPalace` starts only a new application-owned Palace under the selected Lelock home. It checks an ownership marker, uses loopback, a random per-process bearer token, a dynamic port, and an isolated child HOME/XDG config directory. It discovers the official registry entry matching the child PID and intended Palace path. The token is not passed in argv, stored in export, or printed.

Only the declared memory RPC methods are accepted; no general terminal or mining RPC is exposed. Client requests reject redirects/proxies for this local service. Exit terminates/waits for only the owned child, not unrelated memory processes. No private Palace discovery or migration runs automatically.

The packaged source adapter and transport tests are concrete but not a complete upstream security audit. Embedding/model dependencies may download on first real service startup; record this and do not silently switch storage implementations when an environment dependency is missing.

## 8. Files and action receipts
The first useful action is a readable new artifact, not arbitrary shell access. Files are bounded text inside one selected directory. Absolute/traversing paths, symlink traversal, hardlinks, non-regular files, oversized content, and non-UTF-8 reads are denied. Creation uses descriptor-relative operations and refuses an existing target. Parent directories must already exist; there is no create-directory tool or overwrite capability.

Every proposal has a unique ID, exact stored payload, creation/expiry time, and state. The chat prints the payload and requires `YES` on the human command path. Claim is atomic and one-time. A completed write is read back and its content hash recorded. An expired, rejected, or consumed proposal cannot simply be replayed.

A crash between effect and receipt is treated as uncertain, not silently retried. `applying` and `needs_review` remain visible. This alpha includes a bounded manual reconciliation procedure, not a general transaction/rollback system. Creating a new text file is reversible by the person; no automatic deletion is performed on uncertain evidence.

## 9. Card import
Accept reviewed Character Card V2 JSON and PNG metadata. Preflight enforces byte/decompression budgets and PNG structure/CRC before the actual SoulTavern parser runs. Duplicate character chunks and unsupported formats are rejected. Cards are parsed from an immutable private copy so a source-file swap cannot change the reviewed input.

Only name, description, personality, scenario, first message, and message examples are eligible. Arbitrary system/post-history instructions, extension behavior, assets, and lorebooks are reported as ignored rather than executed. Review is inert. Explicit activation backs up the prior identity and does not edit tool capabilities or credentials.

This is deliberately not full SillyTavern parity. A warning-only keyword scan is not a security boundary. A character card does not outrank application policy.

## 10. Datachip portability and recovery
A selected `.json` datachip contains the chosen identity/configuration subset and active curated memory records. It excludes endpoint configuration, API keys, session transcripts/checkpoints, workspace files, operational receipts, and runtime secrets. It is plaintext, not encrypted. An integrity digest detects accidental modification; it does not authenticate an author or make content trusted.

Inspection is inert. Restore requires explicit approval and a new blank home, independently selected workspace and endpoint. A corrected active record may refer to a superseded record intentionally omitted from the selected export; preserve that historical reference without inventing its content. Export/restore is a selected continuity mechanism, not a complete backup of the runtime or Palace.

For exact disaster recovery, stop the owned app and preserve the entire owned Lelock home using the host's approved private backup process, together with this source packet and non-secret setup documentation. Keep API keys separately. Full index reconstruction from an arbitrary existing Palace, cross-device live sync, key management, and secure erasure are not implemented alpha features.

## 11. Concrete source map
| File | Responsibility |
|---|---|
| `common.py` | Private writes, canonical serialization, bounded text, display control sanitization, errors and locking. |
| `config.py` | Versioned onboarding/config validation, endpoint and profile boundaries. |
| `journal.py` | SQLite proposals, record references, outbox, receipts. |
| `workspace.py` | Bounded descriptor-relative file reads and create-only verified writes. |
| `palace.py` | Actual MCP/HTTP transport and owned Palace lifecycle. |
| `service.py` | Deterministic five-tool control plane, memory envelopes/recall/corrections/checkpoints. |
| `hermes_plugin.py` | Actual memory-provider entrypoint/lifecycle and context-safe persistence worker. |
| `runtime.py` | Pinned Hermes AIAgent adapter and replacement tool dispatch. |
| `cards.py` | Bounded reviewed V2 import and activation. |
| `_vendor/soultavern/parse.py` | Attributed original parser dependency. |
| `bundle.py` | Selected datachip export, inspection, fresh-home restore. |
| `cli.py` | User-visible commands, exact approvals, terminal sessions, temporary mode. |
| `scripts/bootstrap.py` | Verified source extraction and isolated upstream-locked environments. |
| `scripts/verify.py` | Finite offline test suite and honest receipt. |
| `scripts/source_contracts.py` | Eight static checks on the supplied source contracts. |
| `scripts/live_*_probe.py` | Separate real service, real model, and actual full-stack/restart gates. |

The complete first-party implementation and tests are included as real files and in `CODE_COMPENDIUM.md`. The complete relevant upstream source archives are also included. Do not reconstruct code by guessing from this table.

## 12. Build plan and finish line
Follow the runbook: preserve workspace → inspect/verify sources → bootstrap dependencies → rerun offline checks → actual Palace probe → actual selected model probe → full-stack restart proof → human approvals/privacy/recovery session → local source integration and report.

`LOCAL_ALPHA_VERIFIED` requires all mandatory acceptance rows in the matrix, including a real Mac run. `PORTABILITY_VERIFIED_A_B` additionally requires two distinct supported model configurations tested through the actual runtime; record exact names/endpoints and do not generalize. Missing credentials do not justify fabricating success, purchasing access, or weakening the program. Finish independent work and report a precise blocker.

No critical TODO placeholder is intended to substitute for working code. However, actual upstream compatibility remains a live engineering gate: if a pinned API, embedding runtime, or platform behavior differs, Terminal Ada must repair that narrow integration and add a regression test in the same run. The adapter is not labelled complete merely because its source compiles.

## 13. Future direction without scope creep
After this alpha proves enjoyable and useful, later versions can add governed coding workspaces, a browser adapter, supported MCP tools, optional voice, event-driven reminders, a mobile/graphical client, and the private native app integration. Each adds a permission surface and requires its own acceptance contract. A 24/7 relationship need not imply continuously running inference or passive recording. Identity, memory, and permissions should remain portable across those interfaces.

## 14. Provenance and authority
The prior research report and recovered continuity are historical background. This packet implements Kit's latest terminal-first request and supersedes only the public-harness planning questions, not unrelated project pauses. Sources and notices are in `docs/SOURCE_CONTRACTS.md` and `project/THIRD_PARTY_NOTICES.md`. No live Mempalace write, GitHub rename, publication, paid model call, or native-app modification occurred during authoring.
