#!/usr/bin/env python3
"""Actual Hermes + actual isolated Palace + explicitly selected model, across two processes.
Synthetic data only. Passing this is not a companion-quality, sandbox, or clinical claim.
"""
import argparse, json, os, subprocess, sys, tempfile
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'src'))
from lelock.config import initialize
from lelock.palace import ManagedPalace
from lelock.service import Service, make_record
from lelock.runtime import HermesRuntime


def worker(a):
    home=Path(a.home)
    with ManagedPalace(home) as rpc:
        service=Service(home,rpc)
        if a.stage=='first':
            service.store(make_record('Synthetic continuity test: Alex calls the project Amber Otter.',kind='project'))
        rt=HermesRuntime(service)
        try:
            if a.stage=='first':
                reply=rt.turn('This is a synthetic integration test. What is the project name I explicitly saved? Then propose creating proof.txt containing exactly hello. Use the available proposal tool. Do not claim the file exists before approval.')
                assert 'amber otter' in reply.lower(), 'Saved evidence was not reflected in the answer.'
                proposals=[p for p in service.journal.proposals() if p['kind']=='write']
                assert proposals, 'No file proposal.'
                assert not (service.workspace.root/'proof.txt').exists(), 'Unauthorized write.'
                # Test-controller authorization, not a model-facing tool or production bypass.
                chosen=None
                for proposal in proposals:
                    payload=json.loads(proposal['payload']) if isinstance(proposal['payload'],str) else proposal['payload']
                    if payload.get('path')=='proof.txt' and payload.get('content')=='hello': chosen=proposal;break
                assert chosen, 'Proposal did not match exact synthetic fixture.'
                service.approve(chosen['id'])
                assert (service.workspace.root/'proof.txt').read_text()=='hello'
                cp=service.checkpoint(rt.session['messages'],rt.session['id'])
                assert cp['status']=='durable'
                evidence={'stage':'first','status':'PASS','approved_synthetic_artifact':True,'durable_checkpoint':True}
            else:
                assert (service.workspace.root/'proof.txt').read_text()=='hello'
                answer=rt.turn('We are back after a process restart. What project name did I explicitly save? Read proof.txt using the available tool and report its actual content. Do not invent other completed work.')
                assert 'amber otter' in answer.lower() and 'hello' in answer.lower(), 'Restart answer missed synthetic continuity.'
                evidence={'stage':'restart','status':'PASS','persistent_history_loaded':True,'reply_for_human_review':answer}
            rt.assert_surface()
        finally:
            rt.close()
    Path(a.evidence).write_text(json.dumps(evidence,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--endpoint',required=True);p.add_argument('--model',required=True)
    p.add_argument('--label',choices=['A','B'],default='A')
    p.add_argument('--stage',choices=['first','restart']);p.add_argument('--home');p.add_argument('--evidence')
    a=p.parse_args()
    if a.stage:
        worker(a);return 0
    result={'gate':'full-stack-'+a.label,'status':'NOT_RUN'}
    try:
        with tempfile.TemporaryDirectory(prefix='lelock-full-stack-') as directory:
            root=Path(directory);home=root/'home'
            initialize(home,root/'workspace',name='Samantha',person='Alex',relationship='friendship',
                       endpoint=a.endpoint,model=a.model,retention='journal')
            steps=[]
            for stage in ('first','restart'):
                evidence=root/(stage+'.json')
                run=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--endpoint',a.endpoint,
                    '--model',a.model,'--label',a.label,'--stage',stage,'--home',str(home),'--evidence',str(evidence)],
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=420)
                if run.returncode:
                    raise RuntimeError('Stage failed: '+stage+'; rerun explicitly in this test environment to diagnose.')
                steps.append(json.loads(evidence.read_text()))
            result={'gate':'full-stack-'+a.label,'status':'PASS','model':a.model,'endpoint':a.endpoint,
                    'steps':steps,'synthetic_only':True,'private_palace_accessed':False}
    except Exception as exc:
        result={'gate':'full-stack-'+a.label,'status':'BLOCKED','reason_type':type(exc).__name__,
                'next':'Diagnose the isolated runtime and explicit endpoint; do not substitute fixtures or weaken assertions.'}
    receipt=P.parent/'receipts';receipt.mkdir(exist_ok=True)
    (receipt/('full-stack-'+a.label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return 0 if result['status']=='PASS' else 3

if __name__=='__main__': raise SystemExit(main())
