import copy
import json
import os
from pathlib import Path
import tempfile
import stat
import unittest
from unittest import mock
from types import SimpleNamespace

from lelock.common import LelockError,atomic_json,read_json,digest,display,home_lock,private_dir
from lelock.config import Config,initialize,endpoint_url
from lelock.service import Service,make_record,SCHEMAS
from lelock.runtime import dispatch_batch
from lelock.bundle import export,inspect,restore_records
from helpers import make_service,FixturePalace

class Core(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.s=make_service(self.root);self.home=self.s.home;self.w=self.s.workspace.root
    def tearDown(self): self.temp.cleanup()
    def test_config_roundtrip(self): self.assertEqual(Config.load(self.home),self.s.config)
    def test_no_home_overwrite(self):
        with self.assertRaises(LelockError):
            initialize(self.home,self.w,name='Other',person='Alex',relationship='friendship',endpoint='http://127.0.0.1/v1',model='x')
    def test_non_nested_workspace(self):
        with self.assertRaises(LelockError):
            initialize(self.root/'bad',self.root/'bad/work',name='Other',person='Alex',relationship='friendship',endpoint='http://127.0.0.1/v1',model='x')
    def test_remote_http_rejected(self):
        with self.assertRaises(LelockError): endpoint_url('http://example.com/v1')
    def test_embedded_credentials_rejected(self):
        with self.assertRaises(LelockError): endpoint_url('https://secret@api.example/v1')
    def test_endpoint_query_rejected(self):
        with self.assertRaises(LelockError): endpoint_url('https://api.example/v1?key=secret')
    def test_https_allowed(self): self.assertEqual(endpoint_url('https://example.com/v1/'),'https://example.com/v1')
    def test_scope_requires_new_profile(self):
        with self.assertRaises(LelockError): Service(self.home,self.s.rpc,scope='work')
    def test_lock_excludes_second_writer(self):
        with home_lock(self.home):
            with self.assertRaises(LelockError):
                with home_lock(self.home): pass
    def test_terminal_escape_rendered(self): self.assertNotIn('\x1b',display('\x1b]52;c;secret\x07'))
    def test_bidi_rendered(self): self.assertNotIn('\u202e',display('name\u202eexe'))
    def test_text_read(self):
        (self.w/'note.txt').write_text('hello');self.assertEqual(self.s.workspace.read('note.txt')['content'],'hello')
    def test_absolute_path_denied(self):
        with self.assertRaises(LelockError): self.s.workspace.read('/etc/passwd')
    def test_parent_path_denied(self):
        with self.assertRaises(LelockError): self.s.workspace.read('../home/config.json')
    def test_dotfile_denied(self):
        with self.assertRaises(LelockError): self.s.workspace.read('.env')
    def test_backslash_denied(self):
        with self.assertRaises(LelockError): self.s.workspace.read('dir\\file')
    def test_symlink_file_denied(self):
        (self.w/'link').symlink_to(self.home/'config.json')
        with self.assertRaises(LelockError): self.s.workspace.read('link')
    def test_symlink_parent_denied(self):
        (self.w/'linked').symlink_to(self.home,target_is_directory=True)
        with self.assertRaises(LelockError): self.s.workspace.read('linked/config.json')
    def test_symlink_parent_nested_denied(self):
        # Regression D1: the escape must also be refused below a genuine subdirectory.
        (self.w/'real').mkdir();(self.w/'real/linked').symlink_to(self.home,target_is_directory=True)
        with self.assertRaises(LelockError): self.s.workspace.read('real/linked/config.json')
    def test_symlink_parent_create_denied(self):
        # Regression D1: an approved write must not land outside the workspace either.
        (self.w/'linked').symlink_to(self.home,target_is_directory=True)
        with self.assertRaises(LelockError): self.s.workspace.create('linked/escaped.txt','x')
        self.assertFalse((self.home/'escaped.txt').exists())
    def test_symlink_parent_proposal_denied(self):
        # Regression D1: denial happens at proposal time, not only at approval.
        (self.w/'linked').symlink_to(self.home,target_is_directory=True)
        with self.assertRaises(LelockError): self.s.write_proposal('linked/escaped.txt','x')
        self.assertFalse((self.home/'escaped.txt').exists())
    def test_symlink_parent_denied_in_code_not_prompt(self):
        # Regression D1 / A11: the model-facing dispatcher must refuse, not merely advise.
        (self.w/'linked').symlink_to(self.home,target_is_directory=True)
        out=json.loads(self.s.dispatch('lelock_read_text',{'path':'linked/config.json'}))
        self.assertFalse(out['ok'])
        self.assertNotIn('profile_id',json.dumps(out))
    def test_hardlink_denied(self):
        os.link(self.home/'config.json',self.w/'linked.json')
        with self.assertRaises(LelockError): self.s.workspace.read('linked.json')
    def test_fifo_denied_without_blocking(self):
        os.mkfifo(self.w/'pipe')
        with self.assertRaises(LelockError): self.s.workspace.read('pipe')
    def test_large_file_denied(self):
        (self.w/'big').write_bytes(b'x'*128001)
        with self.assertRaises(LelockError): self.s.workspace.read('big')
    def test_binary_denied(self):
        (self.w/'binary').write_bytes(b'\xff')
        with self.assertRaises(LelockError): self.s.workspace.read('binary')
    def test_write_is_proposal_only(self):
        self.s.write_proposal('answer.txt','answer');self.assertFalse((self.w/'answer.txt').exists())
    def test_approved_write_verified(self):
        p=self.s.write_proposal('answer.txt','answer');r=self.s.approve(p['proposal_id'])
        self.assertEqual(r['sha256'],digest(b'answer'));self.assertEqual((self.w/'answer.txt').read_text(),'answer')
    def test_approval_single_use(self):
        p=self.s.write_proposal('answer.txt','answer');self.s.approve(p['proposal_id'])
        with self.assertRaises(LelockError): self.s.approve(p['proposal_id'])
    def test_write_precondition_rechecked(self):
        p=self.s.write_proposal('answer.txt','answer');(self.w/'answer.txt').write_text('external edit')
        with self.assertRaises(LelockError): self.s.approve(p['proposal_id'])
        self.assertEqual((self.w/'answer.txt').read_text(),'external edit')
    def test_expired_approval_denied(self):
        p=self.s.journal.propose('write',{'path':'a','content':'a'},ttl=-1)
        with self.assertRaises(LelockError): self.s.approve(p)
    def test_rejected_proposal_denied(self):
        p=self.s.write_proposal('a.txt','a');self.s.journal.reject(p['proposal_id'])
        with self.assertRaises(LelockError): self.s.approve(p['proposal_id'])
    def test_agent_cannot_approve(self):
        p=self.s.write_proposal('a.txt','a')
        result=json.loads(self.s.dispatch('approve',{'id':p['proposal_id']}))
        self.assertFalse(result['ok']);self.assertFalse((self.w/'a.txt').exists())
    def test_unknown_tool_denied(self): self.assertFalse(json.loads(self.s.dispatch('terminal',{'command':'whoami'}))['ok'])
    def test_extra_tool_argument_denied(self): self.assertFalse(json.loads(self.s.dispatch('lelock_status',{'approve':True}))['ok'])
    def test_wrong_tool_argument_type(self): self.assertFalse(json.loads(self.s.dispatch('lelock_status',[]))['ok'])
    def test_dispatch_boundary_never_calls_shell(self):
        msg=SimpleNamespace(tool_calls=[SimpleNamespace(id='x',function=SimpleNamespace(name='terminal',arguments='{"command":"whoami"}'))])
        out=[];dispatch_batch(self.s,msg,out)
        self.assertFalse(json.loads(out[0]['content'])['ok'])
    def test_bad_json_tool_payload(self):
        msg=SimpleNamespace(tool_calls=[SimpleNamespace(id='x',function=SimpleNamespace(name='lelock_status',arguments='bad'))])
        out=[];dispatch_batch(self.s,msg,out);self.assertFalse(json.loads(out[0]['content'])['ok'])
    def test_no_approval_in_schema(self): self.assertTrue(all('approve' not in s['name'] for s in SCHEMAS))
    def test_memory_proposal_not_saved(self):
        self.s.memory_proposal('Favorite color is violet');self.assertEqual(self.s.rpc.rows,{})
    def test_memory_approved_and_recalled(self):
        p=self.s.memory_proposal('Favorite color is violet');self.s.approve(p['proposal_id'])
        self.assertEqual(self.s.recall('color')['memories'][0]['content'],'Favorite color is violet')
    def test_cold_service_restart(self):
        r=make_record('Favorite color is violet');self.s.store(r)
        fresh=Service(self.home,self.s.rpc);self.assertEqual(fresh.fetch(r['id']),r)
    def test_unknown_has_no_evidence(self): self.assertEqual(self.s.recall('neverknown')['status'],'no_evidence')
    def test_correction_supersedes(self):
        old=make_record('Favorite color is blue');self.s.store(old)
        new=make_record('Favorite color is violet',supersedes=old['id']);self.s.store(new)
        self.assertEqual([r['id'] for r in self.s.recall('color')['memories']],[new['id']])
    def test_correction_missing_target_denied(self):
        with self.assertRaises(LelockError): self.s.store(make_record('color is violet',supersedes='a'*32))
    def test_fiction_not_real(self):
        with self.assertRaises(LelockError): make_record('We visited Mars',kind='fiction',scope='personal')
    def test_separate_profile_scope(self):
        other=make_service(self.root/'other',scope='fiction',rpc=self.s.rpc)
        other.store(make_record('We visited Mars',kind='fiction',scope='fiction'))
        self.assertEqual(self.s.recall('Mars')['memories'],[])
    def test_palace_failure_not_saved(self):
        self.s.rpc.fail=True;r=make_record('memory')
        with self.assertRaises(LelockError): self.s.store(r)
        self.assertIsNone(self.s.journal.ref(r['id']))
    def test_palace_readback_failure_not_acknowledged(self):
        self.s.rpc.corrupt=True;r=make_record('memory')
        with self.assertRaises(LelockError): self.s.store(r)
        self.assertIsNone(self.s.journal.ref(r['id']))
    def test_memory_idempotent(self):
        r=make_record('memory');self.s.store(r);self.s.store(r);self.assertEqual(len(self.s.rpc.rows),1)
    def test_memory_id_collision_denied(self):
        r=make_record('memory');self.s.store(r);changed={**r,'content':'different'}
        with self.assertRaises(LelockError): self.s.store(changed)
    def test_outbox_survives_failure(self):
        r=make_record('queued');self.s.journal.enqueue(r['id'],r);self.s.rpc.fail=True
        with self.assertRaises(LelockError): self.s.flush()
        self.assertEqual(len(self.s.journal.pending()),1)
        self.s.rpc.fail=False;self.s.flush();self.assertEqual(self.s.journal.pending(),[])
    def test_no_compression_without_consent(self):
        with self.assertRaises(LelockError): self.s.checkpoint([{'role':'user','content':'private'}],'session')
        self.assertEqual(self.s.rpc.rows,{})
    def test_export_excludes_credentials_runtime(self):
        (self.home/'.env').write_text('KEY=DO_NOT_EXPORT');(self.home/'runtime'/'private.txt').write_text('DO_NOT_EXPORT')
        self.s.store(make_record('memory'));p=self.root/'export.json';export(self.s,p)
        self.assertNotIn('DO_NOT_EXPORT',p.read_text());self.assertNotIn('endpoint',inspect(p))
    def test_export_tamper_detected(self):
        p=self.root/'export.json';export(self.s,p);d=read_json(p);d['payload']['person_name']='intruder';atomic_json(p,d)
        with self.assertRaises(LelockError): inspect(p)
    def test_restore_selected_data_new_profile(self):
        self.s.store(make_record('Favorite color is violet'));p=self.root/'export.json';export(self.s,p)
        other=make_service(self.root/'restored');restore_records(other,inspect(p))
        self.assertEqual(other.recall('color')['memories'][0]['content'],'Favorite color is violet')
    def test_restore_never_merges_existing(self):
        self.s.store(make_record('memory'));p=self.root/'export.json';export(self.s,p)
        with self.assertRaises(LelockError): restore_records(self.s,inspect(p))
    def test_delete_requires_operator(self):
        r=make_record('Favorite color');self.s.store(r)
        p=self.s.journal.propose('forget',{'id':r['id']});self.s.approve(p)
        self.assertEqual(self.s.recall('color')['memories'],[])

class Journaling(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=make_service(Path(self.tmp.name),retention='journal')
    def tearDown(self): self.tmp.cleanup()
    def test_checkpoint_idempotent(self):
        m=[{'role':'user','content':'hello'},{'role':'assistant','content':'hi'}]
        one=self.s.checkpoint(m,'s');two=self.s.checkpoint(m,'s')
        self.assertEqual(one,two);self.assertEqual(len(self.s.rpc.rows),1)
    def test_checkpoint_filters_tool_and_summaries(self):
        m=[{'role':'user','content':'hello'},{'role':'tool','content':'TOOL_SECRET'},
           {'role':'assistant','content':'DERIVED_SECRET','_compressed_summary':True}]
        self.s.checkpoint(m,'s');alltext=str(self.s.rpc.rows)
        self.assertNotIn('TOOL_SECRET',alltext);self.assertNotIn('DERIVED_SECRET',alltext)
    def test_checkpoint_failure_raises_and_retains(self):
        m=[{'role':'user','content':'hello'}];self.s.rpc.fail=True
        with self.assertRaises(LelockError): self.s.checkpoint(m,'s')
        self.assertTrue(self.s.journal.pending());self.assertEqual(m[0]['content'],'hello')
    def test_transcripts_not_returned_as_facts(self):
        self.s.checkpoint([{'role':'user','content':'moon'}],'s');self.assertEqual(self.s.recall('moon')['memories'],[])

class PrivateDirectory(unittest.TestCase):
    """Regression D2: private_dir must prove the leaf is a real directory, not a link to one."""
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.outside=self.root/'outside';self.outside.mkdir(mode=0o755)
    def tearDown(self): self.tmp.cleanup()
    def test_plain_directory_created_private(self):
        target=self.root/'home';private_dir(target)
        self.assertTrue(target.is_dir());self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o700)
    def test_idempotent_on_existing_directory(self):
        target=self.root/'home';private_dir(target);private_dir(target)
        self.assertTrue(target.is_dir());self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o700)
    def test_symlinked_leaf_refused(self):
        link=self.root/'home';link.symlink_to(self.outside,target_is_directory=True)
        with self.assertRaises(LelockError): private_dir(link)
    def test_symlinked_leaf_refused_when_precheck_is_evaded(self):
        # mkdir(exist_ok=True) silently accepts an existing symlink-to-directory because its
        # fallback is_dir() resolves the link, and chmod by path follows it too. Evading the
        # pre-check deterministically stands in for losing the check/use race, and proves the
        # guarantee now comes from the descriptor comparison rather than the pre-check alone.
        link=self.root/'home';link.symlink_to(self.outside,target_is_directory=True)
        with mock.patch.object(Path,'is_symlink',lambda self: False):
            with self.assertRaises(LelockError): private_dir(link)
        self.assertEqual(stat.S_IMODE(self.outside.stat().st_mode),0o755)
    def test_symlinked_ancestor_still_allowed(self):
        # Deliberate scope boundary: macOS /tmp and /var are symlinks, so an application home
        # reached through a linked ancestor must keep working. Only the leaf is constrained.
        (self.root/'via').symlink_to(self.outside,target_is_directory=True)
        private_dir(self.root/'via'/'home')
        self.assertTrue((self.outside/'home').is_dir())

if __name__=='__main__': unittest.main()
