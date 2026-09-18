#!/usr/bin/env python3
"""Repository-local repeatable check; no packet path or private runtime needed."""
from pathlib import Path
import os,subprocess,sys
project=Path(__file__).resolve().parents[1];repo=project.parent
rakazo=repo/'integrations/rakazo-v03';tavern=repo/'integrations/tavern-v03'
env=dict(os.environ,PYTHONPATH=str(project/'src'),LELOCK_V03_FIXTURES=str(project/'tests_tavern_v03/fixtures'),PYTHONDONTWRITEBYTECODE='1',TERM='dumb')
for cmd,cwd in [(['tsc','-p','tsconfig.json'],rakazo),([sys.executable,'-m','unittest','discover','-s',str(project/'tests_tavern_v03'),'-v'],repo),(['node','--test','tests/direct.test.mjs'],rakazo),(['node','--test','tests/controller.test.mjs'],tavern)]:
    r=subprocess.run(cmd,cwd=cwd,env=env)
    if r.returncode:raise SystemExit(r.returncode)
print('New connected tests passed. This is not live account/model/Palace/Docker/browser acceptance.')
