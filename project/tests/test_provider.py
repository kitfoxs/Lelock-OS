"""Lifecycle tests using the actual supplied Hermes MemoryProvider ABC, not the full host."""
import sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'resources/hermes_contract'))
from lelock.hermes_plugin import LelockMemoryProvider,bind_service,unbind_service
from lelock.common import LelockError
from lelock.service import SCHEMAS
from helpers import make_service

class Provider(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=make_service(Path(self.tmp.name),retention='journal')
        self.rh=self.s.home/'runtime/hermes';bind_service(self.rh,self.s)
        self.p=LelockMemoryProvider();self.p.initialize('session',hermes_home=str(self.rh))
    def tearDown(self):
        try: self.p.shutdown()
        except LelockError: pass
        unbind_service(self.rh);self.tmp.cleanup()
    def test_contract_version(self): self.assertEqual(self.p.pre_compress_checkpoint_api_version,2)
    def test_schema_registration(self): self.assertEqual(self.p.get_tool_schemas(),SCHEMAS)
    def test_wrong_home_fails_closed(self):
        with self.assertRaises(LelockError): LelockMemoryProvider().initialize('s',hermes_home=str(self.rh/'other'))
    def test_sync_archives_and_drains(self):
        self.p.sync_turn('hello','hi',session_id='session');self.p.shutdown()
        self.assertFalse(self.s.journal.pending());self.assertEqual(len(self.s.rpc.rows),1)
    def test_compression_failure_propagates(self):
        self.s.rpc.fail=True
        with self.assertRaises(LelockError): self.p.on_pre_compress([{'role':'user','content':'hello'}],require_checkpoint=True)
    def test_non_primary_does_not_write(self):
        self.p.primary=False;self.p.sync_turn('hello','hi');self.assertFalse(self.s.journal.pending())
    def test_recall_outage_is_visible(self):
        from lelock.service import make_record
        self.s.store(make_record('favorite color blue'));self.s.rpc.fail=True
        self.assertIn('unavailable',self.p.prefetch('color'))

if __name__=='__main__': unittest.main()
