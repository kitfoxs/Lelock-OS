"""Bounded MCP JSON-RPC client for the supplied MemPalace 3.9.0 HTTP hub.
Only the managed, per-profile Palace is used. No discovery of Kit's private live Palace.
"""
from __future__ import annotations
import contextlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from .common import LelockError, canonical, private_dir, read_json
from .config import endpoint_url

TOOLS = {'mempalace_add_drawer','mempalace_get_drawer','mempalace_search',
         'mempalace_list_drawers','mempalace_delete_drawer'}
MAX_RPC_BYTES = 4_000_000

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise LelockError('Palace redirect refused.')

class PalaceRPC:
    def __init__(self,base: str,token: str, *, timeout: float = 30):
        self.base=endpoint_url(base,loopback_only=True)
        self.token=token
        self.timeout=timeout
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())

    def rpc(self,method: str,params: dict):
        ident=uuid.uuid4().hex
        raw=canonical({'jsonrpc':'2.0','id':ident,'method':method,'params':params}).encode()
        if len(raw)>MAX_RPC_BYTES: raise LelockError('Palace request too large.')
        req=urllib.request.Request(self.base+'/mcp',data=raw,headers={
            'Content-Type':'application/json','Authorization':'Bearer '+self.token})
        try:
            with self.opener.open(req,timeout=self.timeout) as response:
                data=response.read(MAX_RPC_BYTES+1)
            if len(data)>MAX_RPC_BYTES: raise LelockError('Palace response too large.')
            payload=json.loads(data)
        except (urllib.error.URLError,TimeoutError,ValueError,OSError) as exc:
            raise LelockError('Palace unavailable or returned an invalid response. Nothing acknowledged as saved.') from exc
        if payload.get('id')!=ident or payload.get('error') or 'result' not in payload:
            raise LelockError('Palace RPC rejected; inspect the private local service log.')
        return payload['result']

    def contract(self):
        result=self.rpc('tools/list',{})
        available={t['name']:t for t in result.get('tools',[])}
        if not TOOLS<=available.keys(): raise LelockError('Palace is missing required tools; contract check failed.')
        expected={'mempalace_add_drawer':{'wing','room','content'},
                  'mempalace_get_drawer':{'drawer_id'},'mempalace_search':{'query'},
                  'mempalace_delete_drawer':{'drawer_id'}}
        for name,required in expected.items():
            schema=available[name].get('inputSchema',{})
            if not required<=set(schema.get('properties',{})):
                raise LelockError('Palace tool schema changed; stop before writing.')
        return {'tools':sorted(TOOLS),'transport':'loopback-jsonrpc'}

    def call(self,name: str,args: dict) -> dict:
        if name not in TOOLS: raise LelockError('Palace operation is not allowed.')
        r=self.rpc('tools/call',{'name':name,'arguments':args})
        if r.get('isError'): raise LelockError('Palace tool failed; save is not confirmed.')
        if isinstance(r.get('structuredContent'),dict): out=r['structuredContent']
        else:
            parts=[p.get('text','') for p in r.get('content',[]) if p.get('type')=='text']
            try: out=json.loads(''.join(parts))
            except (ValueError,TypeError) as exc: raise LelockError('Unexpected Palace tool result.') from exc
        if not isinstance(out,dict) or out.get('error') or out.get('success') is False:
            raise LelockError('Palace operation did not succeed.')
        return out

class ManagedPalace:
    """Own only the subprocess started here. No global pkill, service replacement, or existing-hub writes."""
    def __init__(self,home: Path):
        self.home=home.resolve();self.process=None;self.log=None

    def __enter__(self):
        marker=read_json(self.home/'OWNED_BY_LELOCK.json')
        if marker.get('schema')!=1: raise LelockError('Not a Lelock-owned application home.')
        private_dir(self.home/'palace')
        state=self.home/'runtime'/'palace-host'
        private_dir(state)
        token=secrets.token_urlsafe(32)
        # Isolate config, server registry and cache from the person's existing Palace.
        env={k:v for k,v in os.environ.items() if not k.startswith(('MEMPALACE_','HERMES_')) and k not in {'PYTHONPATH','PYTHONHOME'}}
        env.update({'HOME':str(state),'XDG_CONFIG_HOME':str(state/'config'),
                    'MEMPALACE_PALACE_PATH':str(self.home/'palace'),
                    'MEMPALACE_MCP_HTTP_TOKEN':token,'ANONYMIZED_TELEMETRY':'False'})
        self.log=open(self.home/'runtime'/'palace.log','ab',buffering=0)
        cand=Path(__file__).resolve().parents[2]/'.runtime/mempalace/.venv/bin/python'
        default_python=str(cand) if cand.exists() and os.access(cand,os.X_OK) else sys.executable
        palace_python=os.environ.get('LELOCK_PALACE_PYTHON',default_python)
        if not Path(palace_python).is_absolute() or not os.access(palace_python,os.X_OK):
            raise LelockError('Palace runtime interpreter is unavailable.')
        argv=[palace_python,'-m','mempalace.mcp_server','--transport','http',
              '--host','127.0.0.1','--port','0','--palace',str(self.home/'palace')]
        self.process=subprocess.Popen(argv,env=env,cwd=state,stdin=subprocess.DEVNULL,
                                      stdout=self.log,stderr=self.log,start_new_session=True)
        deadline=time.monotonic()+45
        try:
            while time.monotonic()<deadline:
                if self.process.poll() is not None: raise LelockError('Managed Palace exited; see runtime/palace.log. Existing Palace was not touched.')
                for path in (state/'.mempalace/server').glob('*/serverinfo.json'):
                    with contextlib.suppress(LelockError,ValueError):
                        info=read_json(path)
                        if info.get('pid')==self.process.pid and Path(info.get('palace_path','')).resolve()==(self.home/'palace').resolve():
                            rpc=PalaceRPC(f"http://127.0.0.1:{int(info['port'])}",token)
                            rpc.contract()
                            self.rpc=rpc
                            return rpc
                time.sleep(.15)
            raise LelockError('Palace did not become ready within its startup bound. Inspect the local log; do not touch another Palace.')
        except BaseException:
            self.__exit__(None,None,None);raise

    def __exit__(self,*exc):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try: self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill();self.process.wait(timeout=5)
        if self.log: self.log.close()
