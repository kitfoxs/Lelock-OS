# Master implementation contract: deliver the thing Kit clicks

## 1. Product goal and what supersedes earlier planning

The immediate product is an installable SillyTavern extension backed by the existing
Lelock Entity Runtime. It should let a person bind a character, choose permissions,
use a supported signed-in model, and have **that same character** perform useful
work. A switch to work must not silently replace the companion with an anonymous
coding agent. Helpers are opt-in named character entities.

This supersedes the idea that a thin HTTP client plus a tested core library counts
as a finished Tavern integration. It does not supersede MemPalace authority, private
identity ownership, the existing native Mac application, or preserved Mental OS
artifacts. The existing `lelock_entity` implementation remains the tool broker;
this packet adds `lelock_tavern`, not another competing general agent kernel.

The supplied code is a connected implementation candidate. Native APIs, environment
integration, browser behavior, provider terms, and model tool reliability require
live acceptance. Reference tests cannot establish all of those facts.

## 2. Two execution modes; one entity

### A. Enhance the existing SillyTavern connection

SillyTavern still constructs prompts and runs its selected model. The extension
fetches the gateway's authorized schemas and registers them through the host's
function-tool interface. Each callback captures the selected character and chat;
a stale callback after switching cards is refused. Results and exact approvals
come from EntityCore. This route needs a host connection/model that actually
supports tool calling. It does not remove the host's model setup requirement.

### B. Account Chat

SillyTavern is the character picker, conversation display, and operator panel.
The gateway runs the selected account-native backend and registers the same
character's tools. The explicit **Lelock Send** button works without configuring
a separate SillyTavern model API. A generation interceptor aborts the host API
path when Account Chat is selected to avoid accidentally calling two providers.

Codex uses the official app server; Antigravity uses its unmodified native CLI.
Both receive the selected character context and bounded selected chat history.
The main model owns tool calls; Rakazo supplies the computer, not another model.
Fresh native conversations are created for each gateway turn to prevent one card
or chat from inheriting another's native session. The local turn ledger and
MemPalace carry continuity; a global native `--continue` is never used.

The initial Account Chat prompt uses six reviewed card fields and the selected
conversation history. It is **not full parity** with every SillyTavern lorebook,
regex, prompt-preset, extension, alternate-greeting, swipe, or macro behavior.
Those features remain native in Enhance mode. Implement additional Account Chat
context compilation as a separately tested adapter, not by blindly forwarding
all hidden prompts or declaring imported lore to be autobiographical fact.

## 3. Connected architecture

```text
SillyTavern card + current chat
        |
new extension: pair, bind, configure, dynamic tools, Account Chat
        |
authenticated local multi-character gateway
        |
entity mapping / card context / operational turn ledger
        |
existing EntityCore: capabilities, SAFE/TRUSTED/YOLO, receipts
        |                         |
selected main native runtime      actual MemPalace adapter
        |
main character's own tool call
        |------------------ local workspace / Skills / world
        |------------------ Rakazo Private Computer for this entity
        |------------------ optional named helper character
                                  |
                              helper's own context, scope, computer
```

There is no Pi delegation merely because Rakazo is used. `rakazo.py` exposes
computer tools and `service.ts` calls the actual SandboxProvider interface.
The primary Codex or Antigravity model sees the observations and chooses actions.
This preserves one foreground character across conversation and external work.

## 4. Entity mapping and identity discipline

Browser bindings use a generated client ID and generated card key, retained in
SillyTavern settings. The current local avatar filename selects that mapping;
array position and display name are not durable identity. Two cards named Ada
receive separate entities. Copying or renaming a card must not automatically
merge identity. The panel supports explicit attachment to an existing entity ID.

Gateway records retain entity ID, curated card data, configuration, workspace,
turn records, and optional Palace association. Rebinding an already-bound card
does not silently overwrite identity. Card edits need an explicit reviewed sync
workflow before they change an existing entity. The packet does not claim that
workflow is complete. Native Account Chat should warn/document that the initially
bound six fields are the current authoritative gateway character snapshot.

Each entity receives a separate workspace and optional Palace home. A helper is
another bound card with its own identity, not a temporary name pasted over the
main character's memory. Group-chat speaker routing is rejected in this release;
finish explicit speaker mapping before claiming support for arbitrary group chats.

## 5. Tools and real autonomy

The new client does not hardcode five legacy routes. It fetches the authoritative
tool schemas and invokes the current gateway. The original v0.2 `/v1` protocol
remains an existing single-core API; this gateway's `/v2` adds entity routing,
accounts, native turns, and exact operator actions. It does not reopen the old
unauthenticated `/api/remember` server.

Available tools depend on the entity's capabilities and installed adapters:
status; workspace read, create/replace/delete; actual Palace recall/commit when
enabled; reviewed Skill reading; world inspect/apply; explicit host execution;
direct Rakazo command, observation, desktop actions and text-file access; and
named helper invocation. Listing a capability does not install its dependency.

SAFE produces a proposal. TRUSTED executes only declared standing grants. YOLO
executes granted capabilities without asking for every action. All use the same
broker and action records. The native tool callback waits for a real approval
result, then returns the actual effect receipt to the model. It does not tell
the model that a queued proposal already ran.

The new gateway does not expose workspace host execution unless launched with
`--allow-host-exec`. That grants access to an unsandboxed OS-user runner; selecting
a working directory is not containment. Each entity must separately receive
`process.run`. Rakazo Docker is a different execution environment. Native agy
also has its own built-ins; its separate permission bypass requires both an
explicit native acknowledgement and native-YOLO selection.

## 6. Native-account experience

The main supported implementation is **Sign in with ChatGPT through Codex**.
An official browser/device flow owns the OAuth callback. The app-server manages
its credentials in a dedicated home. The gateway exposes only account summary,
login URL/code, model catalog and quota information—not access/refresh tokens.
The user chooses an actual advertised model; the code does not hardcode a
frontier-model entitlement based on a subscription name.

Antigravity signs in interactively through its own app, then uses cached native
credentials in headless mode. No provider token parser or copy operation exists.
A scoped local MCP bridge supplies only the current actor's tools. It exposes no
operator approval command. Headless native approvals that cannot be fulfilled
are errors or a request to use the native client; no invented protocol response
is sent to approve them.

Claude subscription login is native-only under the documented restrictions.
OpenCode and Hermes are offered as native launch/setup routes; their account
capabilities do not automatically make Lelock's existing pinned custom endpoint
adapter support every consumer subscription. Further integration must use an
explicit supported runtime interface, not stolen tokens or old forbidden plugins.

Quotas and optional paid overage remain provider-controlled. There is no silent
fallback to an API key. This gateway counts broker actions/time/output and exposes
Codex's native quota read; it is **not a universal dollar-budget enforcement layer**.

## 7. Direct Rakazo integration

The sidecar is installable source in the overlay and has its own installer into
an actual Rakazo checkout. It imports the pinned factory and uses Docker; it does
not invent a public Grok Bots endpoint. Every call is supplied an actor by trusted
gateway code, not by a character-controlled argument. The sidecar obtains one
Private Computer per actor and verifies that the provider returned that owner.

It performs direct commands, screenshots, desktop actions, text reads/writes, and
stop. File writes require exact readback. Missing exit receipts, partial action
completion and readback failure mark uncertainty instead of replaying the action.
Stopping an unused computer never provisions a new one.

The sidecar stores the opaque computer reference before fallible preparation.
Its first live target is Docker with persistent actor-owned host directories.
E2B, Daytona, Box, shared Team Computers, and provider migration are **not enabled**
here; remote checkpoint/restore and credential/lease behavior need real tests.

A named helper uses the helper's character and Private Computer. Permissions are
the intersection of main and helper permissions; helper delegation is nonrecursive.
The stricter approval policy wins. Child work uses the parent's broker action
budget and stop signal. There are no unbounded random-agent spawns. The first
implemented named helper native backend is Codex; Antigravity's independent host
powers are not represented as attenuated by the Lelock broker.

## 8. Pulse and Skills are now connected, with bounded scope

The operator can inspect a local Skill pack, approve its exact hash, and grant
`skills.read`. Review pins persist privately. A changed pack requires review.
Knowledge files do not install plugins or grant capabilities.

With `--enable-pulse`, the panel can authorize a recurring task for the same
character. It invokes that character's configured Account Chat backend and broker,
then writes the real result to a local inbox. The first UI permits intervals of
at least ten minutes and a one-hour lease; the backend caps a schedule lease at
two hours, and no schedule outlives its Entity session. Quiet hours are active.
Restarting or changing permissions invalidates old schedule authority rather than
silently reviving it. This is not Discord delivery, SMS, voice, a phone call, or
an always-running LLM. There is no passive microphone or desktop monitoring.

## 9. Completion gates, not feature-count marketing

Pass the new tests against the real checkout, then the existing tests, then live
native account and model calls, actual Palace where enabled, actual Rakazo Docker,
and the real SillyTavern workflow. Browser fixture tests are useful but do not
replace a real SillyTavern generation. Source compilation is not OAuth verification.
A mock computer call is not a Docker desktop test. Record each separately.

The acceptance scenario is: install -> pair -> bind two different cards -> log
in once -> main card directly creates and reads a file -> SAFE approval -> YOLO
without repeated prompts -> switch card without identity/history/file leakage ->
assign a named helper -> observe actor-specific actions -> stop -> restart ->
reattach without losing mappings -> actual memory continuity where enabled.

After this works, finish prompt/lore parity, group speakers, richer voice/UI,
remote computers, all-channel messaging, aggregate model-cost enforcement,
long-running scheduling and native-app/Mental OS integration. Those are explicit
remaining tasks, not prerequisites for proving this focused product loop.
