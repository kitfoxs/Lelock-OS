"""Minimal standard stdio MCP tools server; no HTTP MCP, SDK dependency, or operator capability.
Negotiates only the declared protocol versions. External native handshake still needs live acceptance.
"""
from __future__ import annotations
import argparse, json, os, sys, urllib.request, urllib.error, uuid
from pathlib import Path
from urllib.parse import urlsplit
from .common import BridgeError, canonical, strict_load
SUPPORTED={'2024-11-05','2025-03-26','2025-06-18'}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**kw):raise BridgeError('Redirect refused')
class MCP:
    def __init__(self,pairing):
        if pairing.is_symlink() or pairing.stat().st_mode & 0o077:raise BridgeError('Pairing file must be private')
        p=strict_load(pairing.read_bytes());url=urlsplit(p['base'])
        if url.scheme!='http' or url.hostname not in {'127.0.0.1','localhost'} or not url.port or url.path or url.query or url.username:
            raise BridgeError('Expected loopback pairing')
        self.base=p['base'];self.token=p['token'];self.initialized=False
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    def api(self,path,data=None):
        req=urllib.request.Request(self.base+path,data=None if data is None else canonical(data).encode(),
            headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'})
        with self.opener.open(req,timeout=330) as r:return strict_load(r.read(4_000_001))
    def handle(self,m):
        method=m.get('method');params=m.get('params') or {};rid=m.get('id')
        if rid is None:return None
        try:
            if method=='initialize':
                version=params.get('protocolVersion');version=version if version in SUPPORTED else '2025-06-18'
                self.initialized=True
                result={'protocolVersion':version,'capabilities':{'tools':{}},'serverInfo':{'name':'lelock-character-tools','version':'0.3.0'}}
            elif not self.initialized:raise BridgeError('Initialize first')
            elif method=='ping':result={}
            elif method=='tools/list':
                result={'tools':[{'name':t['name'],'description':t['description'],'inputSchema':t['parameters']} for t in self.api('/v2/runtime/tools')['tools']]}
            elif method=='tools/call':
                res=self.api('/v2/runtime/invoke',{'tool':params['name'],'arguments':params.get('arguments',{}),'request_id':uuid.uuid4().hex})
                body=res.get('result',{});images=body.get('content',[]) if isinstance(body,dict) else []
                sanitized={**res,'result':{k:v for k,v in body.items() if k!='content'}} if isinstance(body,dict) else res
                content=[{'type':'text','text':canonical(sanitized)}]+[c for c in images if c.get('type')=='image']
                result={'content':content,'isError':res.get('status')!='done'}
            else:return {'jsonrpc':'2.0','id':rid,'error':{'code':-32601,'message':'Unknown method'}}
            return {'jsonrpc':'2.0','id':rid,'result':result}
        except Exception:return {'jsonrpc':'2.0','id':rid,'error':{'code':-32000,'message':'Scoped tool refused or failed; no success claimed'}}
def main():
    p=argparse.ArgumentParser();p.add_argument('--pairing',type=Path,required=True);args=p.parse_args();server=MCP(args.pairing)
    for line in sys.stdin.buffer:
        if len(line)>1_000_000:break
        try:m=strict_load(line);result=server.handle(m)
        except Exception:result={'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Invalid request'}}
        if result is not None:print(canonical(result),flush=True)
if __name__=='__main__':main()
