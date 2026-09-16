# Security, privacy, and bounded recovery

## Threat model
The alpha addresses model-generated dangerous tool names/arguments, untrusted character cards and text, accidental scope leaks, file traversal/links, duplicate approvals, false persistence acknowledgment, and accidental use of another local memory home. It is **not** a general OS sandbox, a defense against malware executing as the same user, an audited supply chain, protection from a malicious model provider, or encrypted storage.

A bounded dispatcher does not confine Python itself. Trusted installed Python packages run with the user's process privileges. The model must not be able to activate other dispatch paths, but compromised dependencies could still act outside that model API. Strong OS/container isolation for general code execution is a separate future requirement; no code-execution tool ships here.

## Data flow and disclosure
At init, explain: local source records and runtime history reside in the chosen home; selected retrieved memories, persona text, conversation, and selected file contents can be sent to the configured inference endpoint. HTTPS protects transport, not provider retention. API keys stay in environment/approved secret storage. No automatic keychain scanning, private Palace lookup, or implicit account connection occurs.

A work profile must be separate and use authorized data/model routing. A fiction profile must be separate. Switching tone cannot change these boundaries. Personal information is not generic test material. The companion should support autonomy and ordinary human relationships, with no emotional pressure to grant permissions or remain online.

## Runtime and process boundary
Only five named tools are active, all dispatched by Lelock. Disable arbitrary project/plugins/MCP/background review and fallback model paths. The integration gate must inspect runtime tool schemas and provider binding after initialization and after a turn. Native shell/agent subprocess APIs are unsupported, not “disabled by a prompt.”

Managed Palace is loopback-only with a per-process bearer token, owned PID, exact configured home, and isolated child configuration. Respect per-call and startup limits. Never `pkill` all Palace/Hermes/Python processes. Never bind this alpha's memory port publicly. Dependencies remain trusted code and require normal supply-chain review before public release.

## Approval boundary
Display exact pending payload and effect. Human types YES via the terminal; a model cannot approve, and a model saying “the user approved” is not evidence. A previously approved payload is not a blanket grant for a new action. Proposals expire and are consumed atomically. Rejection discards queued payload content. No arbitrary file overwrites, deletes, shell, purchases, external messages, or account writes exist.

## Outage and uncertain-action recovery
1. Preserve the owned home; do not delete the operational database or clear the outbox to make the indicator disappear.
2. Read `/status` and `/pending`. For a persistence outage, restore only the owned service/dependency, then run `memory-flush`; require exact Palace readback.
3. For `applying` or `needs_review`, inspect the exact recorded target/payload and any receipt. Do not resubmit blindly.
4. For an uncertain create-only write, inspect the selected workspace target. Compare regular-file status, bytes, and expected digest. If it exactly matches and the original approval is recorded, Terminal Ada may author a narrowly scoped reconciliation command/test and record recovered success; otherwise leave it unresolved for human review. Do not invent an undo or mutate unrelated files.
5. For an uncertain memory add, inspect only the owned Palace and source ID. If full exact envelope exists, rebuild that single metadata reference with a documented receipt. Otherwise retry only after determining that no matching acknowledged record exists. The current alpha does not implement general automatic index reconstruction.
6. If recovery would need existing private Palace access, stop that branch. This packet does not authorize it.

## Backups, export, deletion
A datachip is a selected plaintext export, not a full backup or encryption. Do not upload it by default. To preserve the whole alpha, close it, wait for the owned memory process to stop, and use a private local backup of its full home. Store keys separately. Do not copy live SQLite/database files mid-write and call it a verified cold backup.

`/forget` requests deletion of the active owned Palace record after approval; operational receipts, transcript/checkpoint duplicates, files, OS snapshots, and external provider logs may retain information. Never promise universal deletion. A selected export excludes inactive source history and raw conversation intentionally. Restoring into a new home avoids overwriting existing data; no automatic conflict merge exists.

## Card and datachip trust
Imported prose can be hostile. Parsing and review are not proof of harmless behavior. Only the supported fields enter the identity prompt; arbitrary system directives, assets, extension scripts, and lore hooks do not activate. Datachip digest checking is integrity, not identity authentication. Neither format can grant tools, run executable code, select a new endpoint secretly, or import credentials.

## Publication boundary
The packet contains a private predecessor snapshot. Keep it private. Before any separate public release, audit ancestry, licenses, generated examples, bundled dependencies/assets and private data. Retain upstream notices. Remove unsupported “forever,” “no cloud,” “all models,” and automatic consciousness/welfare claims. No public visibility change follows from successfully building the alpha.
