# Publication repair — scope and fresh evidence

Reviewed base: `0cbd55efc19fe0dda6ce5ecec1f00f099ba8ade4`.
This is a targeted publication repair, not a recovered application release.

## Actual changes

- Anchor the generated-launcher ignore rule to `/lelock` so it does not hide `src/lelock/`.
- Correct all seven SillyTavern imports for the documented third-party URL layout;
  the remainder of `index.js` is unchanged.
- Document subdirectory installation instead of advertising an unsupported monorepo-root install.
- Make bootstrap refuse missing current source/archives before it creates runtime directories;
  make the app test runner report BLOCKED with zero executed tests when source is absent.
- Add an offline publication checker that detects absent, untracked, staged-only, or
  locally changed Python source, plus extension layout and optional source-hash checks.
- Replace stale headline claims with explicit alpha/recovery status. Preserve old launch,
  Lovable and compendium artifacts under `docs/history/`; never use them to regenerate new source.

## Fresh verification in this repair environment

| Check | Outcome | What was actually exercised |
|---|---|---|
| Publication regressions | PASS, 12 tests | Temporary synthetic Git repositories, missing/staged/modified source, ignore rule, import paths, checksum checks, guarded scripts |
| Changed Python syntax | PASS | bootstrap, verify, publication checker and maintenance tests compiled |
| Extension JavaScript syntax | PASS | Node ESM syntax check; not executed in a browser |
| Static upstream import/export layout | PASS, 7 imports | Actual supplied SillyTavern 1.19.0 ZIP; every corrected URL target exists and exports the imported names |
| Current app tests | BLOCKED | Newer Python package is absent in the public Git tree |
| Full clean-clone install | NOT_RUN | Container Git network access was unavailable; source is absent in any case |
| Actual Palace/model/bridge/Mac/human gates | NOT_RUN | Not replaced with fixtures or inferred from older receipts |

GitHub's connected API was used to inspect the immutable tree and file contents.
Selected existing files used for local checks were byte-verified against the remote
Git blob hashes. No claim is made of cloning and executing the complete public repo.
The unchanged extension template/CSS were not browser-tested. The regression suite's
placeholder modules/assets exist only in disposable test fixtures, not product source.

Raw publication-test evidence is included under `handoff/publication-evidence/`.
These logs contain synthetic data, not the owner's runtime state. No application source
was rewritten from a compendium, or substituted with a test fixture.

## Stage 2: Source Recovery & Release Completion (Mac Maintainer)

Reviewed commit: `8e2c608b260ca3318991448b1111079d39ea3612`.

### Actions executed
- Recovered the 19 authentic Python modules in `project/src/lelock/` from Kit's Mac maintainer working directory (including `_vendor/soultavern/` parser and LICENSE).
- Security and secrets audit: verified zero hardcoded tokens, API keys, private passwords, personal directories, or customer data.
- Stripped trailing whitespace and verified `git diff --cached --check` cleanly.
- Updated `project/scripts/bootstrap.py` to check for missing source prior to python version checks, expanded supported Python range to 3.11–3.14, and added pointer to `fetch_upstream.py`.
- Added `project/scripts/fetch_upstream.py` to automatically download and verify exact SHA-256 archives from GitHub Release `v0.1.0-alpha`.
- Created GitHub Release `v0.1.0-alpha` and uploaded exact pinned source archives:
  - `hermes-agent-2026.9.14.zip` (sha256: `c3694a72bf739c76718e31529102f0e4c16f225c2fba0bec3136ba92e127addc`)
  - `mempalace-3.9.0.zip` (sha256: `8407eb0390bdc8d5a3bba31ce64cd0fda91d8a5a73b5c014995084cd72543bc9`)
  - `SoulTavern-2.0.3.zip` (sha256: `4fdc4e1d1e555ea7748b797ddf79cee0806323ddc1ba09fe2440a7937f4a7b7b`)

### Verification results

| Gate | Outcome | Detail |
|---|---|---|
| Publication layout check (`check_publication.py`) | PASS | Required modules present, committed to HEAD, ignore rule verified, extension layout verified |
| Upstream source check (`check_publication.py --require-upstream`) | PASS | Exact archive SHA-256 matches `source-lock.json` |
| Publication maintenance tests (`unittest maintenance_tests`) | PASS, 12/12 | 12 tests passing in 1.77s |
| Offline application tests (`verify.py`) | PASS, 102/102 | 102 tests passing in 5.97s (Cards, Companions, Core, Provider, RPC, Server) |
| Total test suite | PASS, 114/114 | All tests pass |

### Remaining work
- Live model, Palace, bridge and human acceptance on target Mac.
