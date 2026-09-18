"""Reviewed knowledge packs. No importing Python, running scripts, or granting tools."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from .common import EntityError, canonical, digest, strict_json

@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    content: str
    sha256: str
    capabilities_requested: tuple[str, ...]
    files: tuple[str, ...]

class SkillLibrary:
    def __init__(self, root: Path, approved: dict[str, str] | None = None):
        self.root = Path(root).resolve(strict=True)
        self.approved = dict(approved or {})

    def inspect(self, name: str) -> Skill:
        if not name or "/" in name or "\\" in name or name in {".", ".."}:
            raise EntityError("Invalid skill name")
        folder = self.root / name
        if folder.is_symlink() or not folder.is_dir():
            raise EntityError("Skill folder missing or linked")
        manifest_path = folder / "skill.json"
        if manifest_path.is_symlink() or manifest_path.stat().st_size > 32_000:
            raise EntityError("Invalid skill manifest")
        manifest = strict_json(manifest_path.read_bytes())
        expected = {"schema", "name", "description", "files", "capabilities_requested"}
        if not isinstance(manifest, dict) or set(manifest) != expected or manifest["schema"] != "lelock.skill/1":
            raise EntityError("Unsupported skill schema")
        if manifest["name"] != name or not isinstance(manifest["description"], str):
            raise EntityError("Skill identity mismatch")
        files = manifest["files"]
        caps = manifest["capabilities_requested"]
        if not isinstance(files, list) or not 1 <= len(files) <= 20 or "SKILL.md" not in files:
            raise EntityError("Skill must declare a bounded file list including SKILL.md")
        if len(set(files)) != len(files) or not isinstance(caps, list) or any(not isinstance(c, str) for c in caps):
            raise EntityError("Invalid skill file/capability list")
        contents = {}
        total = 0
        for relative in files:
            if not isinstance(relative, str) or PurePosixPath(relative).is_absolute() or "\\" in relative:
                raise EntityError("Invalid skill path")
            if any(part in {"", ".", ".."} for part in relative.split("/")):
                raise EntityError("Skill traversal refused")
            path = folder
            for part in PurePosixPath(relative).parts:
                path = path / part
                if path.is_symlink():
                    raise EntityError("Linked skill content refused")
            if not path.is_file() or path.stat().st_size > 200_000:
                raise EntityError("Skill file is missing or too large")
            raw = path.read_bytes()
            total += len(raw)
            if total > 300_000:
                raise EntityError("Skill exceeds total budget")
            contents[relative] = raw.decode("utf-8")
        fingerprint = digest({"manifest": manifest, "contents": contents})
        return Skill(name, manifest["description"], contents["SKILL.md"], fingerprint, tuple(caps), tuple(files))

    def approve(self, name: str, reviewed_sha256: str):
        """Operator-side in-memory pin. Persist reviewed pins in private configuration separately."""
        skill = self.inspect(name)
        if skill.sha256 != reviewed_sha256:
            raise EntityError("Skill changed after review")
        self.approved[name] = reviewed_sha256

    def load(self, name: str) -> Skill:
        skill = self.inspect(name)
        if self.approved.get(name) != skill.sha256:
            raise EntityError("Skill not reviewed, or changed since review")
        return skill
