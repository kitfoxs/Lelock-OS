from __future__ import annotations
import argparse
import contextlib
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import uuid
from .common import LelockError, atomic_bytes, atomic_json, canonical, display, home_lock, read_json
from .config import Config, DEFAULT_HOME, initialize, RELATIONSHIPS
from .service import Service, make_record
from .palace import ManagedPalace


def emit(value):
    print(display(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)))

def confirm(prompt):
    if not sys.stdin.isatty(): raise LelockError('Human approval requires an interactive terminal, or an explicitly documented operator CLI flag.')
    return input(prompt+' Type YES: ').strip()=='YES'

@contextlib.contextmanager
def live(home):
    with home_lock(home):
        with ManagedPalace(home) as rpc:
            yield Service(home,rpc)

class DisabledPalace:
    def call(self,name,args):
        if name=='mempalace_search': return {'results':[]}
        raise LelockError('Temporary mode has no Palace persistence.')

class TemporaryService(Service):
    def dispatch(self,name,args):
        if name not in {'lelock_read_text','lelock_status','lelock_recall'}:
            return canonical({'ok':False,'error':'temporary_mode_read_only'})
        return super().dispatch(name,args)


def chat(service,*,temporary=False):
    from .runtime import HermesRuntime
    cfg=service.config
    emit(f'Lelock OS | {cfg.companion_name} | model: {cfg.model}\nEndpoint: {cfg.endpoint}\n'
         f'Scope: {cfg.scope} | retention: {cfg.retention} | /help for commands')
    emit('Temporary mode: no prior memories, no approvals, no durable Palace. Normal cleanup removes app-owned temporary files; provider/OS retention is separate.' if temporary else
         'Session history is stored locally. Explicit retention archives only approved memories; journal retention also archives turns/checkpoints. No background activity after exit.')
    runtime=HermesRuntime(service,temporary=temporary)
    try:
        while True:
            try: line=input('\nYou > ').strip()
            except (EOFError,KeyboardInterrupt): print();break
            if not line: continue
            if line in {'/quit','/exit'}: break
            try:
                if line=='/help':
                    emit('/pending; /approve ID; /reject ID; /remember TEXT; /recall QUERY; /forget ID; /status; /quit\n'
                         'No !shell escape. Use lelock new-session outside chat for a fresh conversation.')
                elif line=='/pending': emit(service.journal.proposals())
                elif line=='/status': emit(json.loads(service.dispatch('lelock_status',{})))
                elif line.startswith('/approve '):
                    if temporary: raise LelockError('Temporary mode cannot approve writes.')
                    ident=line.split(maxsplit=1)[1]
                    matches=[p for p in service.journal.proposals() if p['id']==ident]
                    if not matches: raise LelockError('No such pending proposal.')
                    emit(matches[0])
                    if confirm('Approve exactly this proposal?'): emit(service.approve(ident))
                elif line.startswith('/reject '):
                    service.journal.reject(line.split(maxsplit=1)[1]);emit('Rejected.')
                elif line.startswith('/remember '):
                    if temporary: raise LelockError('Temporary mode cannot save memory.')
                    r=make_record(line.split(maxsplit=1)[1],scope=service.scope,source='person-command')
                    emit({'saved_record_id':r['id'],'drawer_id':service.store(r)})
                elif line.startswith('/recall '): emit(service.recall(line.split(maxsplit=1)[1]))
                elif line.startswith('/forget '):
                    if temporary: raise LelockError('Temporary mode cannot delete memory.')
                    ident=line.split(maxsplit=1)[1]
                    emit(service.fetch(ident))
                    if confirm('Delete this active Palace record? Logs and offline backups may retain copies.'):
                        proposal=service.journal.propose('forget',{'id':ident});emit(service.approve(proposal))
                elif line.startswith('/'):
                    raise LelockError('Unknown local command. Commands never become shell input.')
                else:
                    emit(cfg.companion_name+' > '+runtime.turn(line))
            except (LelockError,OSError,ValueError) as exc:
                emit('Not completed: '+str(exc))
    finally:
        runtime.close()
        if service.journal.pending(): emit('Memory outbox remains pending; it has NOT been acknowledged as saved.')


def parser():
    hp=argparse.ArgumentParser(add_help=False)
    hp.add_argument('--home',type=Path,default=argparse.SUPPRESS,help='Home directory (default: ~/.lelock)')
    p=argparse.ArgumentParser(prog='lelock',description='A terminal companion with user-owned memory and bounded tools.')
    p.add_argument('--home',type=Path,default=DEFAULT_HOME)
    sub=p.add_subparsers(dest='command',required=True)
    init=sub.add_parser('init',parents=[hp])
    init.add_argument('--workspace',type=Path,required=True)
    init.add_argument('--name',default='Samantha');init.add_argument('--person',default='Friend')
    init.add_argument('--relationship',choices=sorted(RELATIONSHIPS),default='friendship')
    init.add_argument('--scope',choices=['personal','work','fiction'],default='personal')
    init.add_argument('--endpoint',required=True);init.add_argument('--model',required=True)
    init.add_argument('--retention',choices=['explicit','journal'],default='explicit')
    init.add_argument('--companion',help='Preload an included companion card (e.g. "Cinder Ashgrave", "Amara Sunscale")')
    init.add_argument('--no-lore',action='store_true',help='Skip seeding companion lorebook entries into MemPalace')
    chatp=sub.add_parser('chat',parents=[hp]);chatp.add_argument('--temporary',action='store_true')
    sub.add_parser('doctor',parents=[hp]);sub.add_parser('new-session',parents=[hp])
    comps=sub.add_parser('companions',parents=[hp],help='List preloaded companion cards and lorebooks')
    comps.add_argument('--collection',choices=['fursona','romance','anime'],help='Filter by collection')
    comps.add_argument('--details',action='store_true',help='Show detailed persona and lore topics')
    cact=sub.add_parser('companion-activate',parents=[hp],help='Activate a preloaded companion on this home')
    cact.add_argument('companion',help='Companion name or ID')
    cact.add_argument('--approve',action='store_true',help='Confirm activation')
    cact.add_argument('--seed-lore',action='store_true',help='Seed lorebook entries into MemPalace')
    mem=sub.add_parser('remember',parents=[hp]);mem.add_argument('content');mem.add_argument('--kind',default='fact',choices=['fact','preference','project','episode','fiction'])
    rec=sub.add_parser('recall',parents=[hp]);rec.add_argument('query')
    sub.add_parser('memory-list',parents=[hp]);sub.add_parser('memory-flush',parents=[hp])
    exp=sub.add_parser('export',parents=[hp]);exp.add_argument('destination',type=Path)
    ins=sub.add_parser('inspect-datachip',parents=[hp]);ins.add_argument('file',type=Path)
    res=sub.add_parser('restore',parents=[hp]);res.add_argument('file',type=Path);res.add_argument('--workspace',type=Path,required=True)
    res.add_argument('--endpoint',required=True);res.add_argument('--model',required=True);res.add_argument('--approve',action='store_true')
    card=sub.add_parser('card-review',parents=[hp]);card.add_argument('file',type=Path)
    act=sub.add_parser('card-activate',parents=[hp]);act.add_argument('id');act.add_argument('--approve',action='store_true')
    srv=sub.add_parser('serve',parents=[hp],help='Start local HTTP bridge daemon for SillyTavern and extensions')
    srv.add_argument('--port',type=int,default=8780,help='Port to bind (default: 8780)')
    srv.add_argument('--host',default='127.0.0.1',help='Host to bind (default: 127.0.0.1)')
    return p


def main(argv=None):
    a=parser().parse_args(argv);home=a.home.expanduser().absolute()
    try:
        if a.command=='init':
            name=a.name
            comp_meta=None
            if a.companion:
                from .companions import find_companion
                comp_meta=find_companion(a.companion)
                name=comp_meta['name']
            c=initialize(home,a.workspace.expanduser().absolute(),name=name,person=a.person,relationship=a.relationship,
                         endpoint=a.endpoint,model=a.model,retention=a.retention,scope=a.scope)
            init_res={'initialized':str(home),'scope':c.scope,'retention':c.retention,
                      'next':'Set the configured API key environment variable for a remote endpoint, then run lelock chat.'}
            if comp_meta:
                from .companions import activate_companion, seed_companion_lore
                with home_lock(home):
                    act=activate_companion(home,a.companion)
                init_res['companion']=act['name']
                init_res['collection']=act['collection']
                init_res['summary']=act['short_description']
                if not a.no_lore:
                    try:
                        with live(home) as service:
                            lore_res=seed_companion_lore(service,comp_meta)
                            init_res['lore_seeded']=lore_res['seeded_entries']
                            init_res['lore_topics']=lore_res['topics']
                    except Exception as exc:
                        init_res['lore_warning']=f"Palace was unavailable to seed lore during init: {exc}"
            emit(init_res)
        elif a.command=='companions':
            from .companions import list_companions
            comps=list_companions(a.collection)
            if a.details:
                emit({'count':len(comps),'companions':comps})
            else:
                summary=[{'id':c['id'],'name':c['name'],'collection':c['collection'],
                          'personality':c['personality'][:80]+('...' if len(c['personality'])>80 else ''),
                          'lore_entries':c['lore_entries_count']} for c in comps]
                emit({'count':len(summary),'companions':summary})
        elif a.command=='companion-activate':
            from .companions import find_companion, activate_companion, seed_companion_lore
            comp=find_companion(a.companion)
            if not a.approve:
                emit({'companion':comp['name'],'collection':comp['collection'],
                      'personality':comp['personality'],'lore_entries':comp['lore_entries_count'],
                      'notice':'Pass --approve to activate this companion into SOUL.md'})
            else:
                with home_lock(home):
                    act=activate_companion(home,a.companion)
                if a.seed_lore:
                    try:
                        with live(home) as service:
                            lore_res=seed_companion_lore(service,comp)
                            act['lore_seeded']=lore_res['seeded_entries']
                            act['lore_topics']=lore_res['topics']
                    except Exception as exc:
                        act['lore_warning']=f"Palace was unavailable to seed lore: {exc}"
                emit(act)
        elif a.command=='doctor':
            c=Config.load(home)
            emit({'home':str(home),'config':'valid','hermes_installed':bool(importlib.util.find_spec('run_agent')),
                  'palace_interpreter_configured':bool(os.environ.get('LELOCK_PALACE_PYTHON')) and Path(os.environ['LELOCK_PALACE_PYTHON']).is_file(),
                  'palace_environment':'separate interpreter; live probe required',
                  'model':c.model,'endpoint':c.endpoint,'scope':c.scope,'live_checks':'NOT_RUN'})
        elif a.command=='inspect-datachip':
            from .bundle import inspect
            emit(inspect(a.file))
        elif a.command=='restore':
            from .bundle import inspect,restore_records
            payload=inspect(a.file)
            if not a.approve: raise LelockError('Inspect the datachip first, then use --approve with a new home.')
            initialize(home,a.workspace.expanduser().absolute(),name=payload['companion_name'],person=payload['person_name'],
                       relationship=payload['relationship'],endpoint=a.endpoint,model=a.model,scope=payload['scope'])
            atomic_bytes(home/'SOUL.md',payload['identity'].encode())
            with live(home) as service: emit(restore_records(service,payload))
        elif a.command=='card-review':
            from .cards import stage
            with home_lock(home): Config.load(home);emit(stage(home,a.file))
        elif a.command=='card-activate':
            from .cards import activate
            if not a.approve: raise LelockError('Read the card-review report first; --approve explicitly activates that staged identity.')
            with home_lock(home): emit(activate(home,a.id))
        elif a.command=='new-session':
            with home_lock(home):
                Config.load(home);path=home/'runtime/hermes/session.json'
                if path.exists(): path.rename(path.with_name('session-closed-'+uuid.uuid4().hex+'.json'))
                emit('Next chat starts a new session. Approved memories and closed local session files remain.')
        elif a.command=='serve':
            from .server import LelockBridgeServer
            with live(home) as service:
                cfg=service.config
                emit(f"Lelock OS Bridge Daemon running on http://{a.host}:{a.port}\n"
                     f"Companion: {cfg.companion_name} | Scope: {cfg.scope} | Workspace: {cfg.workspace}\n"
                     f"Connected to MemPalace wing: {service.wing}\n"
                     f"Press Ctrl+C to stop.")
                server=LelockBridgeServer(service,host=a.host,port=a.port)
                try:
                    server.start(blocking=True)
                except KeyboardInterrupt:
                    emit("\nBridge daemon stopped.")
        elif a.command=='chat' and a.temporary:
            old=Config.load(home)
            with tempfile.TemporaryDirectory(prefix='lelock-temporary-') as folder:
                temp=Path(folder)/'home'
                initialize(temp,Path(old.workspace),name=old.companion_name,person=old.person_name,relationship=old.relationship,
                           endpoint=old.endpoint,model=old.model,retention='explicit',scope=old.scope)
                replace(Config.load(temp),api_key_env=old.api_key_env).save(temp)
                atomic_bytes(temp/'SOUL.md',(home/'SOUL.md').read_bytes())
                with home_lock(temp): chat(TemporaryService(temp,DisabledPalace()),temporary=True)
        else:
            with live(home) as service:
                if a.command=='chat': chat(service)
                elif a.command=='remember':
                    r=make_record(a.content,kind=a.kind,scope=service.scope,source='person-command')
                    emit({'record_id':r['id'],'drawer_id':service.store(r)})
                elif a.command=='recall': emit(service.recall(a.query))
                elif a.command=='memory-list': emit(service.journal.refs(service.scope))
                elif a.command=='memory-flush': emit(service.flush())
                elif a.command=='export':
                    from .bundle import export
                    emit(export(service,a.destination))
        return 0
    except (LelockError,OSError,ValueError) as exc:
        emit('Lelock: '+str(exc));return 2

if __name__=='__main__': raise SystemExit(main())
