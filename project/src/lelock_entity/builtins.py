"""Trusted adapter registration. No user card/skill can add to this registry."""
from __future__ import annotations
from .common import EntityError, STRING, object_schema, strict_json
from .core import EntityCore, Tool
from .policy import Risk
from .workspace import Workspace
from .world import World


def install(core: EntityCore, workspace: Workspace, world: World, *, memory=None, runner=None, skills=None):
    core.register(Tool("lelock_status", "Inspect the actual entity session and enabled capabilities.",
                        "status.read", Risk.READ, object_schema({}), lambda args, session: core.status(session)))
    core.register(Tool("lelock_read_text", "Read bounded UTF-8 text inside the selected workspace.",
                        "workspace.read", Risk.READ, object_schema({"path": STRING}, ["path"]),
                        lambda args, session: workspace.read(args["path"])))
    write_schema = object_schema({"path": STRING, "content": STRING, "expected_sha256": STRING}, ["path", "content"])
    core.register(Tool("lelock_write_text", "Create a text file or replace exact reviewed bytes. Policy may require approval.",
                        "workspace.write", Risk.WRITE, write_schema,
                        lambda args, session: workspace.write(**args)))
    # Keep the familiar alpha spelling while routing through the same core. YOLO may commit immediately.
    core.register(Tool("lelock_propose_text", "Propose/create NEW text according to the current operator policy.",
                        "workspace.write", Risk.WRITE, object_schema({"path": STRING, "content": STRING}, ["path", "content"]),
                        lambda args, session: workspace.write(**args)))
    core.register(Tool("lelock_delete_text", "Delete one reviewed workspace text file; no recursive deletion.",
                        "workspace.delete", Risk.WRITE, object_schema({"path": STRING, "expected_sha256": STRING}, ["path", "expected_sha256"]),
                        lambda args, session: workspace.delete(**args)))
    core.register(Tool("lelock_world_inspect", "Inspect the fictional world. This does not inspect host files.",
                        "world.read", Risk.READ, object_schema({"id": STRING}),
                        lambda args, session: world.inspect(args.get("id", "home"))))
    def patch_world(args, session):
        operations = strict_json(args["operations_json"], max_bytes=300_000)
        if not isinstance(operations, list):
            raise EntityError("World operations must be a JSON array")
        return world.apply(args["expected_revision"], operations)
    core.register(Tool("lelock_world_apply", "Commit an exact fictional-world patch at a known revision.",
                        "world.write", Risk.WRITE, object_schema({"expected_revision": {"type": "integer", "minimum": 0},
                        "operations_json": {"type": "string", "maxLength": 300_000}}, ["expected_revision", "operations_json"]), patch_world))
    if memory is not None:
        core.register(Tool("lelock_recall", "Retrieve source-linked evidence from this profile's actual MemPalace.",
                            "memory.read", Risk.READ, object_schema({"query": STRING}, ["query"]),
                            lambda args, session: memory.recall(args["query"])))
        def commit_memory(args, session):
            return memory.commit(args["content"], kind=args.get("kind", "fact"), supersedes=args.get("supersedes", ""))
        core.register(Tool("lelock_propose_memory", "Propose memory/correction. SAFE asks; YOLO can commit under its explicit session grant.",
                            "memory.write", Risk.WRITE, object_schema({"content": STRING, "kind": {"type": "string", "enum": ["fact", "preference", "project", "episode", "fiction"]},
                            "supersedes": STRING}, ["content"]), commit_memory))
    if runner is not None and runner.backend != "none":
        core.register(Tool("lelock_run_process", "Execute a command using the operator-selected backend; host is UNSANDBOXED.",
                            "process.run", Risk.EXECUTE, object_schema({"script": STRING}, ["script"]),
                            lambda args, session: runner.run(args["script"])))
    if skills is not None:
        core.register(Tool("lelock_skill_read", "Load a reviewed, hash-pinned knowledge pack; it grants no permissions.",
                            "skills.read", Risk.READ, object_schema({"name": STRING}, ["name"]),
                            lambda args, session: {"name": (s := skills.load(args["name"])).name,
                              "content": s.content, "sha256": s.sha256, "permissions_granted": []}))
