"""SOUL.md stays authoritative. Immutable prior bytes are kept as private local history."""
from __future__ import annotations
from pathlib import Path
from .common import EntityError, digest, private_dir, write_new_private
from .workspace import Workspace

class Identity:
    def __init__(self, home: Path):
        self.home = Path(home)
        self.files = Workspace(self.home)
        self.history = private_dir(self.home / "identity-history")

    def read(self) -> dict:
        result = self.files.read("SOUL.md")
        if result["bytes"] > 24_000:
            raise EntityError("Identity exceeds the established prompt budget")
        return {"text": result["content"], "sha256": result["sha256"], "authority": "SOUL.md"}

    def update(self, content: str, expected_sha256: str) -> dict:
        if not isinstance(content, str) or len(content.encode()) > 24_000 or not content.strip():
            raise EntityError("Invalid identity text")
        prior = self.read()
        if prior["sha256"] != expected_sha256:
            raise EntityError("Identity changed since review")
        path = self.history / (expected_sha256 + ".md")
        if path.exists():
            if path.is_symlink() or digest(path.read_bytes()) != expected_sha256:
                raise EntityError("Identity history collision")
        else:
            write_new_private(path, prior["text"].encode())
        result = self.files.write("SOUL.md", content, expected_sha256)
        return {"sha256": result["sha256"], "previous_sha256": expected_sha256,
                "applies": "next_runtime_start", "permissions_changed": False}

    def close(self):
        self.files.close()
