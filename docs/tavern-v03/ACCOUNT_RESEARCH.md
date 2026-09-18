# Current research and provider integration choices
**Verified September 17, 2026.** Provider behavior and policies can change; pin the
installed native binary and recheck official documentation before release.
All implementation choices below are ours; external sources support the stated
interfaces and restrictions, not a claim that the code has passed live acceptance.

## Codex / ChatGPT — official app-server route

OpenAI documents app-server login, account status, model listing, native threads,
turns, dynamic tool callbacks, and turn interruption. Managed ChatGPT login is
available through browser and device flows. This packet uses those flows, rather
than extracting tokens from another application's credential files. Experimental
features require negotiation and are a live binary-version gate. Account catalog
and quotas are authoritative for the connected account; “subscription” does not
mean all models, unlimited turns, or unlimited background activity.

Sources:
- https://developers.openai.com/codex/app-server/
- https://learn.chatgpt.com/docs/app-server
- https://developers.openai.com/codex/config-reference/
- https://github.com/openai/codex/tree/7498521d288b9b3b96ffba4eedf089d8d6e06a84/codex-rs/app-server-protocol

Inspected schema facts: function tool specs include `type`, `name`, `description`,
`inputSchema`; callback output uses `contentItems` and `success`. Image content is
`inputImage` with `imageUrl`. The NDJSON app-server transport is JSON-RPC-shaped
but does not carry a `jsonrpc` field. A completed turn is not inferred merely from
an assistant text delta. The implementation negotiates `experimentalApi` for
`dynamicTools`; Terminal Ada must verify this against the installed version.

## Google Antigravity — unmodified native CLI

Google's headless documentation states that a prior interactive `agy` sign-in
supplies cached credentials. Stream JSON supports an initial user message and
structured output including a final result. It does not support inventing generic
control responses for interactive approval requests. The chosen route runs the
native binary; its own host tools and permissions are separate from Lelock's
scoped MCP tools. It is not an API-key export or an OAuth token-reuse plugin.

Sources:
- https://antigravity.google/docs/cli/headless/
- https://antigravity.google/docs/cli/reference/
- https://antigravity.google/docs/mcp/

The exact native permission and MCP behavior must be tested with Kit's installed
binary. A native runtime may have additional configured services; no claim is
made that setting its working directory prevents it from accessing the host.
The explicit `--dangerously-skip-permissions` option belongs to that runtime and
is distinct from the Lelock broker's YOLO mode.

## Claude Code — a significant restriction, not a missing token trick

Anthropic states that third-party developers must not offer Claude.ai login in
their own applications or route requests through Free/Pro/Max subscription
credentials for users. It distinguishes this from a user signing into the
unmodified Claude Code application, including permitted hosted native setups.
Its Agent SDK product integration should use API or supported cloud credentials.
Therefore the supplied Claude route launches native sign-in only. It does not
advertise Claude Account Chat in SillyTavern. Old third-party OAuth plugins are
not used to route around the current restriction.

Source:
- https://code.claude.com/docs/en/legal-and-compliance

A future character handoff to an unmodified native client should preserve its
visible UI, native authentication and native permission system; do not secretly
wrap that as a general-purpose subscription inference endpoint. This packet does
not implement or claim that future full handoff.

## OpenCode — useful, but no need to add another runtime just for Codex login

OpenCode's provider documentation describes ChatGPT Plus/Pro sign-in and other
subscription integrations. It also states that Claude OAuth plugins were removed
from the bundle in 1.3.0 and that Anthropic prohibits such use. The page retains
some inconsistent older wording; current provider rules take precedence over an
old sentence in a third-party setup guide. The packet includes the native
`opencode auth login` launcher, but no OpenCode conversational backend. Adding
one later requires its actual native event, tool and permission contracts.

Sources:
- https://opencode.ai/docs/providers/
- https://opencode.ai/docs/cli/
- https://github.com/anomalyco/opencode

## Hermes — native OAuth support does not propagate into Lelock automatically

The Hermes provider guide documents native provider/auth choices, including
Codex, while Lelock v0.2's inspected adapter explicitly selects its own custom
Chat Completions endpoint and bounded dispatcher. These are different paths.
Do not turn on a second native dispatcher or silently borrow the user's entire
Hermes profile to make login appear to work. The native `hermes model` launcher
is included; the existing pinned runtime stays untouched. The implemented
Codex app-server path supplies the requested API-key-free route independently.

Sources:
- https://hermes-agent.nousresearch.com/docs/integrations/providers
- https://github.com/NousResearch/hermes-agent
- https://github.com/kitfoxs/Lelock-OS/blob/cc153222f201612bb2aea431e6ab73b5b645c0f2/project/src/lelock/runtime.py

## SillyTavern host contract

Official extension and function-calling documentation supports the host context,
function registration, generation interception and extension manifest. Retrieved
`st-context.js` exports the functions used here. Function-call availability still
depends on the selected host API/model. `characterId` is not used as a durable UUID.
The root manifest and local-copy installer are supplied, but the current public
repository must receive this code before its Git URL can install this extension.

Sources:
- https://docs.sillytavern.app/for-contributors/writing-extensions/
- https://docs.sillytavern.app/for-contributors/function-calling/
- https://github.com/SillyTavern/SillyTavern/blob/06bde939fb1e9c4c8d8641d810f0a916b5bce127/public/scripts/st-context.js

## Rakazo — direct computer substrate, not hosted Grok Bots

Rakazo separates an agent runtime from its SandboxProvider computer runtime.
The inspected interfaces expose lifecycle, command, file, screen observation
and action operations. The new code calls that computer layer directly.
Private computers are used because shared Team folders are organizational,
not mutually untrusted-process isolation. The first live backend is Docker;
remote provider persistence and full UI/control leases remain separate gates.

Sources:
- https://github.com/elie222/rakazo/blob/67e3482e04fbd03f02ef46b7d6ea5e0843737a9c/docs/computer-runtime.md
- https://github.com/elie222/rakazo/blob/67e3482e04fbd03f02ef46b7d6ea5e0843737a9c/packages/adapter-kit/src/interfaces.ts
- https://github.com/elie222/rakazo/blob/67e3482e04fbd03f02ef46b7d6ea5e0843737a9c/packages/adapters/src/sandbox-factory.ts
- https://github.com/elie222/rakazo/blob/67e3482e04fbd03f02ef46b7d6ea5e0843737a9c/packages/adapters/src/docker-sandbox.ts

## Reuse and licensing

New bridge, controller, adapter, installer and test code is first-party MIT.
The v0.2 test snapshot is also first-party MIT and is not installed over the
current runtime. Rakazo's inspected license is Apache-2.0; it is imported from
its own checkout, not copied wholesale into the core. No AGPL Tavern source is
vendored. The extension uses documented host APIs. Preserve all donor notices
in the existing repository, and review licenses before copying other projects'
implementation code rather than merely using their ideas.
