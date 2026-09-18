"""Operational mappings and turn receipts. MemPalace remains semantic memory authority."""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import json, sqlite3, time, uuid
from .common import BridgeError, canonical, digest, private

class Database:
    def __init__(self,root:Path):
        self.root=private(root);self.path=self.root/"tavern.sqlite3"
        if self.path.is_symlink(): raise BridgeError("Linked database refused")
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS entities(id TEXT PRIMARY KEY, card TEXT NOT NULL,
              config TEXT NOT NULL, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS bindings(client TEXT NOT NULL, card_key TEXT NOT NULL,
              entity TEXT NOT NULL, PRIMARY KEY(client,card_key));
            CREATE TABLE IF NOT EXISTS turns(id TEXT PRIMARY KEY, entity TEXT NOT NULL,
              chat TEXT NOT NULL, request_hash TEXT NOT NULL, state TEXT NOT NULL,
              request TEXT NOT NULL, result TEXT, created REAL NOT NULL, parent TEXT);
            CREATE TABLE IF NOT EXISTS turn_events(seq INTEGER PRIMARY KEY AUTOINCREMENT,
              turn_id TEXT NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS tool_results(entity TEXT NOT NULL, session TEXT NOT NULL,
              request_id TEXT NOT NULL, request_hash TEXT NOT NULL, result TEXT NOT NULL,
              PRIMARY KEY(entity,session,request_id));
            """)
        self.path.chmod(0o600)

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=10);db.row_factory=sqlite3.Row
        db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
        try: yield db;db.commit()
        except BaseException: db.rollback();raise
        finally: db.close()

    def bind(self,client,key,card,config,attach=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            prior=db.execute("SELECT entity FROM bindings WHERE client=? AND card_key=?",(client,key)).fetchone()
            if prior:
                if attach and prior[0]!=attach: raise BridgeError("Binding exists; explicit detach required")
                return prior[0],False
            entity=attach or uuid.uuid4().hex
            if attach:
                if not db.execute("SELECT 1 FROM entities WHERE id=?",(entity,)).fetchone():
                    raise BridgeError("Cannot attach unknown entity")
            else:
                db.execute("INSERT INTO entities VALUES(?,?,?,?)",(entity,canonical(card),canonical(config),time.time()))
            db.execute("INSERT INTO bindings VALUES(?,?,?)",(client,key,entity))
            return entity,True

    def entity(self,entity):
        with self.connect() as db:r=db.execute("SELECT * FROM entities WHERE id=?",(entity,)).fetchone()
        if r is None:raise BridgeError("Unknown entity")
        return {"id":r['id'],"card":json.loads(r['card']),"config":json.loads(r['config'])}

    def list_entities(self):
        with self.connect() as db:
            return [{"id":r['id'],"name":json.loads(r['card'])['name']} for r in db.execute("SELECT id,card FROM entities ORDER BY created")]

    def update_config(self,entity,config):
        self.entity(entity)
        with self.connect() as db:db.execute("UPDATE entities SET config=? WHERE id=?",(canonical(config),entity))

    def start_turn(self,tid,entity,chat,request,parent=None):
        h=digest({"entity":entity,"chat":chat,"request":request,"parent":parent})
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old=db.execute("SELECT request_hash FROM turns WHERE id=?",(tid,)).fetchone()
            if old:
                if old[0]!=h:raise BridgeError("Turn ID reused with different input")
                return False
            db.execute("INSERT INTO turns VALUES(?,?,?,?,?,?,NULL,?,?)",
                       (tid,entity,chat,h,'queued',canonical(request),time.time(),parent))
        return True

    def turn(self,tid):
        with self.connect() as db:r=db.execute("SELECT * FROM turns WHERE id=?",(tid,)).fetchone()
        if r is None:raise BridgeError("Unknown turn")
        return {**dict(r),"request":json.loads(r['request']),"result":json.loads(r['result']) if r['result'] else None}

    def finish(self,tid,state,result=None):
        with self.connect() as db:
            db.execute("UPDATE turns SET state=?,result=? WHERE id=?",(state,canonical(result) if result is not None else None,tid))

    def event(self,tid,kind,data):
        with self.connect() as db:db.execute("INSERT INTO turn_events(turn_id,kind,data,created) VALUES(?,?,?,?)",(tid,kind,canonical(data),time.time()))

    def events(self,tid,after=0):
        with self.connect() as db:
            return [{**dict(r),'data':json.loads(r['data'])} for r in db.execute(
                "SELECT seq,kind,data FROM turn_events WHERE turn_id=? AND seq>? ORDER BY seq LIMIT 1000",(tid,after))]

    def recover(self):
        # Single gateway process lease must already be held. No execution is replayed.
        with self.connect() as db:db.execute("UPDATE turns SET state='needs_review' WHERE state IN ('queued','running','waiting_approval')")

    def cached_tool(self,entity,session,rid,args):
        with self.connect() as db:r=db.execute("SELECT * FROM tool_results WHERE entity=? AND session=? AND request_id=?",(entity,session,rid)).fetchone()
        if r is None:return None
        if r['request_hash']!=digest(args):raise BridgeError("Tool request ID reused")
        return json.loads(r['result'])

    def cache_tool(self,entity,session,rid,args,result):
        with self.connect() as db:db.execute("INSERT OR REPLACE INTO tool_results VALUES(?,?,?,?,?)",(entity,session,rid,digest(args),canonical(result)))
