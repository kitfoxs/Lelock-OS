# Security, capability policy and real YOLO mode

## User requirement

Kit specifically requested a YOLO mode because that is how she normally tests terminal agents. Do not remove it, rename it into a read-only simulation, or silently continue asking for each ordinary enabled action. The implementation provides a real `Mode.YOLO` branch that automatically executes registered tools whose capabilities the operator enabled.

Three separate questions must never collapse into one switch:

1. **Authentication:** who is calling this process, and is this the operator or a model-facing client?
2. **Authorization:** what capabilities/resources did the operator give this session?
3. **Approval policy:** does an authorized operation require another confirmation?

YOLO changes question 3. It does not mean anonymous network callers may control the computer, that every installed tool becomes available, or that log and stop facilities disappear. A user-controlled high-autonomy mode and an unauthenticated vulnerable server are not the same feature.

## Mode behavior

| Behavior | SAFE | TRUSTED | YOLO |
|---|---|---|---|
| Read through an enabled read tool | Execute | Execute | Execute |
| Enabled mutation without standing approval | Propose | Propose | Execute |
| Enabled capability on trusted auto-approval list | Propose | Execute | Execute |
| Capability not enabled | Refuse | Refuse | Refuse |
| Unknown tool/schema fields | Refuse | Refuse | Refuse |
| Expired/revoked/stopped session | Refuse | Refuse | Refuse |
| Agent approval endpoint access | Refuse | Refuse | Refuse |
| Action receipts and uncertain-effect handling | Retained | Retained | Retained |

An operator can deliberately grant `workspace.delete`, `process.run`, `identity.write` or an external messaging capability. YOLO then removes per-operation prompts **for those supported capabilities**. It does not add an implementation that is not registered. The current CLI registers text/world/memory tools and optionally a process tool; external messaging and identity-tool registration are later integrations.

The model has no `set_mode`, `grant_permission`, `approve_action`, `read_operator_token` or `disable_audit` tool. Model text such as "Kit said YOLO" cannot change the authenticated session. The selected mode is visible in status and attached to execution receipts as `policy:yolo`, rather than falsely claiming a human clicked Approve.

## Working examples

Run the offline demonstration directly from the extracted packet. It creates disposable test directories and uses no model or Palace:

```sh
cd implementation
PYTHONPATH=src python3 -m lelock_entity demo --mode yolo
```

To demonstrate **real unsandboxed process execution** as well:

```sh
PYTHONPATH=src python3 -m lelock_entity demo \
  --mode yolo --exec-backend host --ack-host-risk
```

That demo executes only its hardcoded harmless `printf` command. The actual registered process tool accepts scripts chosen by the agent once it is connected to a runtime. Its consequences are therefore substantially broader than the demonstration.

After applying the source overlay, installing the existing pinned dependencies and completing baseline setup, the corresponding live command is:

```sh
PYTHONPATH=project/src <HERMES_ENV_PYTHON> -m lelock_entity chat \
  --home /absolute/path/to/an-explicit-test-profile \
  --mode yolo --exec-backend host --ack-host-risk
```

`<HERMES_ENV_PYTHON>` is a placeholder for the existing isolated Hermes interpreter; determine it from the checked-out bootstrap output rather than inventing a path. `--home` must name a real Lelock-owned test profile. This handoff does not initialize or migrate the private Ada Palace automatically.

TRUSTED demonstrates the middle ground:

```sh
PYTHONPATH=src python3 -m lelock_entity demo \
  --mode trusted --auto workspace.write --auto world.write
```

`--cap` replaces the default capability list when supplied and may be repeated. `--auto` must be a subset of that list. Selecting a process backend adds the corresponding `process.run` capability. A future UI must display that effect plainly.

## Execution backend is an independent choice

**Host:** `/bin/sh -c` runs as the operating-system user, with the selected workspace as its starting directory. It is **not confined to that directory**. An arbitrary program can read other files, use network access, spawn processes, modify account-accessible state or obtain information outside the curated tool surface. The reduced environment prevents automatic inheritance of common credentials; it does not stop a program from reading accessible credential files. An application-level `cwd`, path validator or prompt instruction is not a sandbox.

Host mode can also modify or tamper with files used by the application when both run under the same user. Consequently its logs are not tamper-proof and its policy is not a boundary against a hostile same-user process. Do not advertise otherwise. A separate VM/user/container is appropriate when those threats matter.

**Docker:** the provided command builder uses an operator-selected image digest, `--pull=never`, no Docker-socket mount, a single workspace mount, a read-only container root, dropped capabilities, no-new-privileges, process/CPU/memory limits and networking disabled by default. The code includes runtime invocation and cleanup, but **a Docker runtime was not available for a live test here**. The test suite checks the generated command, not container isolation. A container is still not an absolute guarantee against every kernel/runtime vulnerability.

`--docker-network` explicitly changes the container's network choice. It does not secretly pull an image or install a runtime. Image identity, availability, user IDs, file ownership and architecture must be verified on the Mac. A future VM backend should use snapshots and explicit mounts, not reinterpret host mode as a VM.

The process runner preserves no shell history, injects no model API keys by default, bounds captured output, applies a timeout and stops its process group. Child processes that deliberately detach their sessions may escape this host cleanup; include that in the host-mode risk model. OS/container-level process isolation is needed for stronger guarantees.

## Default boundaries and lifespan

A session expires after two hours by default; the CLI permits an explicit duration from one minute to one day. The default action budget is 200. This is a user-changeable testing budget, not a vendor-imposed feature limitation. Model-token and dollar accounting are not implemented by this counter; the live runtime must separately reserve and account for inference usage.

YOLO is **not automatically persisted across restarts**. Starting a new session with `--mode yolo` is explicit renewal. Long-running scheduled jobs must bind to an approved lease and cannot silently obtain a fresh unlimited session after the owner exits. The mode can eventually be persisted as an operator-owned configuration choice, but not as a model-writable preference or imported character-card field.

The stop signal blocks new actions and interrupts the provided process runner. It cannot recall an already sent message or undo an already completed file operation. Do not describe it as universal rollback. Model HTTP cancellation and external-provider cancellation need their own adapters and tests.

## Bridge threat model

The new server binds only `127.0.0.1`, checks the exact Host authority, rejects unapproved/null origins, requires a bearer token, and distinguishes operator and agent credentials. Browser preflight may be unauthenticated only because it reveals no sensitive data and cannot execute an operation. Actual requests require credentials.

Pairing files are private, separate and session-specific. Never put operator tokens in prompts, character cards, lorebooks, localStorage, URLs, screenshots, log bundles, commits or generated documents. The basic JavaScript client keeps its token in memory. A production UI still needs an XSS/content-rendering review.

The current `http.server` implementation is a development loopback service, not a hardened Internet server. Public access requires a separate reviewed transport/authentication design, rate limiting, deployment security and remote-client approval semantics. Installing an MCP wrapper does not authorize a public tunnel. [M1–M2 in sources]

## Action state machine

```text
pending -> executing -> done
    |           |
 rejected       +-> needs_review
```

A request key binds the session, tool and exact argument hash. Reusing it with different content is an error. Replaying a completed request returns its receipt rather than executing again. Approval checks the exact digest and rechecks capability, expiry, tool version and arguments before claiming the action.

A timeout, lost reply, failed readback or crash can occur after an effect. Such a request becomes `needs_review`; it is not automatically retried with a new key. This is conservative uncertain-effect handling, **not** a mathematical exactly-once guarantee for arbitrary external APIs. Provider idempotency keys should be used where genuinely supported.

## Required test expansion before daily personal use

Add tests for actual macOS filesystem behavior, externally modified files during replacement, detached host processes, secrets access under chosen backend, interrupting a real model request, expired pairing files, malicious rendered content, rate/resource exhaustion and adapter-specific external failures. Keep the present tests, but do not confuse them with a comprehensive security audit.
