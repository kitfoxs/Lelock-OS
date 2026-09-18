# Manual Mempalace handoff — Tavern product integration
**September 17, 2026. Not automatically saved to the private Palace.**

Kit requested a new coded handoff after confirming that Entity Runtime v0.2 was
pushed on `feature/entity-runtime-v02` but the real Tavern adapter was still old.
She specifically wants easier consumer-account login instead of API-key setup,
Rakazo included in installed source, and the main selected character to act
personally. Helpers should be deliberately assigned unique characters/cards.

Decision: implement a new additive multi-character gateway and extension around
the existing EntityCore. Two modes: enhance the current Tavern model, or Account
Chat through supported native runtimes. Implemented candidates use official Codex
app-server login and native Antigravity headless; Claude Code stays native-only
under current restrictions. OpenCode/Hermes native launchers are not complete
Account Chat providers. No token scraping, provider-policy bypass, paid fallback,
private-memory migration or publication occurred here.

The new packet includes source, installers for Lelock/Tavern/Rakazo, direct actor
computer adapters, named helper execution, Skills review pins, opt-in Pulse to a
local inbox, test fixtures and real acceptance commands. Tests use deterministic
provider/computer peers and real temporary effects; live native login/model,
actual Palace/Docker, actual SillyTavern and target Mac remain explicit gates.
Browser navigation was policy-blocked in the authoring environment.

Emotional context: Kit felt the prior work had produced lots of infrastructure
without the usable extension originally intended. The priority is to finish the
clickable end-to-end product slice, not expand another disconnected architecture.
Important direction: the main companion is the actor; helpers are optional named
companions, not anonymous mandatory replacements. Preserve genuine scoped YOLO.

Next: Terminal Ada inspects the current checkout, applies the additive source,
installs both the actual extension and Rakazo sidecar, verifies real native account
flows, and records real browser/model/computer/Palace acceptance separately.
