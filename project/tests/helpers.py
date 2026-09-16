from pathlib import Path
import json
import uuid
from lelock.common import LelockError,digest
from lelock.config import initialize
from lelock.service import Service

class FixturePalace:
    """Deterministic transport fixture. NOT MemPalace, NOT semantic retrieval, NOT an LLM."""
    def __init__(self): self.rows={};self.fail=False;self.corrupt=False
    def call(self,name,args):
        if self.fail: raise LelockError('fixture outage')
        if name=='mempalace_add_drawer':
            ident='drawer_'+digest(args['content']);self.rows[ident]=dict(args)
            return {'success':True,'drawer_id':ident}
        if name=='mempalace_get_drawer':
            if args['drawer_id'] not in self.rows: raise LelockError('not found')
            body=self.rows[args['drawer_id']]['content']
            return {'id':args['drawer_id'],'content':'{}' if self.corrupt else body}
        if name=='mempalace_search':
            hits=[]
            for ident,row in self.rows.items():
                if row['wing']==args['wing'] and row['room']==args['room'] and args['query'].lower() in row['content'].lower():
                    hits.append({'drawer_id':ident,'text':row['content'][:200],
                                 'source_path':row['source_file'],'room':row['room'],'wing':row['wing']})
            return {'results':hits}
        if name=='mempalace_delete_drawer':
            self.rows.pop(args['drawer_id']);return {'success':True}
        raise LelockError('fixture unsupported call')

def make_service(root: Path,*,scope='personal',retention='explicit',rpc=None):
    home=root/'home';workspace=root/'workspace'
    initialize(home,workspace,name='Samantha',person='Alex',relationship='friendship',scope=scope,
               endpoint='http://127.0.0.1:1234/v1',model='fixture-model',retention=retention)
    return Service(home,rpc or FixturePalace())
