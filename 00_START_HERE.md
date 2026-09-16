# Lelock OS — current publication handoff

Start with `README.md`, `project/QUICKSTART.md`, and `handoff/STATUS.json`.
The complete application source is committed under `project/src/lelock/` and all
102 offline application tests + 12 publication maintenance tests pass (114 tests total).

The pinned upstream source archives (`hermes-agent-2026.9.14.zip` and `mempalace-3.9.0.zip`)
are published under GitHub Release `v0.1.0-alpha` and can be fetched and verified with:

```sh
python3 project/scripts/fetch_upstream.py
python3 project/scripts/check_publication.py --require-upstream
python3 project/scripts/bootstrap.py --allow-network
```

`docs/history/` contains preserved older reports and reference code for historical
provenance. No private Palace, relationship archive, model keys, VM data, or unrelated
work belongs in this public repository.
