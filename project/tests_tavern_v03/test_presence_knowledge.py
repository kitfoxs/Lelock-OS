import json,tempfile,time,unittest
from pathlib import Path
from lelock_tavern.manager import Manager,DEFAULT_CAPS
from lelock_tavern.presence import Presence
from lelock_tavern.common import BridgeError
from lelock_tavern.knowledge import Knowledge
from lelock_entity.jobs import QuietHours

class Model:
 def run(self,**k):
  r=k['call_tool']('lelock_write_text',{'path':'scheduled.txt','content':'same actor'},'native-repeatable-id')
  return {'text':'Scheduled result: '+r['status'],'provider':'scripted','actor_mode':'direct'}
 def close(self):pass

class PresenceKnowledge(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.m=Manager(self.root,runtimes={'codex':Model()})
  self.e=self.m.bind('c','a',{'name':'Ada'},{'provider':'codex','mode':'yolo','capabilities':sorted(DEFAULT_CAPS|{'skills.read'})})['entity']
 def tearDown(self):self.m.close();self.temp.cleanup()
 def pack(self):
  p=self.m.knowledge.packs/'research';p.mkdir()
  (p/'skill.json').write_text(json.dumps({'schema':'lelock.skill/1','name':'research','description':'Use source evidence','files':['SKILL.md'],'capabilities_requested':['workspace.write']}))
  (p/'SKILL.md').write_text('Read sources. Mark uncertainty.')
  return p
 def test_skill_needs_review(self):
  self.pack()
  with self.assertRaises(Exception):self.m.knowledge.load('research')
 def test_skill_pin_survives_restart(self):
  self.pack();r=self.m.knowledge.inspect('research');self.m.knowledge.approve('research',r['sha256'])
  again=Knowledge(self.root/'knowledge');self.assertEqual(again.load('research').sha256,r['sha256'])
 def test_skill_modification_invalidates_pin(self):
  p=self.pack();r=self.m.knowledge.inspect('research');self.m.knowledge.approve('research',r['sha256']);(p/'SKILL.md').write_text('changed')
  with self.assertRaises(Exception):self.m.knowledge.load('research')
 def test_skill_is_advertised_and_callable(self):
  self.pack();r=self.m.knowledge.inspect('research');self.m.knowledge.approve('research',r['sha256'])
  result=self.m.invoke(self.e,'lelock_skill_read',{'name':'research'},'one');self.assertEqual(result['result']['permissions_granted'],[])
 def presence(self,enabled=True):
  self.m.presence=Presence(self.m,enabled=enabled,quiet=QuietHours(start='00:00',end='00:00'));return self.m.presence
 def test_pulse_requires_explicit_gateway_enable(self):
  p=self.presence(False)
  with self.assertRaises(BridgeError):p.add(self.e,{'prompt':'test'})
 def test_pulse_requires_bounded_frequency(self):
  p=self.presence()
  with self.assertRaises(BridgeError):p.add(self.e,{'prompt':'test','interval':1})
 def test_pulse_is_same_runtime_actual_file_and_local_delivery(self):
  p=self.presence();r=p.add(self.e,{'prompt':'test','interval':600,'ttl':7200})
  now=(int(time.time()//600)+1)*600+1;p.pulse.tick(now=now)
  result=p.worker.run_once(now=now)
  self.assertEqual(result['status'],'done');self.assertTrue((self.m.slot(self.e).workspace/'scheduled.txt').exists())
  inbox=p.inbox(self.e);self.assertEqual(len(inbox),1);self.assertIn('done',inbox[0]['body'])
  turn=self.m.public_turn(result['job_id'],self.e);self.assertEqual(turn['result']['actor'],self.e)
 def test_pulse_new_permission_session_refuses_old_authority(self):
  p=self.presence();p.add(self.e,{'prompt':'test','interval':600,'ttl':7200})
  c=self.m.db.entity(self.e)['config'];self.m.configure(self.e,c)
  now=(int(time.time()//600)+1)*600+1;p.pulse.tick(now=now)
  with self.assertRaises(BridgeError):p.worker.run_once(now=now)
  self.assertFalse((self.m.slot(self.e).workspace/'scheduled.txt').exists())
 def test_disabled_schedule_does_not_fire(self):
  p=self.presence();r=p.add(self.e,{'prompt':'test','interval':600,'ttl':7200});p.disable(self.e,r['schedule'])
  self.assertEqual(p.pulse.tick(now=(int(time.time()//600)+1)*600+1),[])
 def test_schedule_is_not_another_characters(self):
  p=self.presence();r=p.add(self.e,{'prompt':'test'});other=self.m.bind('c','b',{'name':'Rowan'})['entity']
  with self.assertRaises(BridgeError):p.disable(other,r['schedule'])
 def test_quiet_hours_block_native_calls(self):
  from datetime import datetime,timezone
  p=self.presence();p.worker.quiet=QuietHours('UTC','00:00','23:59')
  stamp=datetime(2026,9,17,12,0,tzinfo=timezone.utc).timestamp()
  self.assertEqual(p.worker.run_once(now=stamp)['status'],'quiet')
