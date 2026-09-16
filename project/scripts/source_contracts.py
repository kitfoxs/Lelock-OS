#!/usr/bin/env python3
"""Static compatibility checks against the bundled snapshots, without importing their application code."""
import ast,json,sys,zipfile
from pathlib import Path
P=Path(__file__).resolve().parents[1];PACKET=P.parent
lock=json.loads((P/'resources/source-lock.json').read_text())

def source(name,relative):
    item=lock['sources'][name]
    with zipfile.ZipFile(PACKET/'upstream'/item['file']) as z:
        return z.read(item['root']+'/'+relative).decode()

def cls_method(code,cls,method):
    node=next(n for n in ast.parse(code).body if isinstance(n,ast.ClassDef) and n.name==cls)
    return next(n for n in node.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==method)

checks={}
a=cls_method(source('hermes','run_agent.py'),'AIAgent','__init__')
args={n.arg for n in a.args.args+a.args.kwonlyargs}
checks['hermes_constructor']=set(['enabled_toolsets','skip_context_files','load_soul_identity','skip_background_review','api_mode','ephemeral_system_prompt','max_iterations','run_budget_seconds'])<=args
b=cls_method(source('hermes','run_agent.py'),'AIAgent','_execute_tool_calls')
checks['hermes_dispatch_seam']=[n.arg for n in b.args.args]==['self','assistant_message','messages','effective_task_id','api_call_count']
mp=source('hermes','agent/memory_provider.py')
checks['checkpoint_api_v2']='PRE_COMPRESS_CHECKPOINT_API_VERSION = 2' in mp and 'def spawn_context_thread' in mp
checks['memory_entrypoint']='hermes_agent.memory_providers' in source('hermes','plugins/memory/__init__.py')
palace=source('mempalace','mempalace/mcp_server.py')
checks['palace_tools']=all('"'+n+'"' in palace for n in ['mempalace_add_drawer','mempalace_get_drawer','mempalace_search','mempalace_list_drawers','mempalace_delete_drawer'])
checks['palace_search_source_path']='"source_path": source' in source('mempalace','mempalace/searcher.py')
checks['palace_registry']='"pid": os.getpid()' in source('mempalace','mempalace/server_registry.py')
checks['managed_port_zero']='bound_port = httpd.server_address[1]' in palace
report={'gate':'source-contract','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
        'scope':'Static source compatibility only; no donor runtime imported or executed.'}
path=PACKET/'receipts/source-contracts.json';path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));raise SystemExit(0 if all(checks.values()) else 1)
