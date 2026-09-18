"""Offline demo, explicit-profile daemon and optional real Hermes chat. No automatic installation."""
from __future__ import annotations
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import tempfile
import time
import uuid
from .common import EntityError, canonical, private_dir, write_new_private
from .policy import Budget, Mode, Session
from .store import Store
from .core import EntityCore
from .workspace import Workspace
from .world import World
from .builtins import install
from .http_bridge import Bridge
from .execution import ProcessRunner
from .lifecycle import ProfileLease

DEFAULT_CAPS = {"status.read", "workspace.read", "workspace.write", "world.read", "world.write", "memory.read", "memory.write"}

def construct(args, home: Path, workspace_path: Path, entity: str, scope: str, memory=None):
    caps = set(args.cap) if args.cap else set(DEFAULT_CAPS)
    if memory is None:
        caps -= {"memory.read", "memory.write"}
    if args.exec_backend != "none":
        caps.add("process.run")
    session = Session(entity, scope, frozenset(caps), Mode(args.mode), frozenset(args.auto),
                      expires_at=time.time() + args.session_minutes * 60)
    state = private_dir(home / "entity-v02")
    store = Store(state)
    core = EntityCore(store, session, budget=Budget(max_actions=args.max_actions, seconds=args.session_minutes * 60))
    files = Workspace(workspace_path)
    runner = ProcessRunner(workspace_path, state / "execution", backend=args.exec_backend,
                           acknowledge_host_risk=args.ack_host_risk, image=args.docker_image,
                           network=args.docker_network, timeout=args.process_timeout, stop=core.stop)
    world = World(store, entity)
    install(core, files, world, memory=memory, runner=runner)
    return core, files


def _settings(parser):
    parser.add_argument("--mode", choices=[m.value for m in Mode], default="safe")
    parser.add_argument("--cap", action="append", default=[], help="Exact enabled capability; repeat. Replaces default capability set.")
    parser.add_argument("--auto", action="append", default=[], help="TRUSTED standing approval capability; repeat.")
    parser.add_argument("--session-minutes", type=int, default=120)
    parser.add_argument("--max-actions", type=int, default=200)
    parser.add_argument("--exec-backend", choices=["none", "host", "docker"], default="none")
    parser.add_argument("--ack-host-risk", action="store_true", help="Allow UNSANDBOXED commands as your OS user, beyond workspace boundaries.")
    parser.add_argument("--docker-image", default="", help="Already-pulled, operator-verified image@sha256:digest.")
    parser.add_argument("--docker-network", action="store_true")
    parser.add_argument("--process-timeout", type=int, default=60)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description="Lelock Entity Runtime reference foundation")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Offline real file/world operations in disposable directories, no model/Palace.")
    _settings(demo)
    for name in ("serve", "chat"):
        command = sub.add_parser(name)
        command.add_argument("--home", type=Path, required=True, help="Explicit existing owned Lelock alpha profile; never inferred.")
        _settings(command)
        if name == "serve":
            command.add_argument("--origin", action="append", default=[])
            command.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    if not 1 <= args.session_minutes <= 1440 or not 1 <= args.max_actions <= 100_000 or not 1 <= args.process_timeout <= 600:
        parser.error("Session/process budgets outside supported bounds")
    try:
        if args.mode == "yolo":
            print("YOLO: enabled capabilities auto-approve. Authentication, receipts, expiry and stop remain active.")
        if args.exec_backend == "host":
            print("HOST EXECUTION: UNSANDBOXED. Commands run as your OS user and can escape the workspace.")
        if args.command == "demo":
            with tempfile.TemporaryDirectory(prefix="lelock-entity-demo-") as temporary:
                home = private_dir(Path(temporary) / "home")
                workspace = private_dir(Path(temporary) / "workspace")
                core, files = construct(args, home, workspace, "demo-companion", "test")
                try:
                    action = core.invoke("lelock_propose_text", {"path": "hello.txt", "content": "Hello from Lelock Entity.\n"}, request_id="demo-write")
                    print(canonical(action))
                    if action["status"] == "pending_approval":
                        print("SAFE/TRUSTED demo leaves the file unwritten until explicit approval.")
                        core.reject(action["action_id"])
                    else:
                        print(canonical(core.invoke("lelock_read_text", {"path": "hello.txt"})))
                    print(canonical(core.invoke("lelock_world_inspect", {})))
                    if args.exec_backend != "none":
                        print(canonical(core.invoke("lelock_run_process", {"script": "printf 'real process execution\\n'"}, request_id="demo-process")))
                    print(canonical({"demo": "complete", "model_calls": 0, "palace_used": False, "status": core.status()}))
                finally:
                    files.close()
            return
        # Live commands require the existing installed alpha and its pinned upstream dependencies.
        from lelock.config import Config
        from lelock.palace import ManagedPalace
        from lelock.service import Service
        from .legacy import LegacyMemory, RuntimeServiceAdapter, RUNTIME_POLICY
        home = args.home.expanduser().resolve(strict=True)
        cfg = Config.load(home)
        with ExitStack() as stack:
            stack.enter_context(ProfileLease(home / "entity-v02"))
            rpc = stack.enter_context(ManagedPalace(home))
            service = Service(home, rpc)
            core, files = construct(args, home, Path(cfg.workspace), cfg.profile_id, service.scope, LegacyMemory(service))
            stack.callback(files.close)
            print(canonical({"session": core.session.ident, "state": str(core.store.directory), "mode": core.session.mode.value}))
            if args.command == "serve":
                bridge = Bridge(core, port=args.port, origins=tuple(args.origin)).start()
                stack.callback(bridge.close)
                credentials = bridge.credentials()
                agent_file = core.store.directory / ("agent-" + core.session.ident + ".json")
                operator_file = core.store.directory / ("operator-" + core.session.ident + ".json")
                write_new_private(agent_file, canonical({k: credentials[k] for k in ("base_url", "agent_token", "session")}).encode())
                write_new_private(operator_file, canonical({k: credentials[k] for k in ("base_url", "operator_token", "session")}).encode())
                print("Agent pairing file:", agent_file)
                print("Operator pairing file (never give to the model):", operator_file)
                print("Bridge ready. This tool daemon does not run background inference. Ctrl-C stops it.")
                try:
                    while not core.stop.event.wait(.2) and time.time() < core.session.expires_at:
                        pass
                finally:
                    core.stop.stop()
            else:
                # Runtime patch keeps native Hermes dispatch disabled, including HERMES_YOLO=0.
                from lelock.runtime import HermesRuntime
                adapter = RuntimeServiceAdapter(service, core)
                runtime = HermesRuntime(adapter, schemas=core.schemas(), policy=RUNTIME_POLICY)
                stack.callback(runtime.close)
                print("/actions, /approve ID DIGEST, /reject ID, /stop, /quit. No hidden model loop.")
                while not core.stop.event.is_set() and time.time() < core.session.expires_at:
                    line = input("You> ")
                    if line in {"/quit", "/stop"}:
                        core.stop.stop()
                        break
                    if line == "/actions":
                        print(canonical(core.store.pending(core.session.entity, core.session.ident)))
                    elif line.startswith("/approve "):
                        _, ident, fingerprint = line.split()
                        print(canonical(core.approve(ident, fingerprint)))
                    elif line.startswith("/reject "):
                        print(canonical(core.reject(line.split()[1])))
                    elif line.strip():
                        core.stop.check()
                        print("Companion>", runtime.turn(line))
    except KeyboardInterrupt:
        print("Stopped by operator.")
    except (EntityError, ImportError) as exc:
        raise SystemExit(str(exc)) from exc

if __name__ == "__main__":
    main()
