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
was recovered, rewritten from a compendium, or substituted with a test fixture.
The application test count must be re-established once current Mac source is committed.

## Remaining work

Recover the reviewed current `project/src/lelock/` from the maintainer Mac, supply a
publicly reproducible exact upstream-source bundle, then test the real application and
bridge. Audit loopback authentication/origin handling and consent against the recovered
server; frontend path repairs alone are not a safety certification. Use
`docs/SOURCE_RECOVERY.md` and `handoff/NEXT_ACTION.md`.
