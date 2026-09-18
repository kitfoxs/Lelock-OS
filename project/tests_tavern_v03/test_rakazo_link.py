import os,tempfile,unittest
from pathlib import Path
from lelock_tavern.manager import Manager,DEFAULT_CAPS,COMPUTER_CAPS
from lelock_tavern.rakazo import RakazoComputer
FIXTURES=Path(os.environ.get('LELOCK_V03_FIXTURES',str(Path(__file__).parent/'fixtures')))
class RakazoLink(unittest.TestCase):
 def test_real_python_node_link_keeps_primary_actor(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);computer=RakazoComputer(['node',str(FIXTURES/'rakazo_fixture.mjs'),str(root/'computers')])
   m=Manager(root/'gateway',computer=computer)
   try:
    a=m.bind('client','a',{'name':'Ada'},{'mode':'yolo','computer':True,'capabilities':sorted(DEFAULT_CAPS|COMPUTER_CAPS)})['entity']
    b=m.bind('client','b',{'name':'Rowan'},{'mode':'yolo','computer':True,'capabilities':sorted(DEFAULT_CAPS|COMPUTER_CAPS)})['entity']
    r=m.invoke(a,'lelock_computer_write',{'path':'proof.txt','content':'Written by primary Ada'},'one')
    self.assertEqual(r['result']['actor'],a);self.assertTrue(r['result']['verified']);self.assertFalse(r['result']['delegated'])
    self.assertEqual((root/'computers'/a/'proof.txt').read_text(),'Written by primary Ada')
    self.assertFalse((root/'computers'/b/'proof.txt').exists())
   finally:m.close();computer.close()
 def test_main_and_named_helper_each_operate_their_own_computer(self):
  class NativeWire:
   def run(self,**k):
    if 'named Ada.' in k['system']:
     result=k['call_tool']('lelock_ask_character',{'helper':'Rowan','task':'Write your proof'},'delegation')
     own=k['call_tool']('lelock_computer_write',{'path':'ada.txt','content':'Ada direct'},'own')
     return {'text':'Main and named helper completed','helper':result,'direct':own}
    return {'text':'Rowan completed','computer':k['call_tool']('lelock_computer_write',{'path':'rowan.txt','content':'Rowan direct'},'own')}
   def close(self):pass
  import time
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);computer=RakazoComputer(['node',str(FIXTURES/'rakazo_fixture.mjs'),str(root/'computers')]);model=NativeWire()
   m=Manager(root/'gateway',computer=computer,runtimes={'codex':model})
   try:
    cfg={'mode':'yolo','provider':'codex','computer':True,'capabilities':sorted(DEFAULT_CAPS|COMPUTER_CAPS|{'delegate.run'})}
    a=m.bind('c','a',{'name':'Ada'},cfg)['entity'];b=m.bind('c','b',{'name':'Rowan'},cfg)['entity']
    m.configure(a,m.db.entity(a)['config']|{'helpers':{'Rowan':b}});m.start_turn(a,'chat','run1','Work together',[])
    for _ in range(150):
     r=m.public_turn('run1',a)
     if r['state'] not in {'queued','running','waiting_approval'}:break
     time.sleep(.02)
    self.assertEqual(r['state'],'completed',r)
    self.assertEqual((root/'computers'/a/'ada.txt').read_text(),'Ada direct')
    self.assertEqual((root/'computers'/b/'rowan.txt').read_text(),'Rowan direct')
    self.assertFalse((root/'computers'/a/'rowan.txt').exists())
    self.assertEqual(r['result']['direct']['result']['actor'],a)
   finally:m.close();computer.close()
