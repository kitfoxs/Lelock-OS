"""Real process execution. Host backend is intentionally NOT sandboxed; operator must opt in."""
from __future__ import annotations
from dataclasses import dataclass, field
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time
import uuid
from .common import EntityError, private_dir
from .policy import StopSignal

@dataclass
class ProcessRunner:
    workspace: Path
    state: Path
    backend: str = "none"
    acknowledge_host_risk: bool = False
    image: str = ""
    network: bool = False
    timeout: float = 60
    output_limit: int = 256_000
    stop: StopSignal = field(default_factory=StopSignal)

    def __post_init__(self):
        self.workspace = Path(self.workspace).resolve(strict=True)
        self.state = private_dir(self.state)
        if self.backend == "host" and not self.acknowledge_host_risk:
            raise EntityError("Host execution is unsandboxed; explicit operator acknowledgement required")
        if self.backend not in {"none", "host", "docker"}:
            raise EntityError("Unknown execution backend")
        if self.backend == "docker" and "@sha256:" not in self.image:
            raise EntityError("Choose and verify an immutable Docker image digest")

    def command(self, script: str, container_name: str) -> list[str]:
        if self.backend == "none":
            raise EntityError("Process execution was not enabled")
        if self.backend == "host":
            return ["/bin/sh", "-c", script]
        # No host HOME, credential paths or Docker socket are mounted into the container.
        return ["docker", "run", "--rm", "--pull=never", "--name", container_name,
                "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                "--pids-limit=128", "--memory=2g", "--cpus=2",
                "--network=" + ("bridge" if self.network else "none"),
                "--user", f"{os.getuid()}:{os.getgid()}",
                "--tmpfs", "/tmp:rw,nosuid,nodev,size=128m", "--env", "HOME=/tmp",
                "--mount", f"type=bind,src={self.workspace},dst=/workspace",
                "--workdir", "/workspace", self.image, "/bin/sh", "-c", script]

    def run(self, script: str) -> dict:
        if not isinstance(script, str) or not script or len(script.encode()) > 64_000:
            raise EntityError("Expected a bounded command script")
        self.stop.check()
        name = "lelock-" + uuid.uuid4().hex
        argv = self.command(script, name)
        home = private_dir(self.state / "process-home")
        # Intentionally no API keys, SSH agent, cloud creds or inherited PYTHONPATH.
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home),
               "LANG": "C.UTF-8", "TMPDIR": str(home)}
        process = subprocess.Popen(argv, cwd=self.workspace, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        started = time.monotonic()
        data = bytearray()
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        failure = None
        try:
            while selector.get_map():
                if self.stop.event.is_set():
                    failure = "cancelled"
                    break
                if time.monotonic() - started > self.timeout:
                    failure = "timed_out"
                    break
                for key, _ in selector.select(.05):
                    chunk = os.read(key.fileobj.fileno(), 16384)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        data.extend(chunk)
                        if len(data) > self.output_limit:
                            failure = "output_limit"
                            break
                if failure:
                    break
            if failure:
                raise EntityError(f"Process {failure}; inspect effects before retrying")
            remaining = max(.01, self.timeout - (time.monotonic() - started))
            code = process.wait(timeout=remaining)
            return {"exit_code": code, "stdout": data.decode("utf-8", errors="replace"),
                    "backend": self.backend, "sandboxed": self.backend == "docker",
                    "elapsed_seconds": round(time.monotonic() - started, 3)}
        except subprocess.TimeoutExpired as exc:
            raise EntityError("Process timed out; effects may already have occurred") from exc
        finally:
            selector.close()
            # Also clean up remaining same-group descendants, even after the leader exits.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                process.wait(timeout=.5)
            except subprocess.TimeoutExpired:
                pass
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            process.wait(timeout=2)
            process.stdout.close()
            if self.backend == "docker":
                # This exact generated container only. Never a global prune/kill command.
                subprocess.run(["docker", "rm", "-f", name], env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, check=False)
