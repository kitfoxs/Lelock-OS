import contextlib,json,os,sys,tempfile,threading,time,unittest
from pathlib import Path
from lelock_tavern.codex import Codex
from lelock_tavern.antigravity import Antigravity
from lelock_tavern.manager import Manager
from lelock_tavern.http_server import Server
from lelock_tavern.mcp_stdio import MCP
from lelock_tavern.common import atomic_json,BridgeError
FIXTURES=Path(os.environ.get('LELOCK_V03_FIXTURES',str(Path(__file__).parent/'fixtures')))

class NativeCase(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_codex_login_is_native_rpc(self):
  p=Codex(self.root,[sys.executable,str(FIXTURES/'codex_fixture.py')])
  try:self.assertIn('authUrl',p.login());self.assertTrue(p.account()['signed_in']);self.assertEqual(p.models()[0]['id'],'fixture')
  finally:p.close()
 def test_codex_main_dynamic_tool_real_effect(self):
  p=Codex(self.root/'provider',[sys.executable,str(FIXTURES/'codex_fixture.py')]);m=Manager(self.root/'gateway',runtimes={'codex':p})
  try:
   e=m.bind('c','a',{'name':'Ada'},{'mode':'yolo','provider':'codex'})['entity'];m.start_turn(e,'chat','turn','write proof',[])
   for _ in range(150):
    r=m.public_turn('turn',e)
    if r['state'] not in {'queued','running','waiting_approval'}:break
    time.sleep(.02)
   self.assertEqual(r['state'],'completed',r);self.assertTrue((m.slot(e).workspace/'native-proof.txt').is_file());self.assertEqual(r['result']['actor'],e)
  finally:m.close()
 def test_codex_safe_waits_for_real_operator_approval(self):
  p=Codex(self.root/'provider',[sys.executable,str(FIXTURES/'codex_fixture.py')]);m=Manager(self.root/'gateway',runtimes={'codex':p})
  try:
   e=m.bind('c','a',{'name':'Ada'},{'mode':'safe','provider':'codex'})['entity'];m.start_turn(e,'chat','turn','write proof',[])
   for _ in range(100):
    actions=m.actions(e)
    if actions:break
    time.sleep(.02)
   self.assertTrue(actions);self.assertFalse((m.slot(e).workspace/'native-proof.txt').exists())
   m.approve(e,actions[0]['id'],actions[0]['digest'])
   for _ in range(100):
    r=m.public_turn('turn',e)
    if r['state']=='completed':break
    time.sleep(.02)
   self.assertEqual(r['state'],'completed',r)
  finally:m.close()
 def test_agy_native_wire_calls_real_mcp_http_and_core(self):
  p=Antigravity([sys.executable,str(FIXTURES/'agy_fixture.py')]);m=Manager(self.root,runtimes={'antigravity':p});server=Server(m).start()
  try:
   e=m.bind('c','a',{'name':'Ada'},{'mode':'yolo','provider':'antigravity','native_risk_ack':True})['entity']
   m.start_turn(e,'chat','turn','write proof',[])
   for _ in range(150):
    r=m.public_turn('turn',e)
    if r['state'] not in {'queued','running','waiting_approval'}:break
    time.sleep(.03)
   self.assertEqual(r['state'],'completed',r);self.assertTrue((m.slot(e).workspace/'agy-proof.txt').exists())
   self.assertEqual(m.runtime_credentials,{})
  finally:m.close();server.close()
 def test_mcp_initialize_required(self):
  p=self.root/'pair.json';atomic_json(p,{'base':'http://127.0.0.1:8781','token':'fixture'})
  m=MCP(p);self.assertIn('error',m.handle({'id':1,'method':'tools/list'}))
 def test_mcp_unknown_method_not_success(self):
  p=self.root/'pair.json';atomic_json(p,{'base':'http://127.0.0.1:8781','token':'fixture'})
  m=MCP(p);m.handle({'id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18'}})
  self.assertIn('error',m.handle({'id':2,'method':'operator/approve'}))
 def test_mcp_public_pairing_file_refused(self):
  p=self.root/'pair.json';atomic_json(p,{'base':'http://127.0.0.1:8781','token':'fixture'});p.chmod(0o644)
  with self.assertRaises(BridgeError):MCP(p)
 def test_mcp_remote_pairing_refused(self):
  p=self.root/'pair.json';atomic_json(p,{'base':'https://example.com','token':'fixture'})
  with self.assertRaises(BridgeError):MCP(p)
