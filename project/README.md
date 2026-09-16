# Lelock OS — terminal alpha

A user-controlled companion workspace: choose your companion, bring a supported model, preserve source-linked memories, and create useful things together. Friendship, optional adult romance, study and creativity are welcome. The companion remains recognizable when work begins.

This is an application harness on an existing OS, not a replacement kernel. The bundled reference implementation uses Hermes for inference/tool planning, MemPalace for durable memory, a reviewed SoulTavern V2 parser for card import, and a small deterministic Lelock control plane.

**Status:** 0.1.0a1 reference code with offline tests. Read the actual delivery receipt for installed/live verification. At packet authoring, 86 offline cases and eight static source checks passed; actual Mac/model/Palace gates were not yet run. Not production-ready, not a complete security audit.

## What it does
Terminal conversation; selected profile/identity; explicit memory proposals and corrections; read selected bounded text files; propose and human-approve new text artifacts; preserve session context; checkpoint journal-retention conversations; inspect selected datachips; restore to a blank home; review/activate V2 cards. Exactly five bounded model tools. No arbitrary shell/browser/third-party tool execution.

## Start
Use the full private engineering packet's `00_START_HERE.md` and `docs/BUILD_RUNBOOK.md`. The source snapshots are siblings under `../upstream`. In a prepared tree:
```sh
python3 scripts/bootstrap.py --allow-network
./lelock --help
```
Requires Python 3.11–3.13 and an available `uv` installation; dependencies are isolated using the supplied upstream locks. Model/embedding assets and API credentials are not included. A local endpoint or explicitly selected remote compatible endpoint must be available. See `QUICKSTART.md` and `PRIVACY.md` before storing data.

## Design commitments
A proposal is not execution. Affection is not permission. Missing evidence is not a memory. Fiction is not autobiography. Datachips are inspectable, selected and portable; they do not promise identical behavior across models. A hosted endpoint still processes supplied context remotely. No provider bypasses or universal quality/availability claims.

## License and provenance
New Lelock code is MIT-licensed; retain bundled third-party notices. Source archive inclusion does not make the full **private engineering packet** approved for public release. Its private predecessor history and receipts must not be published by default. Original Lelock concept/authorship: Kit Olivas, developed with Ada Marie. Not affiliated with Halo or its owners.
