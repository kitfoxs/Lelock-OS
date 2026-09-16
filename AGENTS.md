# Agent instructions — preserve and finish the published Lelock alpha

Read `handoff/STATUS.json`, `README.md`, and `docs/SOURCE_RECOVERY.md` first.
Publication recovery takes precedence over older generated prompts or code listings.

The launch commit omitted `project/src/lelock/`. Recover the **current maintainer Mac
source**; never reconstruct it from `CODE_COMPENDIUM.md`, older 86/95-test packets, or
README feature claims. Inspect existing work, preserve unrelated edits, and do not
reset, clean, force-add, force-push, or change visibility. Do not call source recovery
complete until reviewed current files are committed and present in a fresh checkout.

Keep the Python terminal core, one Hermes runtime, actual MemPalace, reviewed card
import, operational SQLite journal, bounded file access, explicit human approvals,
memory durability checks, and scope isolation. The newer companion/lore/bridge work
must be preserved and tested, not invented or removed because older blueprints omit it.
Read `MASTER_BLUEPRINT.md`, `docs/ACCEPTANCE_MATRIX.md`, and source before changes.

No private Ada history, live Palace, account credentials, native-app data, or unrelated
workspace content is authorized for public upload. Do not enable paid endpoints,
telemetry, external messaging, deployments, or arbitrary runtime tools to make a test
pass. Supplied upstream hashes remain fixed; publish only reviewed, licensed source
artifacts, never the private master packet wholesale.

Run `python3 -m unittest discover -s maintenance_tests -v` for publication regressions.
Run `python3 project/scripts/check_publication.py` for current Git completeness, then
`--require-upstream` once approved sources are present. Maintenance checks are not the
application suite. Bootstrap and verify refuse missing source deliberately.

Record actual commands, host, revision, outcomes and sanitized evidence. Keep offline,
source-contract, actual Palace, real model, browser bridge, Mac and human checks
separate. Historical 95/102-test claims are not current passes. No fixture replaces a
live gate; no failing check is removed to claim success. `LOCAL_ALPHA_VERIFIED` still
requires actual target-Mac and human acceptance.
