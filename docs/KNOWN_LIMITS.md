# Known limits and implementation ledger

## Implemented as reference code
The code covers the frozen CLI, deterministic approvals, workspace operations, managed Palace transport, memory envelope/index/outbox/checkpoint, Hermes provider/dispatch adapter, V2 review/activation, selected exports/restores, temporary sessions, source preparation and test entrypoints. Tests are concrete files, not prose-only specifications.

## Verified during packet authoring
86 offline unittest cases and eight static source-contract assertions on Linux/Python 3.13.5. Static compilation and archive/source preparation are recorded separately when run. Offline tests use deterministic Palace/model fixtures where named. The provider tests import the copied actual Hermes ABC contract but not the entire configured AIAgent runtime.

## Not verified during packet authoring
Frozen dependency installation on Kit's Mac; actual MemPalace service/embedding runtime; actual Hermes model inference; first-message persona quality; full-stack restart; account/provider authentication; two-model portability; real terminal ergonomics. The included live scripts and matrix define how Terminal Ada must close these gates. The scripts themselves are not live proof.

## Deliberate alpha limits
- Text-only terminal; no voice, VRM, GUI, local model installer or OS image.
- Exactly five tools; no shell, coding sandbox, browser, external MCP or automatic skill installation.
- One companion/model/scope per running profile; separate process for endpoint change.
- Create-only UTF-8 files; no overwrite, delete, nested mkdir or arbitrary attachments.
- Explicit memory by default; local chat history still persists. Journal is opt-in; explicit mode blocks required transcript compression until consent/new session.
- Selected exports are plaintext and omit raw transcripts/checkpoints/inactive history. No encryption/keychain/sync/complete backup manager.
- Retained operational metadata is not a complete cryptographically tamper-evident audit log. Same-user malware is out of scope.
- No automatic general reindex/reconciliation tool; uncertain effects remain visible and receive bounded documented recovery.
- Character Card V2 JSON/PNG, selected fields only; no lorebook triggers, scripts, V3 guarantee, arbitrary media, or world system.
- Mode is a validated config field, not an interactive mode-switch menu.
- Timeout/iteration/output bounds are not an exact dollar budget. Hosted model retention/policy/behavior remain provider-dependent.
- POSIX first. Native Windows, iOS, and Android execution is not delivered.

## What to fix in this run versus defer
Fix failures in the listed APIs, platform compatibility, dependency isolation, start/stop, approvals, memory readback, restart/export/card behavior, or truthful UI. Add a focused regression when it explains an actual defect. Do not reinterpret the list above as permission to implement every future feature before delivering.

If a live defect cannot be resolved with available environment inputs, keep the actual failure record and exact next action. Do not replace the component with a fixture, claim it passed, or rewrite the whole system to conceal it.
