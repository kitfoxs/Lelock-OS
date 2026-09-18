# Sources, provenance, and licensing
**Checked September 17, 2026. Architecture beyond the source facts below is this packet's proposed design.**

## Lelock baseline

These links pin the inspected revision. The repository was read through the connected GitHub tool; a container clone failed because that environment could not resolve GitHub. New foundation code was authored locally. No private repository content or live Palace was copied into the packet.

- **L1 — repository and current public scope:** [README](https://github.com/kitfoxs/Lelock-OS/blob/c3b2bc6e6b211709be91e640568d0a503a41ffb7/README.md). The original publication lists 102 application and 12 maintenance tests; those are baseline reports, not reruns in this delivery.
- **L2 — original architecture and exclusions:** [MASTER_BLUEPRINT.md](https://github.com/kitfoxs/Lelock-OS/blob/c3b2bc6e6b211709be91e640568d0a503a41ffb7/MASTER_BLUEPRINT.md).
- **L3 — bounded runtime seam:** [runtime.py](https://github.com/kitfoxs/Lelock-OS/blob/c3b2bc6e6b211709be91e640568d0a503a41ffb7/project/src/lelock/runtime.py).
- **L4 — memory and deterministic Service:** [service.py](https://github.com/kitfoxs/Lelock-OS/blob/c3b2bc6e6b211709be91e640568d0a503a41ffb7/project/src/lelock/service.py) and [journal.py](https://github.com/kitfoxs/Lelock-OS/blob/c3b2bc6e6b211709be91e640568d0a503a41ffb7/project/src/lelock/journal.py).
- **L5 — owned MemPalace transport/lifecycle:** [palace.py](https://github.com/kitfoxs/Lelock-OS/blob/c3b2bc6e6b211709be91e640568d0a503a41ffb7/project/src/lelock/palace.py).
- **L6 — source selection and instructions:** [source-lock.json](https://github.com/kitfoxs/Lelock-OS/blob/c3b2bc6e6b211709be91e640568d0a503a41ffb7/project/resources/source-lock.json) and [AGENTS.md](https://github.com/kitfoxs/Lelock-OS/blob/c3b2bc6e6b211709be91e640568d0a503a41ffb7/AGENTS.md). Preserve actual pinned archives instead of moving to a current upstream branch.

The five patch preimages are recorded as Git blob SHA-1 values in `patches/changes.json`. The handoff does not bundle the existing application's full source or dependency archives. Retrieve those through the project's established source-verified process on the target machine.

## Protocol references

- **M1 — official MCP Python SDK and migration:** [SDK repository](https://github.com/modelcontextprotocol/python-sdk), [v2 migration guide](https://py.sdk.modelcontextprotocol.io/migration/). Current docs identify SDK 2.x and the `MCPServer` rename. The included adapter follows that documented API but has not been run against an installed SDK in this environment.
- **M2 — MCP security guidance:** [Security best practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices). Used for the authentication/transport threat model, not a claim that this reference bridge is MCP-certified or production-audited.
- **M3 — MCP authorization guidance:** [Authorization](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/authorization). Remote OAuth design is future integration work; the packet's bridge is local bearer pairing, with a stdio MCP client-facing adapter.

## Design references, not copied implementations

- **Psycheros:** [repository](https://github.com/PsycherosAI/Psycheros). Its canonical entity-core, consolidation hierarchy and Pulse mechanisms motivate separated identity/continuity and event-driven work. Lelock retains MemPalace rather than importing a competing canonical store. The project uses MPL-2.0; no implementation files were copied here.
- **TauriTavern:** [repository](https://github.com/Darkatse/TauriTavern), [official documentation](https://tauritavern.github.io/en/). The native client and agent Skills/workspace/timeline concepts motivate UI and tool-flow requirements. This packet does not assert complete frontend/plugin equivalence or borrow its AGPL implementation.
- **Letta:** [current source](https://github.com/letta-ai/letta-code). Stateful agents, lifecycle, Skills and channels are useful reference concepts. Lelock does not replace Hermes or MemPalace with Letta. Check the license of the exact file/revision before any future code reuse.
- **Chronicler:** [repository](https://github.com/yantrikos/chronicler). Memory tiers and per-record visibility motivate the derived-memory view. Evidence validation here is not a claim to reproduce or benchmark its entire memory engine. No source was copied.
- **SillyBunny:** [repository](https://github.com/SillyBunnyTeam/SillyBunny). Pre/main/post companion processing is retained as a design direction from the earlier comparison, not a verified import or new dependency in this delivery.
- **Hermes:** [upstream](https://github.com/NousResearch/hermes-agent). Consult current documentation for context, but the integration target is the existing pinned Lelock archive, not an automatic latest upgrade.

## Licensing policy

The new first-party reference files are supplied under the included MIT license. They were authored for this handoff rather than pasted from peer projects. Existing Lelock and upstream notices remain intact; this packet does not relicense dependencies or erase their obligations.

Do not copy AGPL-covered Tavern code into the core and then label the entire result MIT without reviewing the resulting obligations. Do not treat “open source” as “no conditions.” MPL-covered code also has file-level requirements; consult the [official Mozilla MPL FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) and the exact notices before reuse. Separate API integration and original implementation are the chosen approach here, not a blanket legal conclusion about every possible combined work.

## Evidence boundaries

Only logs in `evidence/` establish what ran in this container. Peer READMEs establish project-described features, not performance, security or maturity rankings. The code's passing tests establish tested behavior with synthetic fixtures, not every possible input or live dependency. Report unresolved failures and missing access without converting them into success claims.
