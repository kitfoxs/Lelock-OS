# Next action

Stage: cloud implementation complete. **Target-Mac acceptance not started.**

This packet has **not** earned `LOCAL_ALPHA_VERIFIED`. That label requires the target Mac,
a real model endpoint, and the human-experience gates, none of which exist in the cloud
environment this work was done in.

## What was actually run here

Linux 4.19.0-gvisor x86_64, CPython 3.13.12, uv 0.9.29. Synthetic data only. No private
Ada history, no private Palace, no unrelated account, and no native Mac application was
read. No model endpoint was contacted. No billing, deployment, or publish action occurred.

Fresh results: `receipts/offline-result.json`, `receipts/source-contracts.json`,
`receipts/dependency-install.json`, `receipts/live-palace.json`,
`receipts/real-stack-no-model.json`, `receipts/cli-offline-smoke.json`.

Two defects were found and fixed, both regression-tested: see `LELOCK_BUILD_REPORT.md`
(D1 symlinked-parent workspace escape, D2 `private_dir` leaf-link acceptance).

## Before you install on the Mac

Restore the two required upstream archives beside `project/`, because they are excluded
from the delivered ZIP:

```
<packet-root>/upstream/hermes-agent-2026.9.14.zip    sha256 c3694a72bf739c76718e31529102f0e4c16f225c2fba0bec3136ba92e127addc
<packet-root>/upstream/mempalace-3.9.0.zip           sha256 8407eb0390bdc8d5a3bba31ce64cd0fda91d8a5a73b5c014995084cd72543bc9
```

`upstream/SoulTavern-2.0.3.zip` (sha256 `4fdc4e1d1e555ea7748b797ddf79cee0806323ddc1ba09fe2440a7937f4a7b7b`)
is **not** needed to install: the reviewed MIT parser is already vendored at
`project/src/lelock/_vendor/soultavern/`. Restore it anyway to keep `source-lock.json`
provenance complete.

`project/resources/source-lock.json` is unchanged. Do not substitute a moving branch for
any of these.

## Exact commands on the target Mac

```sh
cd <packet-root>
shasum -a 256 upstream/*.zip          # must match source-lock.json before anything else

python3 -V                             # must be 3.11, 3.12 or 3.13
python3 project/scripts/verify.py
python3 -m compileall -q project/src project/scripts project/tests
python3 project/scripts/source_contracts.py

# uv must already be present by an approved official method
python3 project/scripts/bootstrap.py --allow-network
./project/lelock --help

python3 project/scripts/live_palace_probe.py                       # S3, no model needed
LELOCK_PROJECT="$PWD/project" \
  ./project/.runtime/hermes/.venv/bin/python receipts/logs/real_stack_no_model.py   # optional re-check

# S4/S5 need an endpoint and model you explicitly choose. Nothing here picks one for you.
python3 project/scripts/live_model_probe.py --endpoint <URL> --model <NAME> --label A
python3 project/scripts/live_full_stack_probe.py --endpoint <URL> --model <NAME> --label A
```

Then work the synthetic manual script in `docs/ACCEPTANCE_MATRIX.md` for A08, A14, A16 and
the macOS half of A04 and A15, and record each by its acceptance ID.

## Do not

Do not mark a gate PASS from a historical receipt. Do not replace a live integration with a
fixture to get a green result. Do not delete a failing test. Do not treat the cloud results
below as Mac results.
