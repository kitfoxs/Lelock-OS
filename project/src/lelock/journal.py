"""Exact operational state, not a second semantic memory store."""
from __future__ import annotations
import contextlib
import json
import sqlite3
import time
import uuid
from pathlib import Path
from .common import LelockError, canonical, private_dir

class Journal:
    def __init__(self,home: Path):
        private_dir(home)
        path=home/'operations.sqlite3'
        if path.is_symlink(): raise LelockError('Refusing linked journal.')
        self.path=path
        with self.connection() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY,kind TEXT NOT NULL,payload TEXT NOT NULL,
              state TEXT NOT NULL,created REAL NOT NULL,expires REAL NOT NULL,result TEXT);
            CREATE TABLE IF NOT EXISTS memory_refs(id TEXT PRIMARY KEY,drawer TEXT NOT NULL,scope TEXT NOT NULL,
              kind TEXT NOT NULL,supersedes TEXT NOT NULL DEFAULT '',active INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY,payload TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'pending',error TEXT);
            CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY,event TEXT NOT NULL,data TEXT NOT NULL,created REAL NOT NULL);
            """)
        path.chmod(0o600)

    @contextlib.contextmanager
    def connection(self):
        c=sqlite3.connect(self.path,timeout=10)
        c.row_factory=sqlite3.Row
        c.execute('PRAGMA synchronous=FULL')
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback();raise
        finally: c.close()

    def propose(self,kind: str,payload: dict, *, ttl: int = 1800) -> str:
        if kind not in {'write','memory','forget'}: raise LelockError('Unknown proposal type.')
        ident=uuid.uuid4().hex; now=time.time()
        with self.connection() as c:
            c.execute('INSERT INTO proposals VALUES(?,?,?,?,?,?,NULL)',(ident,kind,canonical(payload),'pending',now,now+ttl))
        return ident

    def proposals(self):
        with self.connection() as c:
            return [dict(r) for r in c.execute("SELECT * FROM proposals WHERE state IN ('pending','applying','needs_review') ORDER BY created")]

    def claim(self,ident: str):
        with self.connection() as c:
            c.execute('BEGIN IMMEDIATE')
            r=c.execute('SELECT * FROM proposals WHERE id=?',(ident,)).fetchone()
            if not r or r['state']!='pending' or r['expires']<time.time(): raise LelockError('Proposal missing, expired, or already consumed.')
            c.execute("UPDATE proposals SET state='applying' WHERE id=?",(ident,))
            return r['kind'],json.loads(r['payload'])

    def finish(self,ident: str,state: str,result: dict):
        with self.connection() as c:
            c.execute('UPDATE proposals SET state=?,result=?,payload=? WHERE id=?',
                      (state,canonical(result),'{}' if state=='done' else c.execute('SELECT payload FROM proposals WHERE id=?',(ident,)).fetchone()[0],ident))
        self.receipt('proposal_'+state,{'proposal_id':ident,**result})

    def reject(self,ident: str):
        with self.connection() as c:
            n=c.execute("UPDATE proposals SET state='rejected',payload='{}' WHERE id=? AND state='pending'",(ident,)).rowcount
            if n!=1: raise LelockError('No pending proposal with that ID.')

    def receipt(self,event: str,data: dict):
        with self.connection() as c:
            c.execute('INSERT INTO receipts VALUES(?,?,?,?)',(uuid.uuid4().hex,event,canonical(data),time.time()))

    def ref(self,ident: str):
        with self.connection() as c:
            r=c.execute('SELECT * FROM memory_refs WHERE id=?',(ident,)).fetchone()
            return dict(r) if r else None

    def refs(self,scope: str|None=None):
        with self.connection() as c:
            rows=c.execute('SELECT * FROM memory_refs'+(' WHERE scope=?' if scope else ''),((scope,) if scope else ()))
            return [dict(r) for r in rows]

    def index(self,record: dict,drawer: str):
        with self.connection() as c:
            c.execute('INSERT OR REPLACE INTO memory_refs VALUES(?,?,?,?,?,1)',
                      (record['id'],drawer,record['scope'],record['kind'],record.get('supersedes','')))
            if record.get('supersedes'):
                c.execute('UPDATE memory_refs SET active=0 WHERE id=?',(record['supersedes'],))

    def enqueue(self,ident: str,record: dict):
        with self.connection() as c:
            c.execute('INSERT OR IGNORE INTO outbox(id,payload) VALUES(?,?)',(ident,canonical(record)))

    def pending(self):
        with self.connection() as c:
            return [dict(r) for r in c.execute("SELECT * FROM outbox WHERE state='pending' ORDER BY rowid")]

    def ack(self,ident: str):
        with self.connection() as c: c.execute('DELETE FROM outbox WHERE id=?',(ident,))

    def deactivate(self,ident: str):
        with self.connection() as c: c.execute('UPDATE memory_refs SET active=0 WHERE id=?',(ident,))
