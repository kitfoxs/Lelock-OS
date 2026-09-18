# Acceptance ledger — separate each evidence layer

## Authoring checks

`tools/verify.py` runs the new Python integration tests, additive installer tests,
TypeScript compilation, direct-computer contract tests and extension-controller
tests. Its default dependency is the labeled prior v0.2 snapshot; `--repo` instead
uses the actual checkout. Fixtures do not contact a model or a live sandbox.

The authoring browser test was attempted with real Chromium and a synthetic host
fixture, but local HTTP navigation returned `ERR_BLOCKED_BY_ADMINISTRATOR` before
page load. No browser pass is claimed and no managed browser policy was disabled.
Run `tools/browser_check.py` in an environment whose existing policy permits local
development. That fixture still does not replace actual SillyTavern acceptance.

## Actual checkout

Inspect Git status and run the original repository's documented commands. Do not
quote an old test count as a new result. Then run:

```sh
python3 /path/to/packet/tools/verify.py --repo /path/to/Lelock-OS
```

This must use installed `lelock_entity`; never promote the test snapshot to the
production Python path. Compile the sidecar against actual Rakazo dependencies.
The standalone TypeScript service tests do not establish that upstream conformance.

## Live native/account check

Launch the gateway, pair, and complete the provider's own login. Run:

```sh
python3 /path/to/packet/tools/live_acceptance.py \
  --pairing "$HOME/.local/share/lelock-tavern-v03/operator-pairing.json" \
  --provider codex --use-existing-signed-in-account \
  --report /private/path/codex-live.json
```

The script intentionally consumes existing account quota, creates a new synthetic
character, authorizes only the exact fixture write in SAFE, checks actual bytes
through the read tool, verifies main actor attribution and stops that session.
Repeat with `--yolo` to prove no per-action prompt. `--computer` targets the actual
configured Rakazo computer write/read tools. Antigravity additionally requires
`--provider antigravity --native-risk-ack`; no native bypass flag is silently added.

The live script does not test screenshot perception, every native built-in,
background work, full chat history, or billing enforcement. Record provider model,
binary versions, and actual receipts manually alongside the output.

## Real SillyTavern gate

Use two fresh synthetic cards and an ordinary new chat. Confirm the root manifest
loads with no module/import errors. Pair with a one-time code. Attempt an unpaired
request and wrong-origin request and verify refusal. Bind each card once; confirm
same names do not merge. Configure SAFE then YOLO. With the SillyTavern model API
unset, use Account Chat's explicit **Lelock Send**. Confirm one user message and
one correctly attributed assistant result, with no simultaneous host API request.

Switch cards during an active turn. No text, tool registration, memory or pending
approval may silently follow the new card. Inspect the retained result for the old
card. Test exact approval, rejection, stop, expired pairing/session, disconnection
and repeated requests. Do not use regenerate/swipe or group-chat cases as accepted
features until their own semantics are implemented and tested.

## Direct computer and helpers

Observe an actual screenshot through the primary Codex model and perform one
reversible page/desktop action. Verify real external state, not just a model claim.
Create a file, stop/resume the actor's Docker computer, and prove persistence.
The second card must not access the first's private home. Assign that second card
as a named helper and verify helper-specific persona and computer ownership.
Main-card tools should still work when no helpers are configured.

## Memory, Skills, Pulse and restart

Enable actual MemPalace on fresh profiles. Save a selected fact, verify full
readback, recall after restart and confirm the other card has no evidence for it.
Do not label pure SQLite turn history as canonical Palace memory. Deliberately
stop Palace and verify the failure remains visible.

Review and read one Skill, edit it and confirm the pin no longer authorizes it.
Authorize one recurring account task with Pulse enabled. Verify local-inbox result,
quiet-hours behavior, duplicate handling, schedule disable and expired-session
rejection. The inbox is not an OS notification or external message. Restart the
gateway, re-pair, retain entity mappings, and deliberately reauthorize schedules.

## Release gate

A release record must list each layer as passed / failed / unavailable, exact
commands and versions, sanitized evidence paths, and known limitations. Update
public README and handoff status only to that demonstrated scope. No percentage
complete, padded test total, mock substitution or generic green badge proves the
whole companion product.
