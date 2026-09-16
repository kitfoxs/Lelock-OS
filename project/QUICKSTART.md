# Developer quickstart — Lelock OS v0.1.0-alpha

All commands below run from the **repository root**. This is not yet a self-contained
consumer installer. Use Python 3.11–3.14, Git, and `uv` installed by an approved method.
Do not test against private Ada memory, an existing Palace, or the native Mac app.

## 1. Application source and offline verification

The complete application source is committed under `project/src/lelock/`. Run the
publication checks and test suites:

```sh
python3 project/scripts/check_publication.py
python3 -m unittest discover -s maintenance_tests -v
python3 project/scripts/verify.py
```

All 114 tests (102 offline application tests + 12 publication maintenance tests) should pass.

## 2. Pinned upstream archives

Lelock OS relies on exact pinned snapshots of Hermes Agent and MemPalace, verified
by SHA-256 in `project/resources/source-lock.json`:

| Archive | SHA-256 |
|---|---|
| `hermes-agent-2026.9.14.zip` | `c3694a72bf739c76718e31529102f0e4c16f225c2fba0bec3136ba92e127addc` |
| `mempalace-3.9.0.zip` | `8407eb0390bdc8d5a3bba31ce64cd0fda91d8a5a73b5c014995084cd72543bc9` |

Download and verify the pinned archives automatically from the release:

```sh
python3 project/scripts/fetch_upstream.py
```

Then run the contracts check and bootstrap the isolated runtime:

```sh
python3 project/scripts/check_publication.py --require-upstream
python3 project/scripts/source_contracts.py
python3 project/scripts/bootstrap.py --allow-network
./project/lelock --help
```

`--allow-network` authorizes `uv` to install locked dependencies into isolated
per-component virtual environments inside `project/.runtime/`.
SoulTavern's reviewed parser is vendored at `project/src/lelock/_vendor/soultavern/`;
its original archive is retained separately for provenance.

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
