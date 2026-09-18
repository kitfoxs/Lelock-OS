"""One application owner per explicit profile. No global process discovery or killing."""
from __future__ import annotations
import fcntl
import os
from pathlib import Path
from .common import EntityError, private_dir

class ProfileLease:
    def __init__(self, directory: Path):
        self.directory = private_dir(directory)
        self.fd = None

    def __enter__(self):
        self.fd = os.open(self.directory / "entity-owner.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.close(self.fd)
            self.fd = None
            raise EntityError("Another Entity process owns this profile") from exc
        return self

    def __exit__(self, *_):
        if self.fd is not None:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            os.close(self.fd)
            self.fd = None
