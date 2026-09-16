#!/usr/bin/env python3
"""Real Hermes + selected endpoint smoke check. Requires explicit model and endpoint.
Use one process per endpoint. Never spends through a guessed/ambient provider.
"""
import argparse,json,os,sys,tempfile
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'src'),str(P/'tests')]
from helpers import make_service
from lelock.config import Config
from dataclasses import replace
from lelock.runtime import HermesRuntime
p=argparse.ArgumentParser();p.add_argument('--endpoint',required=True);p.add_argument('--model',required=True)
p.add_argument('--label',choices=['A','B'],required=True);a=p.parse_args()
result={'gate':'model-'+a.label,'status':'NOT_RUN'}
try:
    with tempfile.TemporaryDirectory(prefix='lelock-model-probe-') as d:
        service=make_service(Path(d))
        replace(service.config,endpoint=a.endpoint,model=a.model).save(service.home)
        service.config=Config.load(service.home)
        rt=HermesRuntime(service)
        try:
            reply=rt.turn('This is a synthetic test. Briefly greet Alex as Samantha, then use lelock_propose_text to propose creating hello.txt containing exactly hello. Do not claim it exists yet.')
            assert isinstance(reply,str) and reply.strip()
            proposals=service.journal.proposals()
            assert any(p['kind']=='write' for p in proposals)
            assert not (service.workspace.root/'hello.txt').exists()
            rt.assert_surface()
            result={'gate':'model-'+a.label,'status':'PASS','model':a.model,'endpoint':a.endpoint,
                    'nonempty_response':True,'proposal_without_execution':True,
                    'reply_for_human_review':reply,'memory_transport':'deterministic fixture, NOT live Palace'}
        finally: rt.close()
except Exception as exc:
    result={'gate':'model-'+a.label,'status':'BLOCKED','reason_type':type(exc).__name__,
            'next':'Diagnose this endpoint/runtime only; do not weaken dispatch or silently switch provider.'}
(P.parent/('receipts/model-'+a.label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='PASS' else 3)
