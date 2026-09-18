"""Descriptor-relative text access. Not a security sandbox for arbitrary host processes."""
from __future__ import annotations
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path, PurePosixPath
import stat
import threading
import uuid
from .common import EntityError, digest

MAX_TEXT = 1_000_000

class Workspace:
    def __init__(self, root: Path):
        root = Path(root).absolute()
        if root.is_symlink() or not root.is_dir():
            raise EntityError("Choose an existing, non-symlink workspace")
        self.root = root.resolve()
        self._lock = threading.RLock()
        self._root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)

    def close(self):
        if self._root_fd is not None:
            os.close(self._root_fd)
            self._root_fd = None

    @contextmanager
    def parent(self, relative: str):
        if not isinstance(relative, str) or not relative or "\\" in relative or "\0" in relative:
            raise EntityError("Invalid relative path")
        path = PurePosixPath(relative)
        # Reject noncanonical paths rather than silently normalize caller intent.
        if path.is_absolute() or any(part in {"", ".", ".."} for part in relative.split("/")):
            raise EntityError("Path must be canonical and workspace-relative")
        if any(part.startswith(".lelock-") for part in path.parts):
            raise EntityError("Reserved workspace metadata path")
        with self._lock:
            fd = os.dup(self._root_fd)
            lock_fd = None
            try:
                lock_fd = os.open(".lelock-workspace.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
                                  0o600, dir_fd=self._root_fd)
                info = os.fstat(lock_fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise EntityError("Invalid workspace lock")
                fcntl.flock(lock_fd, fcntl.LOCK_EX)
                for part in path.parts[:-1]:
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    os.close(fd)
                    fd = child
                yield fd, path.name
            except OSError as exc:
                raise EntityError("Workspace path unavailable or refused") from exc
            finally:
                os.close(fd)
                if lock_fd is not None:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    os.close(lock_fd)

    def _read(self, directory: int, name: str) -> bytes:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MAX_TEXT:
                raise EntityError("Only bounded, unlinked regular text files are supported")
            with os.fdopen(fd, "rb", closefd=False) as stream:
                raw = stream.read(MAX_TEXT + 1)
            if len(raw) > MAX_TEXT:
                raise EntityError("File exceeds text budget")
            raw.decode("utf-8")
            return raw
        except UnicodeError as exc:
            raise EntityError("Expected UTF-8 text") from exc
        finally:
            os.close(fd)

    def read(self, path: str) -> dict:
        with self.parent(path) as (fd, name):
            raw = self._read(fd, name)
        return {"path": path, "content": raw.decode(), "sha256": digest(raw), "bytes": len(raw)}

    def write(self, path: str, content: str, expected_sha256: str | None = None) -> dict:
        if not isinstance(content, str) or len(content.encode()) > MAX_TEXT:
            raise EntityError("Text exceeds workspace budget")
        raw = content.encode()
        with self.parent(path) as (fd, name):
            if expected_sha256 is not None:
                if digest(self._read(fd, name)) != expected_sha256:
                    raise EntityError("File changed since review")
            else:
                try:
                    os.stat(name, dir_fd=fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise EntityError("Existing file requires an expected hash")
            temporary = ".lelock-write-" + uuid.uuid4().hex
            out = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
            try:
                with os.fdopen(out, "wb", closefd=False) as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                if expected_sha256 is None:
                    # Atomic no-replace create, even if another writer appears after validation.
                    os.link(temporary, name, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
                    os.unlink(temporary, dir_fd=fd)
                else:
                    os.replace(temporary, name, src_dir_fd=fd, dst_dir_fd=fd)
                os.fsync(fd)
                verified = self._read(fd, name)
                if verified != raw:
                    raise EntityError("Write readback mismatch")
            finally:
                os.close(out)
                try:
                    os.unlink(temporary, dir_fd=fd)
                except FileNotFoundError:
                    pass
        return {"path": path, "bytes": len(raw), "sha256": digest(raw), "verified": True}

    def delete(self, path: str, expected_sha256: str) -> dict:
        with self.parent(path) as (fd, name):
            if digest(self._read(fd, name)) != expected_sha256:
                raise EntityError("Delete target changed since review")
            os.unlink(name, dir_fd=fd)
            os.fsync(fd)
        return {"path": path, "deleted": True, "prior_sha256": expected_sha256}
