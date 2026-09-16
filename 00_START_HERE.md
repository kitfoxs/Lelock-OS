# Lelock OS — current publication handoff

Start with `README.md`, `handoff/STATUS.json`, `AGENTS.md`, and
`docs/SOURCE_RECOVERY.md`. The launch at `0cbd55e` accidentally omitted the current
Python package. This repair does not reconstruct that package from older material.

The current maintainer Mac source is authoritative for application recovery. Run
`python3 project/scripts/check_publication.py` in a fresh checkout after it is committed.
The checker is expected to fail until the source exists **in Git**, not just on one Mac.

`docs/history/` contains preserved older reports and reference code; their successful
tests are not fresh results and their source must not overwrite newer work. The
original architecture/acceptance documents remain useful but are not proof of a build.
No private Palace, relationship archive, model keys, VM data, or unrelated work belongs
in this public repository.
