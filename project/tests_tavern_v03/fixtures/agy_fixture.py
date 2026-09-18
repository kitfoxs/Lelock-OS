"""Scripted native wire peer that calls the actual generated stdio MCP server, HTTP bridge, and core."""
import json,subprocess,sys,os
from pathlib import Path
config=json.loads(Path('.agents/mcp_config.json').read_text())['mcpServers']['lelock']
child=subprocess.Popen([config['command'],*config['args']],env={**os.environ,**config.get('env',{})},stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
def rpc(i,method,params):
 child.stdin.write(json.dumps({'jsonrpc':'2.0','id':i,'method':method,'params':params})+'\n');child.stdin.flush();return json.loads(child.stdout.readline())
rpc(1,'initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'fixture','version':'1'}})
print(json.dumps({'event':'init','init':{'tools':['lelock'],'permission_mode':'fixture'}}),flush=True)
for line in sys.stdin:
 m=json.loads(line)
 if m.get('event')!='user':continue
 result=rpc(2,'tools/call',{'name':'lelock_write_text','arguments':{'path':'agy-proof.txt','content':'Actual MCP/HTTP/broker effect; no real model.'}})
 print(json.dumps({'event':'result','result':{'status':'SUCCESS','response':'Scripted Antigravity wire completed.','conversation_id':'fixture','usage':{'total_tokens':0}}}),flush=True)
child.stdin.close();child.wait(timeout=3)
