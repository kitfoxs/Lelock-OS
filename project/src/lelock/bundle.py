"""Selected-data export. No raw DB, credentials, transcript cache, executable files, or auto-activation."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from .common import LelockError, atomic_json, canonical, digest, read_json, text
from .service import validate_record

MAX_BUNDLE=10_000_000

def export(service,path: Path):
    path=path.expanduser().resolve()
    if path.exists(): raise LelockError('Choose a new export filename.')
    records=[]
    for ref in service.journal.refs(service.scope):
        if ref['active'] and ref['kind'] not in {'transcript','checkpoint'}: records.append(service.fetch(ref['id']))
    config=service.config
    payload={'schema':'lelock.datachip/1','identity':(service.home/'SOUL.md').read_text('utf-8'),
             'companion_name':config.companion_name,'person_name':config.person_name,
             'relationship':config.relationship,'scope':service.scope,'records':records,
             'export_note':'Selected active curated memories only. Credentials, endpoint, transcripts, tasks, and workspace files excluded.'}
    body={'payload':payload,'sha256':digest(payload)}
    if len(canonical(body).encode())>MAX_BUNDLE: raise LelockError('Export exceeds v0.1 limit; select a smaller profile.')
    atomic_json(path,body)
    return {'records':len(records),'file':str(path),'plaintext':True}

def inspect(path: Path):
    data=read_json(path,MAX_BUNDLE)
    if not isinstance(data,dict) or set(data)!={'payload','sha256'} or digest(data['payload'])!=data['sha256']:
        raise LelockError('Datachip integrity check failed.')
    p=data['payload']
    fields={'schema','identity','companion_name','person_name','relationship','scope','records','export_note'}
    if not isinstance(p,dict) or set(p)!=fields or p['schema']!='lelock.datachip/1': raise LelockError('Unsupported datachip.')
    text(p['identity'],maximum=24_000)
    if not isinstance(p['records'],list) or len(p['records'])>2000: raise LelockError('Too many records.')
    ids=set()
    for r in p['records']:
        validate_record(r)
        if r['id'] in ids or r['scope']!=p['scope'] or r['kind'] in {'transcript','checkpoint'}:
            raise LelockError('Duplicate, mismatched, or unsupported exported record.')
        ids.add(r['id'])
    return p

def restore_records(service,payload):
    if service.journal.refs(): raise LelockError('Restore only into a new, blank profile.')
    if service.scope!=payload['scope']: raise LelockError('Scope mismatch.')
    # A selected-data export may retain a supersedes pointer to a deliberately omitted old record.
    for r in payload['records']: service.store(r,allow_missing_predecessor=True)
    return {'restored_records':len(payload['records']),'history':'selected active memories, not a full disk clone'}
