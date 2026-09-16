# Developer quickstart — publication recovery required

All commands below run from the **repository root**. This is not yet a self-contained
consumer installer. Use Python 3.11–3.13, Git, and `uv` installed by an approved method.
Do not test against private Ada memory, an existing Palace, or the native Mac app.

## 1. Current application source

The launch commit omitted `project/src/lelock/`; the corrected ignore rule prevents
recurrence but does not recover files. The maintainer must restore the **current Mac
source**, review it for private material, and commit it. See
[recovery instructions](../docs/SOURCE_RECOVERY.md).

```sh
python3 project/scripts/check_publication.py
python3 project/scripts/verify.py
```

Stop at missing-source errors. Historical code listings and older cloud ZIPs are not
substitutes for the newer implementation. A successful maintenance-only test run is
not application acceptance.

## 2. Exact upstream archives

After source recovery, obtain the original approved source packet from the maintainer.
Place these files in `upstream/` beside `project/`, matching `resources/source-lock.json`:

| Archive | SHA-256 |
|---|---|
| `hermes-agent-2026.9.14.zip` | `c3694a72bf739c76718e31529102f0e4c16f225c2fba0bec3136ba92e127addc` |
| `mempalace-3.9.0.zip` | `8407eb0390bdc8d5a3bba31ce64cd0fda91d8a5a73b5c014995084cd72543bc9` |

These are exact supplied snapshots, not a promise that an upstream tag produces
identical ZIP bytes. **A publicly downloadable pinned source bundle is still a release
blocker.** Do not fetch a moving branch, disable checksum checks, or publish the private
engineering packet wholesale. SoulTavern's reviewed parser is vendored; its original
archive is retained separately for provenance, not required for runtime installation.

```sh
python3 project/scripts/check_publication.py --require-upstream
python3 project/scripts/source_contracts.py
python3 project/scripts/bootstrap.py --allow-network
./project/lelock --help
```

`--allow-network` authorizes locked package installation; it does not download the
source archives, select a model, configure billing, or publish anything.

## 3. Synthetic local acceptance

Read `./project/lelock init --help` from the recovered source before selecting a blank
home/workspace and a real supported model endpoint. The original CLI puts the global
`--home PATH` **before** its subcommand; verify that interface against the current code.
Do not copy a guessed `--companion` option or pretend an example local model is installed.

Run the actual Palace, chosen-model, full-stack/restart, and human gates in
[the acceptance matrix](../docs/ACCEPTANCE_MATRIX.md). API credentials stay out of source,
command histories, exports, and logs. Consumer coding subscriptions do not automatically
fund companion inference.

Card/lore import, companion selection, and `serve` require the recovered newer code
and fresh evidence. Until then, the [SillyTavern extension](../integrations/sillytavern/README.md)
is experimental. Plaintext selected datachips are not encrypted or complete backups.
