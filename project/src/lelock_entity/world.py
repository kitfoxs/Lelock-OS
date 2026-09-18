"""Small revisioned Markdown world. It never treats fictional paths as host filesystem authority."""
from __future__ import annotations
import copy
import json
import re
import time
from .common import EntityError, canonical, digest, text
from .store import Store

class World:
    def __init__(self, store: Store, entity: str):
        self.store, self.entity = store, entity
        with store.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS worlds(entity TEXT PRIMARY KEY, revision INTEGER NOT NULL, state TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS world_events(entity TEXT NOT NULL, revision INTEGER NOT NULL,
              created REAL NOT NULL, patch TEXT NOT NULL, sha256 TEXT NOT NULL,
              PRIMARY KEY(entity,revision));
            """)
            initial = {"schema": "lelock.world/1", "kind": "fictional_world", "nodes": {
                "home": {"kind": "room", "name": "Home", "markdown": "A quiet place to begin.", "source_refs": []}}, "edges": []}
            db.execute("INSERT OR IGNORE INTO worlds VALUES(?,0,?)", (entity, canonical(initial)))

    def snapshot(self) -> dict:
        with self.store.connect() as db:
            row = db.execute("SELECT * FROM worlds WHERE entity=?", (self.entity,)).fetchone()
        return {"revision": row["revision"], "state": json.loads(row["state"]), "sha256": digest(json.loads(row["state"]))}

    @staticmethod
    def identifier(value):
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
            raise EntityError("World IDs must be simple identifiers, not filesystem paths")
        return value

    @classmethod
    def validate_state(cls, state: dict):
        nodes = state["nodes"]
        if "home" not in nodes or nodes["home"]["kind"] != "room" or len(nodes) > 10_000:
            raise EntityError("Invalid world root/size")
        for ident, node in nodes.items():
            cls.identifier(ident)
            if node["kind"] not in {"room", "object", "book"}:
                raise EntityError("Unknown world node type")
            text(node["name"], 250)
            text(node.get("markdown", ""), 200_000, empty=True)
            if not isinstance(node.get("source_refs"), list) or any(not isinstance(s, str) for s in node["source_refs"]):
                raise EntityError("Source references must be opaque text identifiers")
            if node["kind"] != "room":
                parent = nodes.get(node.get("room"))
                if not parent or parent["kind"] != "room":
                    raise EntityError("Objects and books must belong to an existing room")
        for edge in state["edges"]:
            if len(edge) != 2 or edge[0] == edge[1] or any(nodes.get(n, {}).get("kind") != "room" for n in edge):
                raise EntityError("Room connection is invalid")
        if len({tuple(e) for e in state["edges"]}) != len(state["edges"]):
            raise EntityError("Duplicate room connection")
        if len(canonical(state).encode()) > 8_000_000:
            raise EntityError("World exceeds this reference implementation's size budget")

    def apply(self, expected_revision: int, operations: list[dict]) -> dict:
        if isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or not 1 <= len(operations) <= 100:
            raise EntityError("Invalid world revision/patch")
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM worlds WHERE entity=?", (self.entity,)).fetchone()
            if row["revision"] != expected_revision:
                raise EntityError("Stale world revision; inspect again before proposing")
            state = json.loads(row["state"])
            nodes = state["nodes"]
            for op in operations:
                if not isinstance(op, dict):
                    raise EntityError("World operation must be an object")
                action = op.get("op")
                if action == "add":
                    if not set(op) <= {"op", "id", "kind", "name", "markdown", "room", "source_refs"}:
                        raise EntityError("Unknown world operation field")
                    ident = self.identifier(op["id"])
                    if ident in nodes:
                        raise EntityError("World node already exists")
                    node = {"kind": op["kind"], "name": op["name"], "markdown": op.get("markdown", ""),
                            "source_refs": op.get("source_refs", [])}
                    if node["kind"] != "room":
                        node["room"] = op["room"]
                    nodes[ident] = node
                elif action == "connect":
                    if set(op) != {"op", "from", "to"}:
                        raise EntityError("Invalid connect operation")
                    state["edges"].append(sorted([op["from"], op["to"]]))
                elif action == "move":
                    if set(op) != {"op", "id", "room"} or op["id"] not in nodes or nodes[op["id"]]["kind"] == "room":
                        raise EntityError("Invalid move operation")
                    nodes[op["id"]]["room"] = op["room"]
                elif action == "edit":
                    if not {"op", "id"} < set(op) <= {"op", "id", "name", "markdown", "source_refs"} or op["id"] not in nodes:
                        raise EntityError("Invalid edit operation")
                    nodes[op["id"]].update({k: v for k, v in op.items() if k not in {"op", "id"}})
                else:
                    raise EntityError("Unknown world operation")
            self.validate_state(state)
            revision = expected_revision + 1
            state_digest = digest(state)
            db.execute("UPDATE worlds SET revision=?,state=? WHERE entity=?", (revision, canonical(state), self.entity))
            db.execute("INSERT INTO world_events VALUES(?,?,?,?,?)",
                       (self.entity, revision, time.time(), canonical(operations), state_digest))
        return {"revision": revision, "sha256": state_digest, "applied": len(operations)}

    def inspect(self, ident: str = "home") -> dict:
        snapshot = self.snapshot()
        node = snapshot["state"]["nodes"].get(ident)
        if node is None:
            raise EntityError("World node not found")
        children = {k: v for k, v in snapshot["state"]["nodes"].items() if v.get("room") == ident}
        exits = [next(n for n in edge if n != ident) for edge in snapshot["state"]["edges"] if ident in edge]
        return {"id": ident, "revision": snapshot["revision"], "node": node, "contents": children, "exits": exits,
                "fictional": True, "host_permissions_granted": False}
