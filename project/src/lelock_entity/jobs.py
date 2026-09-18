"""Durable Pulse primitives. No hidden startup, sensing, automatic replay or OS installation."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import hashlib
import hmac
import json
import time
import uuid
from zoneinfo import ZoneInfo
from .common import EntityError, canonical, text
from .store import Store
from .policy import StopSignal

@dataclass(frozen=True)
class QuietHours:
    timezone: str = "America/Chicago"
    start: str = "23:00"
    end: str = "09:00"

    def contains(self, timestamp: float) -> bool:
        def minute(value):
            hour, mins = map(int, value.split(":"))
            if not 0 <= hour < 24 or not 0 <= mins < 60:
                raise EntityError("Invalid quiet-hours clock")
            return hour * 60 + mins
        current = datetime.fromtimestamp(timestamp, ZoneInfo(self.timezone))
        now = current.hour * 60 + current.minute
        start, end = minute(self.start), minute(self.end)
        if start == end:
            return False
        return start <= now < end if start < end else now >= start or now < end

class Cron:
    """Five numeric fields; lists/ranges/steps; DOM/DOW OR; no seconds or named months."""
    def __init__(self, expression: str):
        parts = expression.split()
        if len(parts) != 5:
            raise EntityError("Cron needs minute hour day month weekday")
        self.raw = parts
        self.values = [self._parse(part, low, high) for part, (low, high) in
                       zip(parts, [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)])]
        if 7 in self.values[4]:
            self.values[4].remove(7)
            self.values[4].add(0)

    @staticmethod
    def _parse(field: str, low: int, high: int) -> set[int]:
        values = set()
        try:
            for segment in field.split(","):
                base, slash, step_text = segment.partition("/")
                step = int(step_text) if slash else 1
                if step <= 0:
                    raise ValueError()
                if base == "*":
                    left, right = low, high
                elif "-" in base:
                    left, right = map(int, base.split("-"))
                else:
                    left = int(base)
                    right = high if slash else left
                if not low <= left <= right <= high:
                    raise ValueError()
                values.update(range(left, right + 1, step))
        except ValueError as exc:
            raise EntityError("Unsupported/invalid cron field") from exc
        return values

    def matches(self, current: datetime) -> bool:
        minute, hour, dom, month, dow = self.values
        if current.minute not in minute or current.hour not in hour or current.month not in month:
            return False
        day_match, week_match = current.day in dom, (current.weekday() + 1) % 7 in dow
        # Wildcard-led fields have the conventional restricted-field behavior.
        if self.raw[2].startswith("*") or self.raw[4].startswith("*"):
            return day_match and week_match
        return day_match or week_match

class JobQueue:
    def __init__(self, store: Store):
        self.store = store

    @staticmethod
    def _insert(db, dedupe: str, payload: dict, due: float, expires: float):
        raw = canonical(payload)
        if len(raw.encode()) > 200_000 or expires <= due:
            raise EntityError("Invalid job payload/expiry")
        existing = db.execute("SELECT id,payload FROM jobs WHERE dedupe=?", (dedupe,)).fetchone()
        if existing:
            if existing["payload"] != raw:
                raise EntityError("Job dedupe key reused with different content")
            return existing["id"]
        ident = uuid.uuid4().hex
        db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,'pending',NULL,NULL,NULL)",
                   (ident, dedupe, raw, due, expires))
        return ident

    def enqueue(self, dedupe: str, payload: dict, *, due: float | None = None, ttl: float = 3600):
        text(dedupe, 512)
        now = time.time() if due is None else due
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            return self._insert(db, dedupe, payload, now, now + ttl)

    def claim(self, *, now: float | None = None) -> dict | None:
        now = time.time() if now is None else now
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE jobs SET state='expired' WHERE state='pending' AND expires<=?", (now,))
            row = db.execute("SELECT * FROM jobs WHERE state='pending' AND due<=? AND expires>? "
                             "ORDER BY due,id LIMIT 1", (now, now)).fetchone()
            if row is None:
                return None
            db.execute("UPDATE jobs SET state='running',claimed=? WHERE id=?", (now, row["id"]))
            return {**dict(row), "payload": json.loads(row["payload"])}

    def finish(self, ident: str, state: str, result: dict):
        if state not in {"done", "awaiting_approval", "needs_review"}:
            raise EntityError("Invalid job outcome")
        with self.store.connect() as db:
            changed = db.execute("UPDATE jobs SET state=?,finished=?,result=? WHERE id=? AND state='running'",
                                 (state, time.time(), canonical(result), ident)).rowcount
            if changed != 1:
                raise EntityError("Job already finished or not claimed")

class Pulse:
    def __init__(self, queue: JobQueue):
        self.queue = queue
        with queue.store.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS schedules(id TEXT PRIMARY KEY, config TEXT NOT NULL,
              last_slot TEXT, enabled INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS activity(profile TEXT PRIMARY KEY, at REAL NOT NULL);
            """)

    def add(self, ident: str, *, kind: str, policy_id: str, payload: dict,
            expires_at: float, interval: int = 0, cron: str = "", timezone: str = "America/Chicago"):
        """Operator-only registration; policy_id resolves to an existing authorized execution session."""
        if kind not in {"interval", "cron", "inactivity"} or not policy_id:
            raise EntityError("Invalid schedule")
        if kind in {"interval", "inactivity"} and interval < 60:
            raise EntityError("Scheduled model work must be at least 60 seconds apart")
        if kind == "cron":
            Cron(cron)
        ZoneInfo(timezone)
        config = {"kind": kind, "policy_id": policy_id, "payload": payload,
                  "expires_at": expires_at, "interval": interval, "cron": cron, "timezone": timezone}
        with self.queue.store.connect() as db:
            db.execute("INSERT INTO schedules(id,config) VALUES(?,?)", (ident, canonical(config)))

    def activity(self, policy_id: str, *, at: float | None = None):
        # Call ONLY for direct activity on an authorized Lelock interface; not global desktop tracking.
        at = time.time() if at is None else at
        with self.queue.store.connect() as db:
            db.execute("INSERT INTO activity VALUES(?,?) ON CONFLICT(profile) DO UPDATE SET at=excluded.at",
                       (policy_id, at))

    def tick(self, *, now: float | None = None) -> list[str]:
        now = time.time() if now is None else now
        emitted = []
        with self.queue.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for row in db.execute("SELECT * FROM schedules WHERE enabled=1").fetchall():
                config = json.loads(row["config"])
                if now >= config["expires_at"]:
                    continue
                kind = config["kind"]
                slot = None
                if kind == "interval":
                    slot = str(int(now // config["interval"]))
                elif kind == "cron":
                    local = datetime.fromtimestamp(now, ZoneInfo(config["timezone"]))
                    if Cron(config["cron"]).matches(local):
                        # One event per wall-clock minute, including the repeated autumn hour.
                        slot = local.strftime("%Y-%m-%dT%H:%M")
                else:
                    active = db.execute("SELECT at FROM activity WHERE profile=?", (config["policy_id"],)).fetchone()
                    if active and now - active[0] >= config["interval"]:
                        slot = str(active[0])
                if slot is None or slot == row["last_slot"]:
                    continue
                payload = {"policy_id": config["policy_id"], "trigger": kind,
                           "schedule": row["id"], "data": config["payload"]}
                ident = self.queue._insert(db, row["id"] + ":" + slot, payload,
                                          now, min(now + 3600, config["expires_at"]))
                db.execute("UPDATE schedules SET last_slot=? WHERE id=?", (slot, row["id"]))
                emitted.append(ident)
        return emitted

    def webhook(self, *, secret: bytes, timestamp: int, body: bytes, signature: str,
                policy_id: str, event_id: str, now: float | None = None) -> str:
        """Verifier/queue ingress, not a listening Internet endpoint. Domain-specific data only."""
        now = time.time() if now is None else now
        if len(secret) < 32 or abs(now - timestamp) > 300 or len(body) > 100_000:
            raise EntityError("Webhook outside allowed bounds")
        signed = str(timestamp).encode() + b"." + event_id.encode() + b"." + body
        expected = hmac.new(secret, signed, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise EntityError("Webhook signature rejected")
        from .common import strict_json
        data = strict_json(body)
        if not isinstance(data, dict):
            raise EntityError("Webhook payload must be an object")
        return self.queue.enqueue("webhook:" + policy_id + ":" + event_id,
                                  {"policy_id": policy_id, "trigger": "webhook", "data": data}, due=now)

class PulseWorker:
    def __init__(self, queue: JobQueue, dispatch, *, quiet: QuietHours | None = None,
                 stop: StopSignal | None = None):
        self.queue, self.dispatch = queue, dispatch
        self.quiet, self.stop = quiet, stop or StopSignal()

    def run_once(self, *, now: float | None = None):
        self.stop.check()
        now = time.time() if now is None else now
        if self.quiet and self.quiet.contains(now):
            return {"status": "quiet"}
        job = self.queue.claim(now=now)
        if job is None:
            return {"status": "idle"}
        try:
            self.stop.check()
            result = self.dispatch(job["payload"], job["id"])
            state = "awaiting_approval" if result.get("status") == "pending_approval" else "done"
            self.queue.finish(job["id"], state, result)
            return {"status": state, "job_id": job["id"], "result": result}
        except BaseException as exc:
            self.queue.finish(job["id"], "needs_review", {"error_type": type(exc).__name__})
            raise
