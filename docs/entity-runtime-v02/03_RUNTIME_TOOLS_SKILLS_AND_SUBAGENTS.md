# Runtime, tools, Skills, and subagents

## Keep the working engine; replace only the dispatch boundary

Use the exact pinned Hermes source selected by the existing `source-lock.json`. The packet does not require a moving `main`, a new subscription, or a replacement memory engine. The existing adapter is version-sensitive: it overrides `AIAgent._execute_tool_calls` while retaining Hermes planning and the registered Lelock memory provider. [L3, L6]

The source patch adds optional `schemas` and `policy` arguments to `HermesRuntime` and routes upstream tool-call IDs through `RuntimeServiceAdapter.dispatch_tool_call`. Default callers still get the original five-tool surface. New Entity callers provide the broker's selected schemas and a truthful capability policy. `assert_surface()` compares against that instance's selected schema set.

**`HERMES_YOLO=0` intentionally remains set.** Lelock's new YOLO mode is implemented by the Entity policy engine, not by re-enabling Hermes's native dispatcher. Setting both switches would create two competing permission paths. The new path really executes enabled operations automatically; the old bypass stays disabled so there is one broker.

## Registry contract

A Tool contains a stable name, description, required capability, risk classification, JSON schema and handler. Schemas advertised to the model are filtered by the selected session. Invocation validates the actual arguments again; prompt text is not authorization.

```python
from lelock_entity.core import Tool
from lelock_entity.policy import Risk

# Registration is trusted application code, never an imported character-card instruction.
core.register(Tool(
    name="example_local_action",
    description="An explicitly registered local action.",
    capability="example.write",
    risk=Risk.WRITE,
    schema={"type": "object", "properties": {
        "text": {"type": "string", "maxLength": 2000}},
        "required": ["text"], "additionalProperties": False},
    handler=lambda arguments, session: {"received": arguments["text"]},
))
```

Confirm `Tool` field names in `core.py` before extending this example. The reference validator implements an explicit subset of JSON Schema; it is not a full standard implementation. Optional third-party/MCP schemas must be validated by an appropriate supported validator or converted and checked rather than accepted by optimistic passthrough.

### Existing default tool names

Inspect `builtins.py` for the authoritative generated schemas. The reference includes status, selected-workspace text operations, world inspect/apply and optional memory/process tools. The historical `lelock_propose_text` name remains for compatibility, but in YOLO its result may be `done` rather than `pending_approval`; clients must branch on the result state rather than infer state from the name.

The workspace registry includes create, hash-checked replacement and exact-file deletion primitives. There is no recursive delete-all tool. Host process execution is the explicit escape from that bounded file API and is honestly described as unsandboxed. A default `process.run` grant is not secretly sandboxed by setting a working directory.

## Approval and execution state

All effects enter `EntityCore.invoke`. SAFE and unapproved TRUSTED writes produce an action ID plus an exact request digest. The operator reviews the tool, scope, arguments, content and risk, then approves that digest. A modified payload cannot reuse the original approval. YOLO follows the same receipt/state machinery but authorizes the enabled effect automatically.

The normal states are `pending → executing → done`, plus `rejected` and `needs_review`. On uncertain interruption, require reconciliation rather than replaying an action that may already have happened. Reusing a request ID with a different payload is rejected. A repeated completed request returns its recorded state, not a second write. This is not a universal exactly-once guarantee for remote services.

The broker records action counts, response-byte budgets and deadlines. It does **not yet enforce aggregate model-token or dollar budgets**. Those need provider-specific reservations around every model call, including root turns, child turns, memory extraction and retries. A token cost must not be guessed from an API label.

## A usable first autonomous coding slice

Implement one complete task before a general swarm: read a selected project, create or patch a file with expected hashes, run a bounded test command, inspect output, and report the verified result. Use a synthetic repository and either an explicitly acknowledged host backend or a reviewed immutable Docker image. No hidden package downloads are necessary for the packet's offline tests.

Add a model turn envelope containing task ID, session ID, capability set, remaining budgets, source references and cancellation handle. Use a stable idempotency key per proposed effect. Do not include operator bearer tokens, unrelated environment variables or private memory in child prompts.

## Skills are knowledge packages

`skills.py` loads a bounded `skill.json` manifest and `SKILL.md` with a declared file list. A fingerprint covers the reviewed pack. Symlinks, traversal and changed reviewed content are rejected. Files are instructions or reference material for the model; listing a script does not execute it or grant a new capability.

The included `source-backed-research` pack demonstrates the format. Review pins are currently in-memory. Persist approvals in the operational journal before offering install/update buttons, and bind approval to the exact content digest. Changed versions need review. A malicious pack can still contain persuasive instructions; this loader limits I/O and trust, not every prompt-injection tactic.

Search should first return a small manifest and description. Load the full Skill only when relevant. Do not prepend a thousand Skills to every conversation. Imported code examples remain text until an enabled execution tool deliberately handles them.

## Child agents

`Delegator` supplies a real task envelope, capability attenuation, shared broker/budget access and child-session revocation after completion. Child results are labeled untrusted task results and are not automatically canonical memory. The included executor callback is a **library integration seam**, not a deployed separate Hermes process.

Build the real child executor as a separate process because the current Hermes adapter manipulates process-level environment and refuses reuse of a previously imported runtime. Do not instantiate several independent Hermes homes inside one Python process and assume isolation. The parent owns memory access and brokered effects; the child receives only authorized context and a narrow callable interface.

A child may receive a subset of the parent's capabilities, not a broader list. Limits include maximum depth, task deadline, output size and shared action budget. Add model-token reservations and enforce cancellation in the actual provider process. A synchronous Python callback cannot be preempted merely by checking the clock after it returns.

Start with one child at a time: researcher, test runner, or reviewer. A role description is not a permanently deployed agent or a separate canonical companion. Preserve one root conversational owner even when many helpers exist.

## Pre/main/post pipeline

Pre-turn work should retrieve relevant memory, selected project state and Skills. Main-turn work owns the reply and permitted actions. Post-turn work may queue memory candidates, update task metadata and schedule a follow-up under a standing policy. No sidecar may silently edit the root identity, add capabilities, approve its own pending request or publish private results.

A continuity checker is a quality aid, not a secret second personality that rewrites every message. Make its changes inspectable and measure whether it improves factual continuity without flattening the companion's voice.

## Model routing

Keep endpoint/model selection explicit. A local GGUF server, a hosted compatible endpoint and a consumer chat subscription are different products. Test the actual tool protocol, streaming behavior, maximum context, image support, timeout and error format. Fail visibly rather than silently switching to a paid fallback.

The first implementation may stop and restart between model changes. Hot switching requires a normalized turn ledger and a tested adapter; storing the same SOUL file does not establish interoperability. Preserve private/local routing rules: local storage does not mean prompts sent to a hosted model remain on-device.

## MCP and external tools

Use the official SDK adapter as a transport, not as an unrestricted plugin launcher. Pair a tool name with its reviewed server identity/version, arguments schema, access mode and per-tool capability. Unknown tools are denied. A server update changing its schema invalidates the prior review until inspected.

For outbound OAuth integrations, use a supported provider flow, correct audience/scopes and credential isolation. Do not pass arbitrary incoming bearer tokens onward or assume a browser-origin check is authentication. The packet's own MCP adapter is local stdio with agent credentials only; it cannot approve operator actions. [M1–M3]

## Acceptance

Prove real root tool use, source-backed recall, no parent dispatch bypass, no privilege escalation through a card/Skill/tool output, correct child revocation, cancellation and one successful coding task. Then evaluate local/cloud continuity with selected actual models. Offline policy tests do not certify any specific model's reliability.
