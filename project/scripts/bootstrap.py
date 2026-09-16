#!/usr/bin/env python3
"""Prepare exact supplied sources and isolated upstream-locked runtimes.
No sudo, global installs, destructive checkout, user Palace discovery, or remote code pipes.
Dependency downloads need --allow-network. Source preparation is offline.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,stat,subprocess,sys,zipfile
from pathlib import Path,PurePosixPath

PROJECT=Path(__file__).resolve().parents[1]
PACKET=PROJECT.parent

def fail(message): raise SystemExit(message)

def extract(archive: Path,destination: Path,prefix: str):
    if destination.exists():
        marker=destination/'.lelock-source.json'
        if marker.exists() and json.loads(marker.read_text()).get('archive_sha256')==hashlib.sha256(archive.read_bytes()).hexdigest(): return
        fail('Refusing an existing unrecognized source directory: '+str(destination))
    staging=destination.with_name(destination.name+'.extracting')
    if staging.exists(): fail('Interrupted extraction exists; inspect it before retrying: '+str(staging))
    staging.mkdir(parents=True)
    with zipfile.ZipFile(archive) as z:
        if sum(i.file_size for i in z.infolist())>800_000_000: fail('Archive extraction budget exceeded.')
        for info in z.infolist():
            if not info.filename.startswith(prefix+'/'): fail('Unexpected archive root.')
            rel=PurePosixPath(info.filename[len(prefix)+1:])
            if rel.is_absolute() or '..' in rel.parts or '\\' in str(rel): fail('Unsafe archive path.')
            if not rel.parts: continue
            path=staging.joinpath(*rel.parts)
            if info.is_dir(): path.mkdir(parents=True,exist_ok=True);continue
            path.parent.mkdir(parents=True,exist_ok=True)
            if stat.S_ISLNK(info.external_attr>>16):
                # Materialize ONLY a regular in-archive file alias, never a filesystem symlink.
                target=PurePosixPath(z.read(info).decode())
                if target.is_absolute() or '..' in target.parts: fail('Unsafe source alias.')
                referred=str(PurePosixPath(info.filename).parent/target)
                origin=z.getinfo(referred)
                if origin.is_dir() or stat.S_ISLNK(origin.external_attr>>16): fail('Unsupported source alias chain.')
                data=z.read(origin)
            else: data=z.read(info)
            path.write_bytes(data)
            mode=0o755 if (info.external_attr>>16)&0o111 else 0o644
            path.chmod(mode)
    (staging/'.lelock-source.json').write_text(json.dumps({'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))
    staging.rename(destination)

def main():
    p=argparse.ArgumentParser();p.add_argument('--allow-network',action='store_true');a=p.parse_args()
    if not (3,11)<=sys.version_info[:2]<(3,14): fail('Use Python 3.11–3.13. Do not alter the system Python.')
    lock=json.loads((PROJECT/'resources/source-lock.json').read_text())
    runtime=PROJECT/'.runtime';runtime.mkdir(exist_ok=True)
    for name in ('hermes','mempalace'):
        item=lock['sources'][name];archive=PACKET/'upstream'/item['file']
        if not archive.is_file(): fail('Full source packet required: '+str(archive))
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=item['sha256']: fail('Source archive mismatch: '+name)
        extract(archive,runtime/name,item['root'])
    if not a.allow_network:
        print('Exact source trees prepared. No packages installed. Rerun with --allow-network to resolve the supplied upstream lockfiles.');return 0
    uv=shutil.which('uv')
    if not uv: fail('uv is required for frozen upstream locks. Install it by an approved official method, then rerun; no unpinned pip fallback.')
    env={k:v for k,v in os.environ.items() if k not in {'UV_PYTHON','PYTHONPATH','PYTHONHOME','VIRTUAL_ENV'}}
    for name in ('hermes','mempalace'):
        subprocess.run([uv,'sync','--frozen','--no-dev','--python',sys.executable,'--project',str(runtime/name)],check=True,env=env)
    hp=runtime/'hermes/.venv/bin/python'
    subprocess.run([uv,'pip','install','--python',str(hp),'--no-deps','-e',str(PROJECT)],check=True,env=env)
    launcher=PROJECT/'lelock'
    launcher.write_text('#!/bin/sh\nset -eu\nHERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
                       'export LELOCK_PALACE_PYTHON="$HERE/.runtime/mempalace/.venv/bin/python"\n'
                       'exec "$HERE/.runtime/hermes/.venv/bin/python" -m lelock "$@"\n')
    launcher.chmod(0o755)
    print('Isolated runtimes installed. Run ./lelock --help. Live compatibility tests are still required.')
    return 0

if __name__=='__main__': raise SystemExit(main())
