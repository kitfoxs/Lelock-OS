# Pulse, proactive presence, channels, and voice

## A clock is not a permanently thinking model

Pulse wakes approved work when an event is due. Idle time does not consume continuous model inference. An event can request a short reflection, resume an approved project, place a note in the local inbox or send a message through a separately enabled adapter. The event does not expand the session's capabilities.

`jobs.py` implements durable schedule/queue primitives, numeric five-field cron, interval and inactivity events, timezone-aware quiet hours, an HMAC verifier and a worker callback. It does not currently install a background service, watch arbitrary files, expose a public webhook listener or wire the callback to real Hermes. Those are explicit integration tasks.

## Scheduling semantics

A schedule binds an ID, event type, payload, timezone, expiration and **operator-selected policy ID**. Payload content is data; it cannot choose a higher-privilege policy. Resolve the policy ID against the running owner's approved leases each time the event is processed. Expired or revoked leases stop the event even if its queue row survives a restart.

The implemented cron dialect supports numeric fields, lists, ranges and steps. It does not claim every cron extension, named months or natural-language schedule interpretation. Day-of-month and day-of-week behavior follows the code's documented numeric matching. Timezone uses `zoneinfo`. Wall-clock minute deduplication avoids a double event in the repeated autumn hour. Nonexistent spring-forward times are not retroactively replayed. Test the selected timezone on the target Mac.

Intervals are aligned to interval slots, not promised as exactly N seconds after registration. Inactivity measures only direct activity from an authorized Lelock interface, not a global desktop tracker. A threshold produces one event per recorded last-activity value rather than an endless “are you there?” loop. Quiet hours defer execution; they do not covertly disable the queue.

## Durable job lifecycle

The queue claims work transactionally. Completed duplicate submissions use a stable dedupe key. A job interrupted after claim is not automatically declared safe to rerun; its external effects may have occurred. Reconcile running/uncertain work with receipts after establishing that no previous owner remains alive.

A callback returning `pending_approval` makes the job `awaiting_approval`, not `done`. Add a deliberate resume/finalization link after operator approval. Do not restart the entire model task merely because one action was waiting for a click.

Scheduling a job and delivering an external message are separate operations. Persist outbound intent and provider receipts. Where a provider lacks idempotent send, a timeout after acceptance remains uncertain; blindly retrying can send duplicates.

## Working queue example, without a model

```python
import time
from pathlib import Path
from lelock_entity.store import Store
from lelock_entity.jobs import JobQueue, Pulse, PulseWorker

store = Store(Path("./synthetic-pulse-state"))
queue = JobQueue(store)
pulse = Pulse(queue)
pulse.add(
    "demo-tick", kind="interval", policy_id="operator-demo-lease",
    payload={"task": "record a local demo event"},
    expires_at=time.time() + 3600, interval=300,
)
pulse.tick()
worker = PulseWorker(queue, lambda payload, job_id: {
    "status": "done", "job_id": job_id, "demo_only": True,
})
print(worker.run_once())
```

This calls real queue code, but the callback is intentionally a no-effect demonstration. Replacing it with Hermes requires the policy resolver, single-owner runtime, cost budget and cancellation contract below. It is not evidence of an autonomous companion already running.

## Runtime-owner integration to implement

The standalone owner serializes direct conversation and queued work. Add an event dispatcher that resolves the schedule lease, reserves a model budget, assembles only approved context, starts one bounded turn, and records its result. A new direct message should be able to cancel or pause optional scheduled work rather than fight it for the same session file.

Do not run the current `chat` and `serve` CLI owners simultaneously on one home. Their profile lease deliberately prevents this. Unify bridge, conversation queue and Pulse under one owner for the integrated product; both surfaces should submit events to it. The provided `serve` command is a tool daemon, not a completed streaming conversational server.

For macOS background operation, create an opt-in user LaunchAgent only after validating start/stop/restart. No service should automatically enable YOLO on reboot or revive an expired lease. Store schedules separately from the current permission lease so tasks remain inspectable but disabled pending explicit reauthorization.

## Webhooks and filesystem events

The HMAC verifier signs timestamp, event ID and body and rejects stale, oversized or duplicate events. The verifier is not a secure public server by itself. A public receiver needs a reviewed deployment, TLS, rate limiting, source-specific signature rules and a bounded schema; this packet does not deploy one.

Filesystem triggers should monitor explicitly selected paths, ignore temporary/self-generated files, debounce bursts and record content hashes. Triggering on files the agent itself writes can create an infinite loop; dedupe by cause and revision. No whole-home surveillance or account polling is implied by “proactive.”

## Channel adapters

The implemented channel is a **local durable inbox** in `channels.py`. It is not an OS notification, Discord DM, telephone call or delivered email. Build one real external adapter next, not six half-working integrations.

A channel adapter contract needs: authenticated recipient identity; a standing send capability; privacy classification of content; optional draft versus send; stable request ID; provider message ID; delivery/acceptance semantics; retry policy; recipient quiet hours; and revocation. Logs should reference IDs and hashes where practical, not dump tokens or private letters.

Kit's preferred proactive companion behavior can be expressed as explicit policies: a gentle local check-in after an agreed inactivity threshold, an interesting research finding from an approved project, or a scheduled study invitation. Avoid guilt, pressure or fabricated offscreen adventures. “I found this” requires a recorded search or supplied evidence, not a trigger inventing an event.

## Voice build contract

Start with push-to-talk: microphone capture → transcription → normal Entity conversation turn → speech synthesis → playback. Preserve the same identity, memory, permissions and audit trail as text. Do not build a second voice companion with a disconnected memory file.

Add interruptible playback and input cancellation before hands-free wake words. The user should be able to cut off a long answer without waiting for it to finish. A cancel signal must reach the provider request and the owned process runner where supported; marking a UI button “Stop” is not enough.

Keep tool confirmations visible and accessible. A voice utterance granting permission must be unambiguously user-originated and bound to the exact pending action. Do not let TTS playback, a webpage, or another person in the room approve an action by echoing “yes.” YOLO remains an explicit operator session setting, not a word a model can casually say aloud.

Voice history retention is separate from transcript/memory retention. Default to not persisting raw audio unless selected. Hosted transcription or TTS sends content to a provider; state that clearly in the actual setup UI. Microphone permissions, audio routing, device changes and privacy need real Mac/iOS testing. No voice provider is installed, purchased or certified here.

## Acceptance

Prove a real schedule with an actual bounded turn, one actual local inbox note, quiet hours, duplicate suppression, expiration, restart, stop and uncertain-result reconciliation. Then test the chosen external channel with an explicitly authorized test recipient. Voice gets separate microphone, playback, interruption, tool-approval and retention gates. Keep each result independently labeled.
