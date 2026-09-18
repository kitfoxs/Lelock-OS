# Rakazo direct-character execution

## The guarantee we are designing and testing

When Ada is selected, the native model that replies as Ada receives Ada's computer
tools. A call to `lelock_computer_write`, `lelock_computer_run`, or a desktop action
keeps Ada's entity ID. It does not spawn Pi, swap to an anonymous worker, or transfer
Ada's private memory to a different runtime. Observation images return to that
same model when the transport supports images.

Enhance mode's SillyTavern text function callback does not implement screenshot
media injection. Therefore it omits the observation tool. Use the Codex Account
Chat route for the implemented multimodal callback. Do not pretend base64 text
is equivalent to giving a vision model an image.

A helper is another explicitly mapped card. The operator binds Rowan, then assigns
`{"Rowan":"<rowan-entity-id>"}` in Ada's helper settings. The main model can call
`lelock_ask_character` for Rowan; that worker gets Rowan's persona and computer.
It returns a labeled result to Ada, and Ada owns the final reply. Helper results
are not automatically promoted into the parent's canonical memory.

## Install the actual code

`tools/install_packet.py` includes the Rakazo source under
`integrations/rakazo-v03` in Lelock. `tools/install_rakazo.py` also installs it
into the actual Rakazo checkout at `integrations/lelock-v03` where its factory
import resolves. Both are required; merely testing the standalone service is
not installation into the live provider stack.

The inspected Rakazo commit is `67e3482e04fbd03f02ef46b7d6ea5e0843737a9c`.
Preserve any newer checkout. Run its own pinned dependency installation/build
under the operator's normal workflow; the packet never auto-downloads code.
Inspect `upstream-conformance.ts` against those actual dependencies. Use the
repository's compatible TypeScript configuration rather than deleting an
incompatible type check to get a green tick.

`entry.mjs` imports `createSandboxProvider`, not `createRunSandbox`. The latter
can select the real host computer according to Rakazo deployment settings.
A companion granted a private Docker computer must not silently inherit the Mac.
The live entry permits Docker only. The pure test service also accepts `fake`
for explicit offline fixtures; no application menu labels that as a live computer.

## Start with Docker and separate durable homes

Install and configure the real Rakazo Docker supervisor from its own documentation.
Supply its dedicated `SANDBOX_SUPERVISOR_TOKEN` to the sidecar process; do not put
that token in a card, chat, checked-in JSON or browser extension settings. The
supervisor URL defaults to `http://127.0.0.1:7091`.

```sh
# Values below are local operator setup, not secrets to commit.
export LELOCK_RAKAZO_HOME="$HOME/.local/share/lelock-rakazo-v03"
export LELOCK_RAKAZO_PROVIDER=docker
export SANDBOX_SUPERVISOR_URL=http://127.0.0.1:7091
# Supply SANDBOX_SUPERVISOR_TOKEN privately through your normal environment.

# The JSON argv must point to the sidecar installed IN the Rakazo checkout.
python3 /absolute/path/Lelock-OS/project/lelock-tavern serve \
  --origin http://localhost:8000 \
  --rakazo-command-json '["/bin/sh","/absolute/path/rakazo/integrations/lelock-v03/run-sidecar.sh"]'
```

Do not run the sidecar's stdio entry in a separate terminal and expect the gateway
to discover it. The gateway owns that subprocess and communicates over its pipes.
The Docker supervisor is the separate service.

After pairing, bind the card, enable its computer, and grant only the desired
`computer.*` capabilities. Default cards do not acquire computer or host powers.
YOLO skips repeated approvals only for granted operations. Native permissions
remain a separate concern, particularly for Antigravity.

## Actual interface and errors

The direct sidecar returns protocol `lelock-rakazo/1`, a provider descriptor,
`actor_mode: direct`, and `agent_runtime: false`. It implements `computer/execute`,
`observe`, `act`, `read`, `write`, and `stop`. Requests contain an actor inserted
by trusted gateway code and typed arguments. Character text cannot select an
arbitrary provider, account, bot ID, or host directory.

Command cwd is left to the provider's portable-home mapping. A host absolute
home is not passed as a container cwd. Text writes are read back exactly; reads
have bounds and relative-path validation. Screenshots remain image content in
the native callback. Desktop actions are bounded and partial completion is
uncertain. A stop never creates a missing computer. Independent actor operations
may run concurrently; overlapping operations on one actor's computer are fenced.

The implementation does not embed Rakazo's live noVNC viewer, full user-takeover
UX, or all cloud checkpoint/migration paths. Native screenshot operations and
text files are the first connected slice. Preserve browser profiles in the
actor-owned Docker home; use the provider's actual lifecycle tests for durability.
The sidecar's stored reference is not a complete computer backup.

## Mandatory live gate

Run the actual sidecar and supervisor; ask the main character to create a fixture
file and read it back. Confirm that its returned actor equals the active entity.
Run a second card and verify it cannot read the first card's fixture. Assign a
named helper; confirm helper and main receipts identify the appropriate entities.
Request a screenshot with a vision-capable account model; inspect an actual page,
perform one reversible action, and verify the external state. Stop the computer,
resume, and prove file persistence. Record actual versions and test output.

The packet's cross-language tests use real Python/Node transports and real
temporary files but an explicitly fake SandboxProvider. They are not this live gate.
