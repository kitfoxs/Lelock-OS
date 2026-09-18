from dataclasses import replace
import json
from pathlib import Path
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from lelock_entity.common import EntityError, digest, object_schema, strict_json, validate
from lelock_entity.policy import Session, Mode, Risk, Budget
from lelock_entity.core import EntityCore, Tool
from lelock_entity.store import Store
from lelock_entity.workspace import Workspace
from lelock_entity.world import World
from lelock_entity.builtins import install
from lelock_entity.delegation import Delegator

class CoreCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'work').mkdir()
        self.files = Workspace(self.root / 'work')
        self.store = Store(self.root / 'state')
        self.calls = []
        self.caps = frozenset({'status.read', 'workspace.read', 'workspace.write', 'workspace.delete',
                               'world.read', 'world.write', 'delegate.run'})
    def tearDown(self):
        self.files.close()
        self.tmp.cleanup()
    def core(self, mode=Mode.SAFE, caps=None, auto=frozenset(), budget=None):
        session = Session('fixture', 'test', self.caps if caps is None else caps, mode, auto)
        core = EntityCore(self.store, session, budget=budget)
        install(core, self.files, World(self.store, 'fixture'))
        return core
    def write(self, core, rid='write'):
        return core.invoke('lelock_propose_text', {'path':'file.txt','content':'exact bytes\n'}, request_id=rid)

    def test_safe_proposes_without_writing(self):
        result = self.write(self.core())
        self.assertEqual(result['status'], 'pending_approval')
        self.assertFalse((self.root / 'work/file.txt').exists())
    def test_safe_exact_approval_writes(self):
        core = self.core(); p = self.write(core)
        result = core.approve(p['action_id'], p['digest'])
        self.assertTrue(result['result']['verified'])
        self.assertEqual((self.root / 'work/file.txt').read_text(), 'exact bytes\n')
    def test_yolo_actually_executes(self):
        result = self.write(self.core(Mode.YOLO))
        self.assertEqual(result['status'], 'done')
        self.assertTrue((self.root / 'work/file.txt').exists())
    def test_yolo_does_not_create_capabilities(self):
        core = self.core(Mode.YOLO, frozenset({'status.read'}))
        with self.assertRaises(EntityError): self.write(core)
    def test_trusted_only_enabled_standing_grant(self):
        core = self.core(Mode.TRUSTED, auto=frozenset({'workspace.write'}))
        self.assertEqual(self.write(core)['status'], 'done')
        p = core.invoke('lelock_delete_text', {'path':'file.txt','expected_sha256':digest(b'exact bytes\n')})
        self.assertEqual(p['status'], 'pending_approval')
    def test_unknown_tool_denied_in_yolo(self):
        with self.assertRaises(EntityError): self.core(Mode.YOLO).invoke('approve_myself', {})
    def test_unknown_arguments_cannot_change_mode(self):
        with self.assertRaises(EntityError): self.core().invoke('lelock_propose_text', {'path':'x','content':'x','mode':'yolo'})
    def test_operator_approval_digest_must_match(self):
        core = self.core(); p = self.write(core)
        with self.assertRaises(EntityError): core.approve(p['action_id'], 'wrong')
    def test_reject_is_terminal(self):
        core = self.core(); p = self.write(core)
        core.reject(p['action_id'])
        with self.assertRaises(EntityError): core.approve(p['action_id'], p['digest'])
    def test_double_approval_denied(self):
        core = self.core(); p = self.write(core)
        core.approve(p['action_id'], p['digest'])
        with self.assertRaises(EntityError): core.approve(p['action_id'], p['digest'])
    def test_retry_returns_receipt_not_second_effect(self):
        core = self.core(Mode.YOLO)
        first = self.write(core); second = self.write(core)
        self.assertEqual(first['action_id'], second['action_id'])
        self.assertTrue(second['replayed'])
    def test_request_id_cannot_change_payload(self):
        core = self.core(); self.write(core)
        with self.assertRaises(EntityError):
            core.invoke('lelock_propose_text', {'path':'other','content':'different'}, request_id='write')
    def test_expired_proposal_cannot_execute(self):
        core = self.core(); p = self.write(core)
        with self.store.connect() as db:
            db.execute('UPDATE actions SET expires=0 WHERE id=?', (p['action_id'],))
        with self.assertRaises(EntityError): core.approve(p['action_id'], p['digest'])
    def test_manifest_change_invalidates_approval(self):
        core = self.core(); p = self.write(core)
        core.tools['lelock_propose_text'] = replace(core.tools['lelock_propose_text'], version='2')
        with self.assertRaises(EntityError): core.approve(p['action_id'], p['digest'])
    def test_tampered_stored_payload_denied(self):
        core = self.core(); p = self.write(core)
        row = self.store.get(p['action_id']); payload = json.loads(row['payload']); payload['arguments']['content'] = 'changed'
        with self.store.connect() as db: db.execute('UPDATE actions SET payload=? WHERE id=?',(json.dumps(payload), p['action_id']))
        with self.assertRaises(EntityError): core.approve(p['action_id'], p['digest'])
    def test_changed_session_object_not_trusted(self):
        core = self.core(); impostor = replace(core.session, mode=Mode.YOLO)
        with self.assertRaises(EntityError): core.invoke('lelock_status', {}, session=impostor)
    def test_expired_session_denied(self):
        core = self.core(); expired = replace(core.session, expires_at=0)
        core.sessions[expired.ident] = expired
        with self.assertRaises(EntityError): core.invoke('lelock_status', {}, session=expired)
    def test_new_session_cannot_approve_old_action(self):
        p = self.write(self.core())
        with self.assertRaises(EntityError): self.core().approve(p['action_id'], p['digest'])
    def test_stop_prevents_commit(self):
        core = self.core(); p = self.write(core); core.stop.stop()
        with self.assertRaises(EntityError): core.approve(p['action_id'], p['digest'])
    def test_budget_applies_to_reads_and_writes(self):
        core = self.core(Mode.YOLO, budget=Budget(max_actions=1))
        core.invoke('lelock_status', {})
        with self.assertRaises(EntityError): self.write(core)
    def test_uncertain_effect_does_not_replay(self):
        core = self.core(Mode.YOLO)
        def fail(args, session):
            self.calls.append(1); raise RuntimeError('after side effect')
        core.register(Tool('uncertain','test','workspace.write',Risk.WRITE,object_schema({}),fail))
        with self.assertRaises(RuntimeError): core.invoke('uncertain',{},request_id='one')
        retry = core.invoke('uncertain',{},request_id='one')
        self.assertEqual(retry['status'],'needs_review'); self.assertEqual(len(self.calls),1)
    def test_concurrent_same_request_only_one_effect(self):
        core = self.core(Mode.YOLO)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _:self.write(core), range(2)))
        self.assertEqual(len({r['action_id'] for r in results}),1)
        self.assertEqual(sum(bool(r.get('replayed')) for r in results),1)
    def test_child_cannot_gain_capability(self):
        core = self.core()
        with self.assertRaises(EntityError): core.register_child(core.session, {'network.everything'})
    def test_child_depth_bound(self):
        core = self.core(); child=core.register_child(core.session, {'status.read'}); grand=core.register_child(child, {'status.read'})
        with self.assertRaises(EntityError): core.register_child(grand, {'status.read'})
    def test_child_shares_parent_budget(self):
        core = self.core(budget=Budget(max_actions=1)); child=core.register_child(core.session, {'status.read'})
        core.invoke('lelock_status',{},session=child)
        with self.assertRaises(EntityError): core.invoke('lelock_status',{})
    def test_delegation_revokes_child_after_result(self):
        core = self.core(Mode.YOLO); child_ids=[]
        def executor(task, call):
            child_ids.append(task.session.ident)
            return call('lelock_status',{})
        result=Delegator(core).run('test',{'status.read'},executor)
        self.assertEqual(result['authority'],'untrusted_task_result')
        self.assertNotIn(child_ids[0],core.sessions)
    def test_recovery_marks_inflight_uncertain(self):
        core=self.core(); p=self.write(core)
        self.store.claim(p['action_id'],p['digest'],core.session.entity,core.session.ident)
        self.assertEqual(self.store.recover_uncertain()['actions'],1)
        self.assertEqual(self.store.get(p['action_id'])['state'],'needs_review')
    def test_recorded_yolo_approval_source(self):
        core=self.core(Mode.YOLO); p=self.write(core)
        result=json.loads(self.store.get(p['action_id'])['result'])
        self.assertEqual(result['approved_by'],'policy:yolo')

class ValidationCase(unittest.TestCase):
    def test_duplicate_keys_rejected(self):
        with self.assertRaises(EntityError): strict_json('{"x":1,"x":2}')
    def test_nonfinite_numbers_rejected(self):
        for value in ['NaN','Infinity','-Infinity']:
            with self.subTest(value=value), self.assertRaises(EntityError): strict_json(value)
    def test_boolean_is_not_integer(self):
        with self.assertRaises(EntityError): validate({'type':'integer'},True)
    def test_auto_approval_cannot_grant_new_capability(self):
        with self.assertRaises(EntityError): Session('x','test',frozenset(),auto_approve=frozenset({'execute'}))
    def test_invalid_scope_rejected(self):
        with self.assertRaises(EntityError): Session('x','all',frozenset())
