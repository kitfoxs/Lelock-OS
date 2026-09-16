#!/usr/bin/env python3
"""One real, synthetic, isolated Palace round trip. Never points at an existing Palace."""
import json,os,sys,tempfile
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'src'))
if 'LELOCK_PALACE_PYTHON' not in os.environ:
    cand = P / '.runtime/mempalace/.venv/bin/python'
    if cand.exists(): os.environ['LELOCK_PALACE_PYTHON'] = str(cand)
from lelock.config import initialize
from lelock.palace import ManagedPalace
from lelock.service import Service,make_record
result={'gate':'live-palace','status':'NOT_RUN'}
try:
    with tempfile.TemporaryDirectory(prefix='lelock-palace-probe-') as folder:
        root=Path(folder);home=root/'home'
        initialize(home,root/'workspace',name='Test Companion',person='Synthetic Tester',relationship='friendship',
                   endpoint='http://127.0.0.1:1234/v1',model='not-used',retention='journal')
        with ManagedPalace(home) as rpc:
            service=Service(home,rpc)
            r=make_record('Synthetic test: the favorite mineral is amethyst.')
            drawer=service.store(r)
            assert service.fetch(r['id'])==r
            hits=service.recall('favorite mineral')
            assert any(x['id']==r['id'] for x in hits['memories'])
            cp=service.checkpoint([{'role':'user','content':'synthetic checkpoint'}],'synthetic-session')
            assert cp['status']=='durable'
            result={'gate':'live-palace','status':'PASS','write_read_recall_checkpoint':True,'data':'synthetic-only','private_palace_accessed':False}
except Exception as exc:
    result={'gate':'live-palace','status':'BLOCKED','reason_type':type(exc).__name__,
            'next':'Inspect isolated service log during rerun; check installed dependencies/contracts. Do not use the private Palace as a workaround.'}
(P.parent/'receipts/live-palace.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='PASS' else 3)
