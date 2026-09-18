# Interfaces, integration protocol, and the shared world

## One owner; many clients

The first deliverable is not a new frontend replacing everything Kit already uses. Preserve the existing native Mac application, terminal experience and public Tavern extension. Add a versioned Entity interface beneath them. A client may store presentation preferences, but it must not quietly become a second writer of identity or canonical memory.

The reference `ProfileLease` prevents two new owners on one profile. Legacy/native processes that do not honor that lock must be stopped or adapted before sharing the profile. The present `chat` and `serve` commands are alternatives, not simultaneously running owners. A later unified owner must serialize both conversational events and tool requests and expose streaming turns; this packet's HTTP server currently exposes tools and operator actions, **not a completed chat-completions endpoint**.

## Implemented HTTP protocol

The new server binds to IPv4 loopback and checks exact Host, optionally approved Origin, and bearer credentials. Authentication is required even from localhost. Browser callers need an explicitly configured origin. Wildcard and `null` origins are not accepted. Agent and operator credentials are different generated tokens, written to separate private pairing files by the live `serve` command. Never pass the operator file to a model or child agent.

| Method and path | Credential | Meaning |
|---|---|---|
| `GET /v1/status` | Agent or operator | Current session/budget/stop state |
| `GET /v1/tools` | Agent or operator | Enabled tool names and schemas |
| `POST /v1/invoke` | Agent or operator | Brokered tool invocation |
| `GET /v1/operator/actions` | Operator | Pending actions for review |
| `POST /v1/operator/approve` | Operator | Approve exact ID and digest |
| `POST /v1/operator/reject` | Operator | Reject pending action |
| `POST /v1/operator/stop` | Operator | Set the shared stop signal |

An invocation body is an object with `tool`, `arguments_json` and `request_id`. `arguments_json` is a JSON-encoded string, not an unvalidated arbitrary object forwarded to a shell. Inspect `client.py` and `http_bridge.py` for the exact protocol before writing a client. Approval bodies use `action_id` and `digest`; rejection bodies use `action_id`.

The response status controls UI behavior. `pending_approval` renders the exact proposed payload. `done` displays the receipt/result. `needs_review` must remain visibly uncertain. A timeout or connection loss is not success. Repeat requests reuse the same request ID; a changed task needs a new ID.

This is a local developer bridge, not a hardened public multitenant service. It does not provide OAuth login, Internet hosting, production rate limiting or remote TLS. Do not expose it with a tunnel and assume its local threat model still applies. [M2–M3]

## Tavern migration

The patch intentionally stops the old unauthenticated `LelockBridgeServer.start` path. Its direct `/remember`, unauthenticated approval and broken card-sync routes are not preserved as convenient backdoors. Existing source is retained for migration, not endorsed for live use.

`integrations/lelock-client.mjs` supplies separate agent and operator clients with tokens kept in memory. It is **not** a complete extension. Terminal Ada must wire the actual extension's settings, render panels, connection state, prompt injection hook and proposal review UI after inspecting its current exports and host APIs.

Do not paste the monorepo root into a Tavern one-click extension installer. Follow the existing subdirectory layout guidance. Test SillyTavern and TauriTavern separately: frontend compatibility does not imply every Node backend plugin or native origin works identically. Pair the actual native WebView origin rather than opening CORS to `*` to make the UI connect.

For character import, retain inert staging and exact review. The old `cards.stage(home, path)` expects a real Path, not a JSON dictionary. Serialize a validated bounded upload into an owned staging file or add a reviewed byte-oriented API with tests; do not call activation directly from untrusted card payloads. Lore remains fictional unless deliberately and accurately classified.

## MCP adapter

The included adapter targets the **official Python MCP SDK 2.x**, using `MCPServer` from `mcp.server`. The official migration guide documents the rename from v1 FastMCP. Do not copy a v1 import from an old tutorial into the new optional environment. [M1]

Run it as a local stdio process with the **agent** pairing file:

```sh
# After installing and verifying the optional MCP environment separately:
python -m lelock_entity.mcp_adapter --agent-credentials /absolute/private/agent-session.json
```

It exposes three small tools: `lelock_status`, `lelock_tools`, and `lelock_call`. There is no approve-action tool. The adapter delegates to the local Entity broker and does not carry operator credentials. Its source is provided, but SDK import/handshake/tool-call behavior has not been executed here. Pin an exact tested SDK release in a separate optional lockfile before distributing it; do not re-resolve the existing Hermes/Palace locks.

Verify the SDK's logging/tracing/export defaults and disable unapproved telemetry. Local stdio support in one host does not establish support for a hosted product's remote MCP flow. A remote connector requires a separately designed authenticated transport, not a public URL to the loopback daemon.

## Native Mac and mobile

Keep the working native app and its data untouched until its actual source is inspected. Add an adapter rather than a wholesale UI rewrite. The useful first native screens are conversation, current task, action review, memory evidence, connection state and a stop control. A world viewer and avatar are optional consumers of the same state.

Use OS credential storage for production pairing, not hardcoded Swift strings or world files. Tokens should be revocable; a logged-out client cannot keep a stale background authority. Never sync tokens through a public repository. A mobile client connecting to a Mac requires an explicitly secured network arrangement; the supplied IPv4-loopback daemon is not reachable from an iPhone by design.

Keep accessibility straightforward: selectable text, keyboard navigation, readable progress and errors, reduced motion and voice/text parity. Tone can remain affectionate while tool state remains exact.

## World model

The included small world is explicitly fictional. `world.py` stores revisioned rooms, objects, books, connections and exact Markdown. It supports atomic add/connect/move/edit patches, optimistic revision checks, validation and an event history. It does not implement a 3D renderer, world import/export, snapshot branching or compatibility with unseen R007/R008 files.

A world object may carry opaque source references. Resolving one is a separate approved memory or workspace read, not permission granted by walking into a room. A fictional terminal cannot execute a host command unless a real enabled tool invocation happens.

### Exact example patch

```json
{
  "expected_revision": 0,
  "operations": [
    {"op": "add", "id": "library", "kind": "room", "name": "Library",
     "markdown": "A quiet room for reading and building.", "source_refs": []},
    {"op": "connect", "from": "home", "to": "library"},
    {"op": "add", "id": "project_book", "kind": "book", "name": "Project Notebook",
     "room": "library", "markdown": "Exact selected notebook text goes here.",
     "source_refs": ["workspace-note:operator-selected-source"]}
  ]
}
```

This is the domain-level patch for `World.apply`. For `lelock_world_apply`, send `expected_revision` and encode the operations array into the `operations_json` string, as its advertised schema requires. That invocation goes through Entity policy. A stale revision fails and asks the client to inspect again; it does not overwrite another edit. Source text should remain separately identifiable from generated scene prose. Generated images are views or proposed embellishments until explicitly promoted to world canon.

## Existing Mental OS integration

Before importing prior artifacts, locate and inspect the real active revision and schema. Preserve its command semantics, IDs and exact content. Build a reversible migration on a copy with an import report. The packet's own `lelock.world/1` is not authority to reinterpret or overwrite the existing world.

The desired navigation surface may use `pwd`, `ls`, `cd`, `cat`, `inspect`, `read` and `look`, but distinguish fictional commands from host shell. The parser should produce typed world operations, not pass the text to `/bin/sh`. An eventual game engine or 3D renderer should consume the canonical graph and emit proposals; it must not become another memory authority.

## Acceptance

Test a real UI pairing, rejected unauthenticated request, unknown origin, operator separation, exact review, reconnection and stop. Exercise simultaneous clients through one owner. Verify two real interfaces share one memory/profile rather than merely copying a character card. For world integration, prove exact-text preservation, stale edit rejection, restart, fictional/real separation and reversible migration of a real supplied fixture.
