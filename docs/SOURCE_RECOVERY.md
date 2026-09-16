# Recover the current source without undoing Terminal Ada's work

The initial published commit `0cbd55efc19fe0dda6ce5ecec1f00f099ba8ade4` contains
packaging, tests, resources, and extension JavaScript but no `project/src/lelock/`.
A bare `lelock` rule in `project/.gitignore` excluded both the generated launcher and
the nested package. `/lelock` correctly ignores only the launcher.

## Maintainer Mac: recover, do not regenerate

Use the existing working checkout that produced the newer 102-test build. First inspect
`git status --short --untracked-files=all`, the current branch and remotes. Preserve all
unrelated changes. Do not switch branches, reset, or pull over dirty work blindly.

Apply/reconcile the publication repair to that checkout. Confirm its `project/.gitignore`
uses `/lelock`, then inspect:

```sh
git check-ignore -v --no-index project/src/lelock/cli.py
git status --short --untracked-files=all -- project/src/lelock
git ls-files -- project/src/lelock
```

For a nonignored source file, `git check-ignore` normally prints nothing and exits 1.
Review the entire current package, including new bridge/companions modules, for secrets,
private data, unexpected binaries, symlinks and stale copies. Add only reviewed source:

```sh
git add -- project/.gitignore project/src/lelock
git diff --cached --stat
git diff --cached --check
```

Review the actual staged content before committing/pushing through the normal workflow.
Do not use `git add -f .`, upload the whole home directory, or publish runtime data.
Do not restore the older compendium over the newer source. The owner can instead upload
a ZIP of the current `project/src/lelock/` (source only) for review; that is not proof it
was committed until the Git tree is checked.

## Fresh-checkout gate

After publication, make a new checkout in a **different** directory; do not delete the
working Mac copy. Run the publication checker and actual app tests there:

```sh
python3 project/scripts/check_publication.py
python3 project/scripts/verify.py
```

The checker verifies required package files are regular, tracked, committed, unchanged
relative to HEAD, and import-path/manifest metadata is consistent. This is a bounded
publication check, not a full security or dependency audit. A missing package produces
FAIL; it is not patched with stubs.

Restore exact source archives and follow `project/QUICKSTART.md`. Run real model,
Palace, browser bridge, target-Mac and human gates. A public downloadable pinned-source
bundle is still required before advertising a complete consumer installation.
Update `handoff/STATUS.json` with fresh evidence; preserve historical reports separately.
