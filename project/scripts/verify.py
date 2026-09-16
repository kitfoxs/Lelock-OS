#!/usr/bin/env python3
"""Finite offline suite. Exit codes: 0 pass; 1 failure. No live checks masquerade as skipped passes."""
import json,os,platform,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parents[1]
required=('__init__.py','__main__.py','cli.py','runtime.py','palace.py','hermes_plugin.py')
missing=[name for name in required if not (P/'src/lelock'/name).is_file()]
if missing:
    print(json.dumps({'gate':'offline','status':'BLOCKED','exit_code':2,
          'reason':'Current application source is missing; see docs/SOURCE_RECOVERY.md.',
          'missing':missing,'tests_executed':0},indent=2))
    raise SystemExit(2)
receipt=P.parent/'receipts';receipt.mkdir(exist_ok=True)
env=dict(os.environ);env['PYTHONPATH']=str(P/'src')+os.pathsep+str(P/'tests')
started=time.time()
r=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(P/'tests'),'-v'],cwd=P,env=env,
                 stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(receipt/'offline-tests.log').write_text(r.stdout)
report={'gate':'offline','status':'PASS' if r.returncode==0 else 'FAIL','exit_code':r.returncode,
        'elapsed_seconds':round(time.time()-started,3),'python':platform.python_version(),
        'system':platform.system(),'evidence':'offline-tests.log',
        'does_not_prove':['actual MemPalace service','Hermes full runtime','model behaviour','macOS installation','zero-retention provider']}
(receipt/'offline-result.json').write_text(json.dumps(report,indent=2)+'\n')
print(r.stdout);print(json.dumps(report,indent=2));raise SystemExit(r.returncode)
