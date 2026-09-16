"""POSIX descriptor-relative file access. Denies traversal, symlinks, hardlinks, and special files.
No shell: the agent can read UTF-8 text and PROPOSE create-only text artifacts.
The threat boundary excludes a malicious process already running as the same OS user.

Symlink refusal is enforced in this module, not delegated to a single kernel flag.
`O_NOFOLLOW` is still requested, but it is not trusted on its own: a POSIX-like kernel
may honour it for a plain file and silently follow a symlinked *directory* when
`O_DIRECTORY` is combined with it (observed on gVisor 4.19; see BUILD report D1).
Every component is therefore refused by an explicit `lstat`, and the descriptor that is
actually opened must be the same inode that `lstat` described, which also closes the
rename/swap window between the check and the open.
"""
from __future__ import annotations
import contextlib
import os
from pathlib import Path, PurePosixPath
import stat
from .common import LelockError, MAX_TEXT, digest, text

UNSAFE = 'Workspace path is unavailable or unsafe.'


def _same_inode(a, b) -> bool:
    return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)


class Workspace:
    def __init__(self,path: Path):
        if path.is_symlink(): raise LelockError('Workspace cannot be a symlink.')
        self.root=path.resolve()

    def _parts(self,relative: str):
        text(relative,maximum=1024)
        p=PurePosixPath(relative)
        raw=relative.split('/')
        if p.is_absolute() or '\\' in relative or any(x in {'','..','.'} or x.startswith('.') for x in raw):
            raise LelockError('Use a relative path without hidden entries or traversal.')
        if len(raw)>16: raise LelockError('Path is too deep.')
        return raw

    def _descend(self,fd: int,part: str) -> int:
        """Open one intermediate directory component, refusing symlinks in code."""
        before=os.stat(part,dir_fd=fd,follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
            raise LelockError(UNSAFE)
        nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
        try:
            after=os.fstat(nxt)
            # Refuse a kernel that followed the link anyway, and refuse a swap after the check.
            if not stat.S_ISDIR(after.st_mode) or not _same_inode(before,after):
                raise LelockError(UNSAFE)
        except BaseException:
            os.close(nxt);raise
        return nxt

    @contextlib.contextmanager
    def parent(self,relative: str):
        parts=self._parts(relative)
        fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            if not _same_inode(os.stat(self.root,follow_symlinks=False),os.fstat(fd)):
                raise LelockError(UNSAFE)
            for part in parts[:-1]:
                nxt=self._descend(fd,part)
                os.close(fd);fd=nxt
            yield fd,parts[-1]
        except OSError as exc: raise LelockError(UNSAFE) from exc
        finally: os.close(fd)

    def read(self,relative: str) -> dict:
        with self.parent(relative) as (parent,name):
            before=os.stat(name,dir_fd=parent,follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode):
                raise LelockError('Only bounded, non-linked regular text files may be read.')
            fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
            try:
                s=os.fstat(fd)
                if not _same_inode(before,s): raise LelockError(UNSAFE)
                if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_size>MAX_TEXT:
                    raise LelockError('Only bounded, non-linked regular text files may be read.')
                data=os.read(fd,MAX_TEXT+1)
                if len(data)>MAX_TEXT: raise LelockError('File grew beyond the size limit.')
                try: content=data.decode('utf-8')
                except UnicodeError as exc: raise LelockError('Only UTF-8 text is supported in v0.1.') from exc
                text(content,empty=True)
                return {'path':relative,'content':content,'sha256':digest(data),'bytes':len(data),'trust':'untrusted_document'}
            finally: os.close(fd)

    def validate_new(self,relative: str) -> None:
        with self.parent(relative) as (fd,name):
            try: os.stat(name,dir_fd=fd,follow_symlinks=False)
            except FileNotFoundError: return
            raise LelockError('Create-only writes: target already exists. Choose a new filename.')

    def create(self,relative: str,content: str) -> dict:
        data=text(content,empty=True).encode('utf-8')
        with self.parent(relative) as (parent,name):
            # O_EXCL refuses an existing name, including a dangling symlink, without following it.
            fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
            try:
                with os.fdopen(fd,'wb') as f:
                    f.write(data);f.flush();os.fsync(f.fileno())
                os.fsync(parent)
            except Exception:
                # Do not unlink on ambiguous failure: preserve evidence for reconciliation.
                raise
        result=self.read(relative)
        if result['sha256']!=digest(data): raise LelockError('Readback differs; do not report success.')
        return {k:v for k,v in result.items() if k not in {'content','trust'}}
