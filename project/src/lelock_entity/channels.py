"""Durable local notification inbox; external delivery is a separately registered adapter."""
from __future__ import annotations
import json
import time
from .common import EntityError, canonical, digest, text
from .store import Store

class LocalInbox:
    """Real local persistence, NOT an OS notification, Discord DM, SMS or phone call."""
    def __init__(self, store: Store, entity: str):
        self.store, self.entity = store, entity
        with store.connect() as db:
            db.executescript("""CREATE TABLE IF NOT EXISTS inbox(
              entity TEXT NOT NULL,id TEXT NOT NULL,created REAL NOT NULL,body TEXT NOT NULL,
              read INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(entity,id));""")

    def send(self, body: str, delivery_id: str):
        text(body, 20_000)
        text(delivery_id, 150)
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT body FROM inbox WHERE entity=? AND id=?", (self.entity, delivery_id)).fetchone()
            if old and old[0] != body:
                raise EntityError("Delivery ID reused with different content")
            db.execute("INSERT OR IGNORE INTO inbox(entity,id,created,body) VALUES(?,?,?,?)",
                       (self.entity, delivery_id, time.time(), body))
        return {"delivered": "local_inbox", "message_id": delivery_id, "replayed": bool(old)}

    def unread(self):
        with self.store.connect() as db:
            return [dict(row) for row in db.execute("SELECT id,created,body FROM inbox WHERE entity=? AND read=0 ORDER BY created",
                                                    (self.entity,))]

    def mark_read(self, ident: str):
        with self.store.connect() as db:
            db.execute("UPDATE inbox SET read=1 WHERE entity=? AND id=?", (self.entity, ident))
