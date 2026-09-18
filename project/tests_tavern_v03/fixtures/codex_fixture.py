"""Deterministic fake model WIRE peer. No inference or external network. Tools execute in the real gateway."""
import json,sys,uuid
threads={};pending={}
def send(m):print(json.dumps(m),flush=True)
for line in sys.stdin:
 m=json.loads(line);method=m.get('method');p=m.get('params',{});rid=m.get('id')
 if method=='initialize':send({'id':rid,'result':{'userAgent':'fixture'}})
 elif method=='initialized':pass
 elif method=='account/read':send({'id':rid,'result':{'account':{'type':'chatgpt','planType':'fixture-not-a-real-account'}}})
 elif method=='account/login/start':send({'id':rid,'result':{'type':'chatgpt','loginId':'fixture','authUrl':'https://example.invalid/fixture-login'}})
 elif method=='account/logout':send({'id':rid,'result':{}})
 elif method=='model/list':send({'id':rid,'result':{'data':[{'id':'fixture','model':'fixture','displayName':'Scripted fixture'}],'nextCursor':None}})
 elif method=='thread/start':
  tid=uuid.uuid4().hex;threads[tid]=p;send({'id':rid,'result':{'thread':{'id':tid}}})
 elif method=='turn/start':
  tid=p['threadId'];turn=uuid.uuid4().hex;send({'id':rid,'result':{'turn':{'id':turn}}})
  call=uuid.uuid4().hex;pending[call]=(tid,turn)
  send({'id':call,'method':'item/tool/call','params':{'threadId':tid,'turnId':turn,'callId':'native_fixture_call','tool':'lelock_write_text','arguments':{'path':'native-proof.txt','content':'Written through the real Lelock broker by a scripted wire fixture.'}}})
 elif method=='turn/interrupt':send({'id':rid,'result':{}})
 elif rid in pending:
  tid,turn=pending.pop(rid);ok=m.get('result',{}).get('success',False)
  send({'method':'item/completed','params':{'threadId':tid,'item':{'type':'agentMessage','id':'m','text':'Fixture completed actual tool call: '+str(ok)}}})
  send({'method':'turn/completed','params':{'threadId':tid,'turn':{'id':turn,'status':'completed'}}})
 elif rid is not None:send({'id':rid,'error':{'code':-32601,'message':'unknown fixture method'}})
