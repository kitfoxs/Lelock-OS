# Source contracts and provenance

Accessed/inspected September 15, 2026. This packet uses the **user-supplied archives** listed in `project/resources/source-lock.json`; hashes establish which supplied bytes were inspected, not independent upstream authenticity. Keep relevant upstream licenses in `project/resources/licenses/` and notices in `project/THIRD_PARTY_NOTICES.md`.

## Primary references
- [H1] Hermes repository: https://github.com/NousResearch/hermes-agent
- [H2] Memory provider contract: https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin
- [H3] Plugin mechanisms: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins
- [H4] Security guidance: https://hermes-agent.nousresearch.com/docs/user-guide/security
- [H5] Profiles: https://hermes-agent.nousresearch.com/docs/user-guide/profiles
- [M1] MemPalace repository: https://github.com/MemPalace/mempalace
- [S1] SoulTavern repository: https://github.com/imphillip/SoulTavern

The API shape is verified against supplied source and these official references, not a third-party blog. Documentation can move; do not silently substitute newer APIs for pinned behavior. Runtime compatibility is a separate gate.

## Hermes seam
`agent/memory_provider.py` defines the actual ABC, `spawn_context_thread`, registration and checkpoint-version semantics. The `lelock` setuptools entrypoint is `hermes_agent.memory_providers`. The provider is activated only after a service is bound to the exact isolated Hermes home.

The relevant `run_agent.AIAgent` constructor, `_execute_tool_calls`, `run_conversation`, memory manager/provider lifecycle, and `shutdown_memory_provider` are concrete source references. The dispatch override is intentionally narrow but version-sensitive; a matching text signature does not prove the instantiated agent routes all tools through it. Verify the actual object and calls in the live gates.

## MemPalace seam
`mempalace/mcp_server.py` supplies HTTP transport with dynamic local port, bearer-token handling and registry discovery. The adapter expects tools `mempalace_add_drawer`, `mempalace_get_drawer`, `mempalace_search`, `mempalace_list_drawers`, and `mempalace_delete_drawer`. Search results include `source_path`; get-drawer returns complete logical content, including grouped chunks in the supplied implementation. Do not substitute a truncated search snippet for stored source readback.

## SoulTavern seam
`skills/soultavern/scripts/soultavern/parse.py` is copied exactly under `_vendor/soultavern/` with its license. Lelock adds separate bounded preflight/review/allowlist behavior. This is a derived import path, not a claim that all SoulTavern runtime output or capabilities are adopted. The standalone skills archive duplicates the full project's skills subtree, so it is not installed twice.

## Static assertions
The source-contract script checks eight selected markers: Hermes constructor parameters, dispatch signature, checkpoint API2, provider entrypoint family, Palace RPC names, source-path search field, PID registry field, and dynamic-port support. These detect specific drift, not a whole-code security clearance.

## Private history is excluded here
The original master packet kept the private predecessor and personal research locally. This cloud copy deliberately omits that archive and report. They are not needed to implement the reference code. The private native application is neither included nor modified. Inspecting these source archives does not establish that any private Git history is safe to publish.
