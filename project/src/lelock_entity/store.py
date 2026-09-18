"""Private operational SQLite: proposals, run receipts and jobs; not semantic memory."""
from __future__ import annotations
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import time
import uuid
from .common import EntityError, canonical, digest, private_dir

class Store:
    def __init__(self, directory: Path):
        self.directory = private_dir(directory)
        self.path = self.directory / "entity-operations.sqlite3"
        if self.path.is_symlink():
            raise EntityError("Linked database refused")
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            INSERT OR IGNORE INTO meta VALUES('schema','1');
            CREATE TABLE IF NOT EXISTS actions(
              id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
              entity TEXT NOT NULL, session TEXT NOT NULL, tool TEXT NOT NULL,
              payload TEXT NOT NULL, digest TEXT NOT NULL, state TEXT NOT NULL,
              created REAL NOT NULL, expires REAL NOT NULL, result TEXT);
            CREATE TABLE IF NOT EXISTS events(
              seq INTEGER PRIMARY KEY AUTOINCREMENT, created REAL NOT NULL,
              kind TEXT NOT NULL, metadata TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs(
              id TEXT PRIMARY KEY, dedupe TEXT UNIQUE NOT NULL, payload TEXT NOT NULL,
              due REAL NOT NULL, expires REAL NOT NULL, state TEXT NOT NULL,
              claimed REAL, finished REAL, result TEXT);
            """)
            version = db.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0]
            if version != "1":
                raise EntityError("Unsupported operational schema")
        self.path.chmod(0o600)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def event(self, kind: str, metadata: dict):
        # Callers log identifiers/hashes, never credentials or raw terminal output.
        with self.connect() as db:
            db.execute("INSERT INTO events(created,kind,metadata) VALUES(?,?,?)",
                       (time.time(), kind, canonical(metadata)))

    def propose(self, *, entity: str, session: str, tool: str, payload: dict,
                request_key: str, expires: float) -> dict:
        fingerprint = digest({"entity": entity, "session": session, "tool": tool, "payload": payload})
        now = time.time()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM actions WHERE request_key=?", (request_key,)).fetchone()
            if row:
                if row["digest"] != fingerprint:
                    raise EntityError("Request ID reused with different content")
                return dict(row)
            ident = uuid.uuid4().hex
            db.execute("INSERT INTO actions VALUES(?,?,?,?,?,?,?,?,?,?,NULL)",
                       (ident, request_key, entity, session, tool, canonical(payload), fingerprint,
                        "pending", now, min(expires, now + 1800)))
            return dict(db.execute("SELECT * FROM actions WHERE id=?", (ident,)).fetchone())

    def get(self, ident: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT * FROM actions WHERE id=?", (ident,)).fetchone()
            if not row:
                raise EntityError("Action does not exist")
            return dict(row)

    def claim(self, ident: str, expected_digest: str, entity: str, session: str) -> dict:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM actions WHERE id=?", (ident,)).fetchone()
            if not row or row["entity"] != entity or row["session"] != session:
                raise EntityError("Action belongs to a different entity/session")
            if row["digest"] != expected_digest or row["expires"] <= time.time() or row["state"] != "pending":
                raise EntityError("Action changed, expired or already consumed")
            payload = json.loads(row["payload"])
            actual = digest({"entity": entity, "session": session, "tool": row["tool"], "payload": payload})
            if actual != expected_digest:
                raise EntityError("Stored action integrity mismatch")
            db.execute("UPDATE actions SET state='executing' WHERE id=?", (ident,))
            return dict(row)

    def finish(self, ident: str, state: str, metadata: dict):
        if state not in {"done", "needs_review"}:
            raise EntityError("Invalid terminal action state")
        with self.connect() as db:
            changed = db.execute("UPDATE actions SET state=?,result=? WHERE id=? AND state='executing'",
                                 (state, canonical(metadata), ident)).rowcount
            if changed != 1:
                raise EntityError("Cannot finish an unclaimed action")
            db.execute("INSERT INTO events(created,kind,metadata) VALUES(?,?,?)",
                       (time.time(), "action." + state, canonical({"action_id": ident, **metadata})))

    def reject(self, ident: str, entity: str, session: str):
        with self.connect() as db:
            changed = db.execute("UPDATE actions SET state='rejected',payload='{}' "
                                 "WHERE id=? AND entity=? AND session=? AND state='pending'",
                                 (ident, entity, session)).rowcount
            if changed != 1:
                raise EntityError("No pending action to reject")
        self.event("action.rejected", {"action_id": ident})

    def pending(self, entity: str, session: str) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM actions WHERE entity=? AND session=? "
                     "AND state IN ('pending','executing','needs_review') ORDER BY created", (entity, session))]

    def recover_uncertain(self) -> dict:
        """Operator-only startup reconciliation AFTER proving the old owner is stopped."""
        with self.connect() as db:
            actions = db.execute("UPDATE actions SET state='needs_review' WHERE state='executing'").rowcount
            jobs = db.execute("UPDATE jobs SET state='needs_review' WHERE state='running'").rowcount
        return {"actions": actions, "jobs": jobs}
