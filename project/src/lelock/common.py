"""Small bounded IO primitives. No shell execution, network, or import side effects."""
from __future__ import annotations
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any

class LelockError(RuntimeError):
    """Expected, user-actionable failure; do not print credentials/tracebacks by default."""

MAX_TEXT = 128_000

def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def text(value: Any, *, maximum: int = MAX_TEXT, empty: bool = False) -> str:
    if not isinstance(value, str) or len(value.encode('utf-8', errors='replace')) > maximum:
        raise LelockError("Expected bounded UTF-8 text.")
    if not empty and not value.strip():
        raise LelockError("Text must not be empty.")
    try:
        value.encode('utf-8', errors='strict')
    except UnicodeError as exc:
        raise LelockError("Invalid Unicode text.") from exc
    if '\x00' in value:
        raise LelockError("NUL bytes are not accepted.")
    return value

def display(value: str) -> str:
    # Render control bytes as visible escapes, not terminal instructions (OSC 52, etc.).
    out = []
    for c in str(value):
        n = ord(c)
        if c in '\n\t' or (n >= 32 and not 127 <= n <= 159 and n not in range(0x202a,0x202f) and n not in range(0x2066,0x206a)):
            out.append(c)
        else:
            out.append(f'\\u{n:04x}')
    return ''.join(out)

def private_dir(path: Path) -> None:
    """Ensure this exact directory exists at 0700. Ancestors may legitimately be links
    (macOS /tmp and /var are symlinks), but the leaf itself must not be one.

    `Path.mkdir(exist_ok=True)` swallows the error for an existing symlink-to-directory
    because its fallback `is_dir()` resolves the link, and `os.chmod` by path follows it
    too. The guarantee is therefore re-established through a descriptor: the opened
    directory must be the same inode `lstat` reported. See BUILD report D2.
    """
    if path.is_symlink():
        raise LelockError("Refusing symlinked application directory.")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as exc:
        raise LelockError("Refusing symlinked application directory.") from exc
    try:
        link = os.lstat(path)
        opened = os.fstat(fd)
        if (stat.S_ISLNK(link.st_mode) or not stat.S_ISDIR(opened.st_mode)
                or (link.st_dev, link.st_ino) != (opened.st_dev, opened.st_ino)):
            raise LelockError("Refusing symlinked application directory.")
        os.fchmod(fd, 0o700)
    finally:
        os.close(fd)

def atomic_json(path: Path, value: Any) -> None:
    atomic_bytes(path, (canonical(value)+'\n').encode('utf-8'))

def atomic_bytes(path: Path, data: bytes) -> None:
    private_dir(path.parent)
    if path.is_symlink():
        raise LelockError("Refusing to replace a symlink.")
    fd, tmp = tempfile.mkstemp(prefix='.lelock-', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd,'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
        d = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(d)
        finally: os.close(d)
    finally:
        with contextlib.suppress(FileNotFoundError): os.unlink(tmp)

def read_json(path: Path, max_bytes: int = 2_000_000) -> Any:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > max_bytes:
        raise LelockError("Missing, linked, or oversized JSON file.")
    try: return json.loads(path.read_text('utf-8'))
    except (ValueError, UnicodeError) as exc: raise LelockError("Invalid JSON file.") from exc

@contextlib.contextmanager
def home_lock(home: Path):
    """POSIX process lock; process death releases it. Never delete another owner's file."""
    import fcntl
    private_dir(home)
    path=home/'session.lock'
    fd=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc: raise LelockError('This Lelock home is already in use.') from exc
        yield
    finally:
        os.close(fd)
