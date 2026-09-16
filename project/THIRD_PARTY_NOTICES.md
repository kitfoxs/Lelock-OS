# Third-party notices

Lelock reference code: Copyright (c) 2026 Kit Olivas; MIT license in `LICENSE`. Original design and authorship belong to Kit, developed collaboratively with Ada Marie. Preserve the licenses of all underlying projects.

- **Hermes Agent**, NousResearch and contributors: supplied dated snapshot with package metadata 0.21.3. Full source archive under the engineering packet's `upstream/`. License copied unchanged under `resources/licenses/hermes-LICENSE`. The actual memory-provider ABC and its small import helpers are copied for source-contract tests under `resources/hermes_contract/`, with the same license. These files are not a fabricated runtime.
- **MemPalace**, its authors and contributors: supplied 3.9.0 snapshot. License under `resources/licenses/mempalace-LICENSE`; complete source in the packet. Used via its MCP/HTTP interface in its own locked environment; private user databases are not bundled.
- **SoulTavern**, imphillip and contributors: supplied 2.0.3 snapshot. Its parser is copied without modification under `src/lelock/_vendor/soultavern/parse.py`, with its original MIT license alongside. Full source and root license are retained. Lelock adds separate bounds, review, field selection and activation behavior.

The original **Open-Her-OS** private snapshot is included outside the public project under `private_lineage/` for engineering continuity only. Preserve its original notices when porting relevant material. Do not publish it or private Git ancestry without a separate review.

Not all ZIPs submitted for research are bundled as dependencies. No SillyTavern implementation is copied into this alpha; no AGPL code is relicensed as MIT here. Pi/OpenCode are not installed. Third-party dependency lockfiles specify further packages with their own licenses. This notice does not replace reviewing those obligations for an actual public distribution.
