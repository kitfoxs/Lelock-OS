from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
from lelock_entity.common import EntityError, canonical, digest
from lelock_entity.store import Store
from lelock_entity.workspace import Workspace
from lelock_entity.world import World
from lelock_entity.identity import Identity
from lelock_entity.lifecycle import ProfileLease
from lelock_entity.skills import SkillLibrary
from lelock_entity.memory import derive, revalidate, canon_proposal
from lelock_entity.jobs import Cron, JobQueue, Pulse, PulseWorker, QuietHours
from lelock_entity.execution import ProcessRunner
from lelock_entity.channels import LocalInbox

class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.work=self.root/'work'; self.work.mkdir(); self.store=Store(self.root/'state')
    def tearDown(self): self.tmp.cleanup()

class WorkspaceCase(Fixture):
    def setUp(self): super().setUp(); self.fs=Workspace(self.work)
    def tearDown(self): self.fs.close(); super().tearDown()
    def test_roundtrip_unicode(self):
        result=self.fs.write('book.md','A blue unicorn 🦄\n')
        self.assertEqual(self.fs.read('book.md')['content'],'A blue unicorn 🦄\n')
        self.assertTrue(result['verified'])
    def test_create_does_not_overwrite(self):
        self.fs.write('a','first')
        with self.assertRaises(EntityError): self.fs.write('a','second')
    def test_replace_requires_exact_hash(self):
        prior=self.fs.write('a','first')
        with self.assertRaises(EntityError): self.fs.write('a','second','wrong')
        self.fs.write('a','second',prior['sha256']); self.assertEqual(self.fs.read('a')['content'],'second')
    def test_delete_exact_hash(self):
        prior=self.fs.write('a','first')
        with self.assertRaises(EntityError): self.fs.delete('a','wrong')
        self.fs.delete('a',prior['sha256']); self.assertFalse((self.work/'a').exists())
    def test_paths_are_not_permissions(self):
        for path in ['/tmp/no','../outside','a/../x','a//x','./x','a\\x','.lelock-private']:
            with self.subTest(path=path), self.assertRaises(EntityError): self.fs.write(path,'x')
    def test_symlink_file_refused(self):
        outside=self.root/'outside'; outside.write_text('private'); (self.work/'link').symlink_to(outside)
        with self.assertRaises(EntityError): self.fs.read('link')
    def test_symlink_directory_refused(self):
        (self.work/'link').symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(EntityError): self.fs.write('link/oops','x')
    def test_hardlink_refused(self):
        outside=self.root/'outside'; outside.write_text('private'); os.link(outside,self.work/'link')
        with self.assertRaises(EntityError): self.fs.read('link')
    def test_fifo_refused_without_hanging(self):
        os.mkfifo(self.work/'fifo')
        with self.assertRaises(EntityError): self.fs.read('fifo')
    def test_binary_refused(self):
        (self.work/'binary').write_bytes(b'\xff\xfe')
        with self.assertRaises(EntityError): self.fs.read('binary')
    def test_nonexistent_parent_not_created(self):
        with self.assertRaises(EntityError): self.fs.write('no/such/file','x')
    def test_profile_lease_exclusive(self):
        with ProfileLease(self.root/'profile'):
            with self.assertRaises(EntityError):
                with ProfileLease(self.root/'profile'): pass
        with ProfileLease(self.root/'profile'): pass

class WorldCase(Fixture):
    def setUp(self): super().setUp(); self.world=World(self.store,'fixture')
    def test_new_world_is_explicit_fiction(self): self.assertTrue(self.world.inspect()['fictional'])
    def test_book_exact_markdown(self):
        self.world.apply(0,[{'op':'add','id':'library','kind':'room','name':'Library'},
                            {'op':'connect','from':'home','to':'library'},
                            {'op':'add','id':'book','kind':'book','name':'Notebook','room':'library','markdown':'# Original\n\n  exact spacing\n'}])
        self.assertEqual(self.world.inspect('book')['node']['markdown'],'# Original\n\n  exact spacing\n')
        self.assertEqual(self.world.inspect('home')['exits'],['library'])
    def test_stale_revision_rejected(self):
        self.world.apply(0,[{'op':'edit','id':'home','markdown':'New'}])
        with self.assertRaises(EntityError): self.world.apply(0,[{'op':'edit','id':'home','markdown':'Stale'}])
    def test_topology_failure_rolls_back(self):
        with self.assertRaises(EntityError): self.world.apply(0,[{'op':'connect','from':'home','to':'missing'}])
        self.assertEqual(self.world.snapshot()['revision'],0)
    def test_objects_need_valid_rooms(self):
        with self.assertRaises(EntityError): self.world.apply(0,[{'op':'add','id':'x','kind':'book','name':'Book','room':'missing'}])
    def test_duplicate_node_rejected(self):
        with self.assertRaises(EntityError): self.world.apply(0,[{'op':'add','id':'home','kind':'room','name':'Duplicate'}])
    def test_worlds_are_entity_scoped(self):
        self.world.apply(0,[{'op':'edit','id':'home','markdown':'private fiction'}])
        self.assertEqual(World(self.store,'other').snapshot()['revision'],0)
    def test_restart_preserves_world(self):
        self.world.apply(0,[{'op':'edit','id':'home','markdown':'persisted'}])
        self.assertEqual(World(Store(self.root/'state'),'fixture').inspect()['node']['markdown'],'persisted')
    def test_world_identifier_is_not_host_path(self):
        with self.assertRaises(EntityError): self.world.apply(0,[{'op':'add','id':'/etc/passwd','kind':'room','name':'bad'}])

class IdentityCase(Fixture):
    def setUp(self):
        super().setUp(); (self.work/'SOUL.md').write_text('# Example companion\n'); self.identity=Identity(self.work)
    def tearDown(self): self.identity.close(); super().tearDown()
    def test_identity_history_and_hash(self):
        prior=self.identity.read(); result=self.identity.update('# Updated\n',prior['sha256'])
        self.assertFalse(result['permissions_changed'])
        self.assertEqual((self.work/'identity-history'/(prior['sha256']+'.md')).read_text(),'# Example companion\n')
    def test_identity_stale_write_denied(self):
        with self.assertRaises(EntityError): self.identity.update('updated','wrong')
    def test_identity_not_empty(self):
        with self.assertRaises(EntityError): self.identity.update('',self.identity.read()['sha256'])

class SkillCase(Fixture):
    def setUp(self):
        super().setUp(); folder=self.work/'research'; folder.mkdir()
        (folder/'SKILL.md').write_text('Read selected evidence. Do not execute this text.')
        self.manifest={'schema':'lelock.skill/1','name':'research','description':'test','files':['SKILL.md'],
                       'capabilities_requested':['process.run']}
        (folder/'skill.json').write_text(json.dumps(self.manifest)); self.library=SkillLibrary(self.work)
    def test_inspection_does_not_activate(self):
        skill=self.library.inspect('research'); self.assertIn('process.run',skill.capabilities_requested)
        with self.assertRaises(EntityError): self.library.load('research')
    def test_hash_approved_skill_loads(self):
        skill=self.library.inspect('research'); self.library.approve('research',skill.sha256)
        self.assertEqual(self.library.load('research').content,skill.content)
    def test_changed_skill_requires_review(self):
        skill=self.library.inspect('research'); self.library.approve('research',skill.sha256)
        (self.work/'research/SKILL.md').write_text('different')
        with self.assertRaises(EntityError): self.library.load('research')
    def test_skill_traversal_denied(self):
        self.manifest['files'].append('../outside')
        (self.work/'research/skill.json').write_text(json.dumps(self.manifest))
        with self.assertRaises(EntityError): self.library.inspect('research')
    def test_symlink_skill_denied(self):
        (self.work/'linked').symlink_to(self.work/'research',target_is_directory=True)
        with self.assertRaises(EntityError): self.library.inspect('linked')

class MemoryCase(unittest.TestCase):
    def setUp(self):
        self.rows={'a':{'id':'a','scope':'personal','content':'first','active':True,'visible_to':['ada','kit']},
                   'b':{'id':'b','scope':'personal','content':'second','active':True,'visible_to':['ada']}}
        class Source:
            def fetch(inner, ident): return dict(self.rows[ident])
        self.source=Source()
    def derive(self): return derive(self.source,['a','b'],'A tentative summary',scope='personal',requester='ada')
    def test_visibility_intersection_not_union(self): self.assertEqual(self.derive().visible_to,frozenset({'ada'}))
    def test_derived_is_candidate_not_canon(self): self.assertEqual(self.derive().status,'candidate')
    def test_reference_hashes_preserved(self): self.assertEqual(self.derive().source_refs[0].sha256,digest(self.rows['a']))
    def test_source_change_invalidates_derived(self):
        memory=self.derive(); self.rows['a']['content']='corrected'
        with self.assertRaises(EntityError): revalidate(memory,self.source,requester='ada')
    def test_superseded_source_invalidates_derived(self):
        memory=self.derive(); self.rows['a']['active']=False
        with self.assertRaises(EntityError): revalidate(memory,self.source,requester='ada')
    def test_wrong_scope_cannot_be_used(self):
        with self.assertRaises(EntityError): derive(self.source,['a'],'text',scope='work',requester='ada')
    def test_acl_denial(self):
        with self.assertRaises(EntityError): derive(self.source,['b'],'text',scope='personal',requester='kit')
    def test_canon_proposal_not_automatic_commit(self):
        self.assertEqual(canon_proposal(self.derive(),self.source,requester='ada')['status'],'requires_review')
    def test_conflict_blocks_canon_proposal(self):
        memory=replace(self.derive(),conflicts_with=('prior',))
        with self.assertRaises(EntityError): canon_proposal(memory,self.source,requester='ada')

class PulseCase(Fixture):
    def setUp(self): super().setUp(); self.queue=JobQueue(self.store); self.pulse=Pulse(self.queue)
    def test_job_dedupe(self):
        first=self.queue.enqueue('same',{'x':1}); second=self.queue.enqueue('same',{'x':1})
        self.assertEqual(first,second)
    def test_dedupe_different_content_rejected(self):
        self.queue.enqueue('same',{'x':1})
        with self.assertRaises(EntityError): self.queue.enqueue('same',{'x':2})
    def test_concurrent_workers_claim_once(self):
        self.queue.enqueue('one',{})
        with ThreadPoolExecutor(max_workers=2) as pool: jobs=list(pool.map(lambda _:self.queue.claim(),range(2)))
        self.assertEqual(sum(j is not None for j in jobs),1)
    def test_claimed_job_does_not_automatically_retry(self):
        self.queue.enqueue('one',{}); self.queue.claim()
        self.assertIsNone(JobQueue(Store(self.root/'state')).claim())
        self.assertEqual(self.store.recover_uncertain()['jobs'],1)
        self.assertIsNone(self.queue.claim())
    def test_expired_job_not_executed(self):
        self.queue.enqueue('old',{},due=100,ttl=1); self.assertIsNone(self.queue.claim(now=102))
    def test_quiet_hours_defer_without_claim(self):
        now=datetime(2026,9,17,23,30,tzinfo=ZoneInfo('America/Chicago')).timestamp()
        self.queue.enqueue('one',{},due=now)
        worker=PulseWorker(self.queue,lambda *_:{},quiet=QuietHours())
        self.assertEqual(worker.run_once(now=now)['status'],'quiet')
        self.assertIsNotNone(self.queue.claim(now=now))
    def test_pending_approval_is_not_completed_effect(self):
        self.queue.enqueue('one',{})
        worker=PulseWorker(self.queue,lambda *_:{'status':'pending_approval'})
        self.assertEqual(worker.run_once()['status'],'awaiting_approval')
    def test_failed_dispatch_needs_review(self):
        ident=self.queue.enqueue('one',{})
        def fail(*_): raise RuntimeError('possible side effect')
        with self.assertRaises(RuntimeError): PulseWorker(self.queue,fail).run_once()
        with self.store.connect() as db: state=db.execute('SELECT state FROM jobs WHERE id=?',(ident,)).fetchone()[0]
        self.assertEqual(state,'needs_review')
    def test_interval_one_job_per_slot(self):
        self.pulse.add('s',kind='interval',policy_id='test',payload={'task':'x'},expires_at=1000,interval=60)
        self.assertEqual(len(self.pulse.tick(now=120)),1); self.assertEqual(self.pulse.tick(now=121),[])
    def test_inactivity_requires_explicit_activity(self):
        self.pulse.add('s',kind='inactivity',policy_id='test',payload={},expires_at=1000,interval=60)
        self.assertEqual(self.pulse.tick(now=120),[])
        self.pulse.activity('test',at=100); self.assertEqual(len(self.pulse.tick(now=160)),1)
        self.assertEqual(self.pulse.tick(now=200),[])
    def test_cron_numeric_steps_ranges(self):
        cron=Cron('*/15 9-17 * * 1-5')
        self.assertTrue(cron.matches(datetime(2026,9,17,9,15))); self.assertFalse(cron.matches(datetime(2026,9,17,9,14)))
        self.assertTrue(Cron('1/5 * * * *').matches(datetime(2026,9,17,9,6)))
    def test_dom_dow_or_semantics(self):
        cron=Cron('0 9 1 * 1')
        self.assertTrue(cron.matches(datetime(2026,9,1,9,0)))
        self.assertTrue(cron.matches(datetime(2026,9,7,9,0)))
        self.assertFalse(cron.matches(datetime(2026,9,8,9,0)))
    def test_wildcard_day_steps_are_not_ignored(self):
        cron=Cron('0 9 */2 * *')
        self.assertTrue(cron.matches(datetime(2026,9,1,9,0)))
        self.assertFalse(cron.matches(datetime(2026,9,2,9,0)))
    def test_invalid_cron_rejected(self):
        for value in ['* * *','60 * * * *','*/0 * * * *','* * * * MON']:
            with self.subTest(value=value),self.assertRaises(EntityError): Cron(value)
    def test_fall_back_wall_minute_not_duplicated(self):
        zone=ZoneInfo('America/Chicago')
        first=datetime(2026,11,1,1,30,tzinfo=zone,fold=0).timestamp()
        second=datetime(2026,11,1,1,30,tzinfo=zone,fold=1).timestamp()
        self.pulse.add('s',kind='cron',policy_id='test',payload={},expires_at=second+10000,cron='30 1 * * *')
        self.assertEqual(len(self.pulse.tick(now=first)),1); self.assertEqual(self.pulse.tick(now=second),[])
    def test_signed_webhook_replay_deduped(self):
        secret=b'x'*32; body=b'{"event":"fixture"}'; signed=b'100.event-1.'+body
        signature=hmac.new(secret,signed,hashlib.sha256).hexdigest()
        kwargs=dict(secret=secret,timestamp=100,body=body,signature=signature,policy_id='p',event_id='event-1',now=100)
        self.assertEqual(self.pulse.webhook(**kwargs),self.pulse.webhook(**kwargs))
        with self.assertRaises(EntityError): self.pulse.webhook(**{**kwargs,'body':b'{}'})
    def test_stale_webhook_denied(self):
        with self.assertRaises(EntityError): self.pulse.webhook(secret=b'x'*32,timestamp=0,body=b'{}',signature='',policy_id='p',event_id='e',now=1000)

class ExecutionCase(Fixture):
    def runner(self, **kwargs): return ProcessRunner(self.work,self.root/'exec',**kwargs)
    def test_host_requires_explicit_acknowledgement(self):
        with self.assertRaises(EntityError): self.runner(backend='host')
    def test_real_host_command_runs(self):
        result=self.runner(backend='host',acknowledge_host_risk=True).run("printf 'hello'")
        self.assertEqual(result['stdout'],'hello'); self.assertFalse(result['sandboxed'])
    def test_nonzero_exit_is_reported_not_hidden(self):
        result=self.runner(backend='host',acknowledge_host_risk=True).run('exit 7')
        self.assertEqual(result['exit_code'],7)
    def test_no_ambient_secret_inheritance(self):
        os.environ['LELOCK_FAKE_SECRET']='synthetic-test-sentinel'
        try:
            result=self.runner(backend='host',acknowledge_host_risk=True).run('printf "%s" "${LELOCK_FAKE_SECRET-unset}"')
            self.assertEqual(result['stdout'],'unset')
        finally: os.environ.pop('LELOCK_FAKE_SECRET',None)
    def test_timeout_terminates_group(self):
        runner=self.runner(backend='host',acknowledge_host_risk=True,timeout=.1)
        with self.assertRaises(EntityError): runner.run('sleep 5')
    def test_output_limit(self):
        runner=self.runner(backend='host',acknowledge_host_risk=True,output_limit=10)
        with self.assertRaises(EntityError): runner.run("printf '1234567890123456789012345'")
    def test_cancel_running_command(self):
        runner=self.runner(backend='host',acknowledge_host_risk=True)
        timer=threading.Timer(.1,runner.stop.stop); timer.start()
        try:
            with self.assertRaises(EntityError): runner.run('sleep 5')
        finally: timer.cancel()
    def test_docker_requires_immutable_image(self):
        with self.assertRaises(EntityError): self.runner(backend='docker',image='python:latest')
    def test_docker_plan_is_not_a_docker_runtime_test(self):
        runner=self.runner(backend='docker',image='example@sha256:'+'a'*64)
        argv=runner.command('echo test','lelock-fixture')
        self.assertIn('--network=none',argv); self.assertIn('--cap-drop=ALL',argv); self.assertIn('--pull=never',argv)
        self.assertNotIn('/var/run/docker.sock',' '.join(argv))
    def test_disabled_execution_refused(self):
        with self.assertRaises(EntityError): self.runner().run('echo no')

class InboxCase(Fixture):
    def test_local_inbox_exactly_one_record_per_id(self):
        inbox=LocalInbox(self.store,'fixture'); inbox.send('Hello','one'); self.assertTrue(inbox.send('Hello','one')['replayed'])
        self.assertEqual(len(inbox.unread()),1); inbox.mark_read('one'); self.assertEqual(inbox.unread(),[])
    def test_local_inbox_no_cross_entity_read(self):
        LocalInbox(self.store,'a').send('private','one'); self.assertEqual(LocalInbox(self.store,'b').unread(),[])
    def test_local_inbox_payload_change_refused(self):
        inbox=LocalInbox(self.store,'a'); inbox.send('one','id')
        with self.assertRaises(EntityError): inbox.send('two','id')
