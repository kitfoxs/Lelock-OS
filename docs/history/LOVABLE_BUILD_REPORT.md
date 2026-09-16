# Lelock OS terminal alpha — build report

Version `0.1.0a1`. Work performed in a Lovable cloud sandbox: **Linux 4.19.0-gvisor x86_64,
CPython 3.13.12, uv 0.9.29**. Synthetic data only.

> **This packet is not `LOCAL_ALPHA_VERIFIED`.** That label needs the target Mac, a real
> model endpoint, and the human-experience gates. None of the three existed here, and none
> of them is claimed below. Historical receipts shipped in the packet were treated as
> baseline history and re-run rather than trusted.

---

## 1. What changed

Three first-party source files. Nothing else in `project/` was touched, and
`project/resources/source-lock.json` is **unchanged**.

| File | Change | Lines |
|---|---|---|
| `project/src/lelock/workspace.py` | D1 — symlink refusal enforced in code instead of delegated to one kernel flag | rewrote `_descend`, hardened `read()`, added `_same_inode` |
| `project/src/lelock/common.py` | D2 — `private_dir` proves the leaf is a real directory via a descriptor, and applies permissions with `fchmod` | `private_dir` only |
| `project/tests/test_core.py` | 9 new regression tests (5 for D1, 4 for D2), 3 new imports | +~45 |

Full unified diff: `receipts/logs/lelock-source.patch`.

Generated artifacts (`project/.runtime/`, `project/lelock`, `*.egg-info`, `__pycache__`) are
excluded from the ZIP; `bootstrap.py` recreates them.

No new dependency, module, framework, GUI, daemon, or runtime shell path was added. No test
was deleted or weakened, and no integration was replaced with a mock.

---

## 2. Defects found and fixed

### D1 — Workspace symlinked-parent escape (high)

**Found by** the packet's own offline suite: `test_symlink_parent_denied` failed on the
baseline run, 1 of 86.

`workspace.py` relied on a single `os.open(..., O_DIRECTORY|O_NOFOLLOW)` to refuse symlinked
directories. On this gVisor 4.19 kernel that open **does not** return `ELOOP` for a symlinked
directory — it follows the link. Reading `linked/config.json`, `linked/SOUL.md` and
`linked/operations.sqlite3` from outside the workspace all succeeded, and an approved write
would have landed outside the workspace too.

**Fix.** Refusal no longer depends on one flag behaving the same way on every kernel. Each
path component is `lstat`-checked (rejecting symlinks and non-directories), opened with
`O_DIRECTORY|O_NOFOLLOW`, and then confirmed to be the same `(st_dev, st_ino)` the `lstat`
reported. The root descriptor is inode-verified as well, and `read()` re-checks the final
component. `create()` keeps `O_EXCL|O_NOFOLLOW`, which does correctly reject an existing
symlink with `EEXIST` here; `validate_new()` is unchanged.

**Tests.** `test_symlink_parent_nested_denied`, `test_symlink_parent_create_denied`,
`test_symlink_parent_proposal_denied`, `test_symlink_parent_denied_in_code_not_prompt`, plus
the original `test_symlink_parent_denied`. All five fail against the original `workspace.py`
and pass against the repaired one. Denial happens at proposal time, not only at approval, and
the model-facing dispatcher returns `ok: false` rather than merely advising against it.

### D2 — `private_dir` accepted a symlinked leaf and chmod'd the link target (medium)

**Found by** an automated source review, then confirmed by direct execution.

```python
if path.is_symlink(): raise ...
path.mkdir(parents=True, exist_ok=True, mode=0o700)
os.chmod(path, 0o700)
```

`Path.mkdir(exist_ok=True)` swallows the error for an existing symlink-to-directory, because
its fallback `is_dir()` resolves the link; `os.chmod` by path follows it as well. The
non-atomic pre-check was therefore the only guard. `private_dir` gates the application home,
`palace/`, `runtime/`, `cards/`, `exports/`, `identity-history/` and the workspace root, so
a redirected leaf would send private data somewhere else and relax the target's permissions.

**Fix.** After `mkdir`, the directory is opened and the descriptor compared against `lstat`
by `(st_dev, st_ino)`; permissions are applied with `fchmod` through that descriptor rather
than by path — the same belt-and-braces pattern as D1, which matters because `O_NOFOLLOW`
alone is unreliable on this kernel.

**Deliberate boundary.** Symlinked **ancestors** stay permitted, and
`test_symlinked_ancestor_still_allowed` pins that. macOS `/tmp` and `/var` are themselves
symlinks, so refusing ancestors would break the acceptance target. Only the leaf is
constrained, which is exactly what the function's own error message promises.

**Tests.** `test_plain_directory_created_private`, `test_idempotent_on_existing_directory`,
`test_symlinked_leaf_refused`, `test_symlinked_leaf_refused_when_precheck_is_evaded`,
`test_symlinked_ancestor_still_allowed`. The evaded-pre-check test fails against the original
file and passes against the repaired one, and asserts the link target's mode is untouched.

### Reviewed and deliberately left alone

- **`Journal.finish()` has no `WHERE state='applying'` guard**, unlike `reject()`. Its only
  caller goes through `claim()`, which does `BEGIN IMMEDIATE` plus a pending-state check in
  one transaction, so single-use approval holds. Correct code was not rewritten for
  appearance; it is recorded here so a future second caller triggers a re-check.
- **A test of mine asserted fiction could be stored in a personal-scope home.** The product
  was right and the test was wrong — `make_record` refuses `kind='fiction'` outside
  `scope='fiction'`. The check now asserts the refusal.

---

## 3. Acceptance matrix

Statuses are by the original IDs in `docs/ACCEPTANCE_MATRIX.md`. Every PASS below comes from
a command run in this environment; none is inherited from a shipped receipt.

| ID | Status | Basis |
|---|---|---|
| A01 | **PASS** | Isolated copy; upload left byte-identical; archive scanned for unsafe paths/links before extraction. No private Ada history, Palace, account or native Mac app read. |
| A02 | **PASS** | `source-contracts.json` 8/8; all three archive sha256 match an unchanged `source-lock.json`. |
| A03 | **PASS** | 95 tests, 0 failures, **0 skipped**, exit 0 (`offline-tests.log`). Baseline was 86 with 1 failure. |
| A04 | **PARTIAL** | Frozen install + CLI pass on cloud Linux/3.13.12. The assertion names the target Mac — macOS is NOT_RUN. |
| A05 | **PASS** | `live-palace.json`: real MemPalace add/get/search/checkpoint on a synthetic new home. |
| A06 | **BLOCKED** | Needs a real model endpoint; external inference was not authorized. |
| A07 | **BLOCKED** | Depends on A06. |
| A08 | **NOT_RUN** | Human-observed approval/rejection gate. |
| A09 | **PARTIAL** | Correction supersedes the earlier active fact on a real Palace; fiction refused outside fiction scope; personal recall returns no fiction content. "Unknown answer admits no evidence" needs a model turn. |
| A10 | **PARTIAL** | A separate process recalls the stored fact; selected identity and memory survive restart and a card activation. "Without claiming omitted facts" needs a model turn. |
| A11 | **PASS** | Real constructed runtime exposes exactly five bounded functions and no approval tool. `terminal`, `shell`, `bash`, `approve`, `lelock_approve`, `web_search`, `read_file` all denied. `../`, absolute, dotfile and symlinked-parent paths denied **in code**, leaking nothing. Hostile V2 card's `system_prompt`, `post_history_instructions`, `character_book`, `extensions` ignored at import. |
| A12 | **PASS** | Offline failure tests **plus** bounded injection against the installed adapter: failing transport raises instead of acknowledging persistence, pending entry retained, recovery flush clears it only after a successful readback. |
| A13 | **PASS** | Card staged inert; activation refused without `--approve`; activation reports `permissions_changed: false` and leaves the surface at five; prior identity kept in `identity-history/`; datachip exported and restored into a blank home with an independently chosen endpoint; artifact holds no endpoint key, credential or raw transcript. |
| A14 | **NOT_RUN** | Temporary-session behaviour needs a chat turn; depends on A06. |
| A15 | **PARTIAL** | Second process refused the home lock; lock reusable after the owner exits. Stop/cancel and owned-child cleanup during an interactive run, on macOS, outstanding. |
| A16 | **NOT_RUN** | Human review gate. |
| A17 | **BLOCKED** | Needs a second distinct model endpoint. |
| A18 | **NOT_AUTHORIZED** | Public-release review is out of scope for this work. |

Supporting receipts: `offline-result.json`, `offline-tests.log`, `source-contracts.json`,
`dependency-install.json`, `live-palace.json`, `real-stack-no-model.json`,
`cli-offline-smoke.json`, `logs/dependency-install.log`, `logs/lelock-source.patch`.

### Evidence classes, kept separate

| Class | Ran? | Covers |
|---|---|---|
| Offline fixtures | yes | A03, parts of A11/A12 |
| Static source checks | yes | A02 |
| Real Palace, no model | yes | A05, A13, parts of A09/A10/A12/A15 |
| Real Hermes runtime constructed, no model turn | yes | A11 tool surface and dispatch denials |
| Real model | **no** | A06, A07, A14, A17 |
| Full-stack restart with a model | **no** | A07 |
| Target Mac / human | **no** | A04 (macOS half), A08, A15 (interactive half), A16 |

---

## 4. Remaining blockers

**B1 — model endpoint.** Blocks A06, A07, A14, A17. Needs an endpoint and model name you
explicitly select, plus authorization to contact it. Nothing in the packet picks one. A local
endpoint needs no API key; a remote one reads the environment variable named in config.

**B2 — the target Mac.** Blocks the macOS half of A04 and A15, and A08/A16 entirely. Apple
Silicon wheel availability for the frozen locks is unproven from Linux.

**B3 — upstream archives.** Two archives are excluded from the ZIP for size and must be
restored beside `project/` before installing:

```
upstream/hermes-agent-2026.9.14.zip   sha256 c3694a72bf739c76718e31529102f0e4c16f225c2fba0bec3136ba92e127addc
upstream/mempalace-3.9.0.zip          sha256 8407eb0390bdc8d5a3bba31ce64cd0fda91d8a5a73b5c014995084cd72543bc9
```

`upstream/SoulTavern-2.0.3.zip` (`4fdc4e1d1e555ea7748b797ddf79cee0806323ddc1ba09fe2440a7937f4a7b7b`)
is **not** required to install — verified by removing it and re-running both
`source_contracts.py` and a card import successfully, because the reviewed MIT parser is
already vendored at `project/src/lelock/_vendor/soultavern/` with its LICENSE. Restore it
anyway to keep `source-lock.json` provenance complete.

### One recorded deviation

`bootstrap.py` requires `uv` and correctly refuses an unpinned pip fallback. `uv` was not
preinstalled in this sandbox, so **uv 0.9.29 was fetched from the nixpkgs binary cache**, an
official signed package source — no install script was piped to a shell. uv resolved only the
supplied frozen lockfiles and altered no pin. On the Mac, install uv by whichever approved
official method you prefer.

---

## 5. Exact next commands on the Mac

```sh
cd <packet-root>
shasum -a 256 upstream/*.zip          # must match source-lock.json first

python3 -V                             # must be 3.11, 3.12 or 3.13
python3 project/scripts/verify.py
python3 -m compileall -q project/src project/scripts project/tests
python3 project/scripts/source_contracts.py

python3 project/scripts/bootstrap.py --allow-network   # uv must already be installed
./project/lelock --help

python3 project/scripts/live_palace_probe.py           # S3, no model needed

# S4/S5 need an endpoint and model you choose explicitly
python3 project/scripts/live_model_probe.py      --endpoint <URL> --model <NAME> --label A
python3 project/scripts/live_full_stack_probe.py --endpoint <URL> --model <NAME> --label A
```

Then work the synthetic manual script in `docs/ACCEPTANCE_MATRIX.md` for A08, A14, A16 and
the macOS halves of A04 and A15, recording each by its acceptance ID.

Do not mark a gate PASS from a historical receipt, replace a live integration with a fixture,
or delete a failing test. Treat nothing above as a Mac result.

---

## 6. Validation of the delivered ZIP

`Lelock_OS_Lovable_Source_Result.zip` was reopened after packaging and checked, not just
written:

- **CRC test passes**, 108 entries, extracts cleanly to a fresh directory.
- The extracted copy contains the repairs — `_same_inode` in `workspace.py`, `fchmod` in
  `common.py`, all 9 new tests plus the original `test_symlink_parent_denied` in
  `test_core.py`.
- `diff -rq` against the pristine extraction reports **exactly three differing files**, the
  three in the table above. `project/resources/source-lock.json` is byte-identical.
- From the extracted ZIP with **no** upstream archives restored:
  `python3 project/scripts/verify.py` → **95 tests, OK, exit 0**;
  `python3 -m compileall -q project/src project/scripts project/tests` → **exit 0**.
- `python3 project/scripts/source_contracts.py` → **exit 1, `FileNotFoundError` on
  `upstream/hermes-agent-2026.9.14.zip`**, which is the expected and correct behaviour: it
  reads the frozen archives directly. After restoring **only** the two archives named in
  `upstream/README.md` — SoulTavern deliberately left out — it returns **PASS, 8/8, exit 0**.
  The restore instructions are therefore proven sufficient, not assumed.
- Excluded from the ZIP: virtual environments (`project/.runtime/`, 733 MB), `__pycache__`,
  `*.pyc`, `*.egg-info`, the generated `project/lelock` launcher, runtime `*.sqlite3`
  databases, and the three upstream archives. A credential scan over the staged tree found
  nothing. Logs are sanitised — sandbox paths appear as `<PACKET_ROOT>` and `<WORK>`.
