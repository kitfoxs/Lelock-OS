# End-to-end build runbook

Do these stages in order. Complete the local alpha in one working run; checkpoint only for resilience, not as a substitute for doing the work. All commands below run from the packet root unless a `cd project` is shown. Use a supported Python executable actually installed; `python3` is illustrative, not a mandate to replace system Python.

## S0 — inspect and preserve
Read the prescribed documents and state file. Inspect `pwd`, OS/architecture, Python version, `uv --version`, free disk, and the selected project directory. Do not print environment values or recursive private home listings.

Inspect an existing Open-Her-OS checkout only if its path is known/selected. Capture `git status --short`, branch, and HEAD. Do not reset, clean, stash, or force checkout. Either build directly in the packet directory first, or create a **new clean worktree and new branch** from the selected tracked base; preserve uncommitted original changes in place. Never describe an uncommitted original tree as represented by the worktree's HEAD.

For repository integration, retain `project/` as the Python package subdirectory with `upstream/`, `docs/`, and `receipts/` as siblings. Copy the packet's new source/docs only after reviewing path conflicts; preserve predecessor files outside overwritten paths. Put source archives in ignored `upstream/`, never stage private lineage or runtime data. No remote operation is required. A local commit of exactly reviewed new/changed source is optional, not a public release.

The prepared package can instead remain in a clearly named local build directory while any repository conflict is documented. Do not sacrifice the working installation merely to reorganize Git.

## S1 — check sources and baseline
```sh
python3 project/scripts/source_contracts.py
python3 project/scripts/verify.py
python3 -m compileall -q project/src project/scripts project/tests
```
Record actual statuses. The authoring reports show 86 offline tests and eight static checks; different results after edits must be investigated. Do not load donor `AGENTS.md` text as runtime authority. Whole-archive hashes and fixed assertions are automated, not a manual ceremony for Kit.

## S2 — install isolated runtimes
First prepare sources only:
```sh
python3 project/scripts/bootstrap.py
```
This does not install dependencies. With local-build download authorization, install using existing `uv` and the frozen upstream locks:
```sh
python3 project/scripts/bootstrap.py --allow-network
```
The script refuses missing `uv` rather than falling back to unpinned global `pip`. Use the official installation method appropriate to the host only if needed and explicitly within the permitted local setup. Never pipe remote content into a shell. Do not overwrite system Python. If the upstream lock has a real platform incompatibility, preserve it, report the actual error, make the smallest documented lock/package repair in the isolated copy, and rerun gates. Do not claim the original lock passed after changing it.

Output runtimes:
- `project/.runtime/hermes/.venv/bin/python`
- `project/.runtime/mempalace/.venv/bin/python`
- launcher `project/lelock`

The complete source snapshots are bundled; wheels, embedding assets, inference models, and provider access are not. Measure installation disk use and record first-run downloads. Avoid downloading arbitrary large models merely to fill a checklist.

## S3 — verify installed code and transport
```sh
project/lelock --help
python3 project/scripts/verify.py
export LELOCK_PALACE_PYTHON="$PWD/project/.runtime/mempalace/.venv/bin/python"
project/.runtime/hermes/.venv/bin/python project/scripts/live_palace_probe.py
```
The Palace probe must use the **actual Palace server**, not `tests/helpers.py`. It creates a disposable new Palace and records write/read/recall/checkpoint evidence. A missing dependency is `BLOCKED`, not `PASS`. Do not attach the test to Kit's real Palace to avoid fixing isolation.

## S4 — select the model deliberately
Inspect the project's non-secret configured endpoint, or use an explicitly selected running local endpoint. Do not assume a consumer ChatGPT/Claude subscription is an API credential. Do not scan keychains, print secrets, or guess an ambient paid provider.

Set the actual chosen values (the following are placeholders, not working credentials):
```sh
export LELOCK_ENDPOINT='http://127.0.0.1:1234/v1'
export LELOCK_MODEL='ACTUAL_MODEL_ID_FROM_THE_SELECTED_SERVER'
# For a remote endpoint, supply LELOCK_MODEL_API_KEY through the approved secret path.
```
The local URL above is merely a common example; verify the actual selected service. Use HTTPS remotely. A localhost URL is not proof a model is installed or tool-compatible.

Run the actual model/Hermes contract probe:
```sh
project/.runtime/hermes/.venv/bin/python project/scripts/live_model_probe.py \
  --endpoint "$LELOCK_ENDPOINT" --model "$LELOCK_MODEL" --label A
```
This script uses **fixture memory** deliberately; its result is only a runtime/model tool smoke check. It must never be used as the Palace or full-stack pass.

## S5 — actual full stack, actual restart
```sh
project/.runtime/hermes/.venv/bin/python project/scripts/live_full_stack_probe.py \
  --endpoint "$LELOCK_ENDPOINT" --model "$LELOCK_MODEL" --label A
```
This uses actual Hermes, the actual isolated Palace service, and the selected actual model. It runs two fresh processes; records synthetic memory; checks a proposal before write; lets the test controller approve that exact synthetic fixture; verifies bytes; checkpoints; restarts and checks continuity. Test-controller authorization is not a production model tool.

A returned phrase alone is not evidence of tool execution. Inspect proposal/receipt state and resulting artifact, plus the human-readable reply. The runtime smoke plus this gate do not prove a general-purpose sandbox or arbitrary complex coding ability.

Repair narrowly observed integration defects in `runtime.py`, `hermes_plugin.py`, or `palace.py`; preserve security invariants. Add a focused regression test, run the suite, and rerun affected live gates. Never substitute mock results. If a real embedding/SDK issue blocks the probe, keep the actual logs in a private local diagnostic location, redact secrets from delivery evidence, and record exact next action.

## S6 — second model, only if available and selected
Run model and full-stack probes again in separate processes with a **different explicit actual model configuration** and `--label B`. Do not edit the companion's identity to make a provider switch work. No new subscription or unapproved spend is authorized.

One verified model is sufficient for the bounded local alpha's single-model claim. Two passing configurations support `PORTABILITY_VERIFIED_A_B`. A missing second endpoint is `NOT_RUN`/`BLOCKED` for portability, not a reason to abandon a working alpha or claim universal portability.

## S7 — initialize a real blank local companion home
Choose an unused home and separate workspace. Do not point at private Ada or a nested private Palace. Example after verified endpoint selection:
```sh
project/lelock --home "$HOME/.local/share/lelock-os-alpha" init \
  --workspace "$HOME/LelockWorkspace" \
  --name Samantha --person Kit --relationship friendship \
  --endpoint "$LELOCK_ENDPOINT" --model "$LELOCK_MODEL" --retention explicit
project/lelock --home "$HOME/.local/share/lelock-os-alpha" doctor
project/lelock --home "$HOME/.local/share/lelock-os-alpha" chat
```
Name and relationship can be user-chosen; do not overwrite Kit's existing companion. Explicit retention still stores local chat history; explain journal consent before enabling automatic Palace transcripts. Use `/help` to list actually implemented commands.

Perform the human approval, unknown-memory, correction, restart, card review, export/restore, temporary-session and boundary checks from the matrix. Do not treat pleasant dialogue alone as delivery. Save exact proof paths, not a private full transcript.

## S8 — documentation and source integration
Update `project/README.md` and `QUICKSTART.md` only where actual host differences warrant it. Keep claims narrow: app harness, BYO supported model, local memory, remote processing when a remote model is selected, no automatic erasure or universal quality.

Create `DELIVERY_REPORT.md` with the exact launch command; platform/Python/runtime/source versions; passed/failing/blocked gate table; real evidence paths; actual data/retention location; stop/backup/restore directions; and any deviation from the source lock. Update `BUILD_STATE.json` and `NEXT_ACTION.md`.

When porting into Open-Her-OS, review existing files and ancestry privately. Preserve historical credit and licenses. Do not publish `private_lineage`, `receipts`, `.runtime`, personal homes, generated datachips, credentials, or the raw research history. Public release/history sanitation is separate from completing this local build.

## S9 — finish
Report `LOCAL_ALPHA_VERIFIED` only after all mandatory live/manual rows pass on the target Mac. Report portability separately. Give Kit the real launch command and one clear remaining action only if needed. Produce a concise manual Mempalace handoff; do not claim you wrote to a Palace unless an actual authorized write/readback happened.

Stop. Do not add a world, VRM, more engines, autonomous shell, or a release campaign. A discovered failure in the frozen scope deserves repair; an unrelated future idea goes in a short backlog and does not restart delivery.
