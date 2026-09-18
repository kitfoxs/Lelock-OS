from dataclasses import replace
import http.client
import json
from pathlib import Path
import tempfile
import unittest
from lelock_entity.policy import Session, Mode
from lelock_entity.store import Store
from lelock_entity.core import EntityCore
from lelock_entity.workspace import Workspace
from lelock_entity.world import World
from lelock_entity.builtins import install
from lelock_entity.http_bridge import Bridge
from lelock_entity.common import EntityError, canonical
from lelock_entity.client import Client

class HttpCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); root=Path(cls.tmp.name); work=root/'work'; work.mkdir()
        cls.files=Workspace(work)
        cls.core=EntityCore(Store(root/'state'),Session('fixture','test',frozenset({'status.read','workspace.read','workspace.write','world.read'})))
        install(cls.core,cls.files,World(cls.core.store,'fixture'))
        cls.bridge=Bridge(cls.core,origins=('http://localhost:8000',)).start()
    @classmethod
    def tearDownClass(cls): cls.bridge.close(); cls.files.close(); cls.tmp.cleanup()
    def request(self,path,*,method='GET',body=None,token='agent',headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.bridge.port,timeout=3)
        values={'Content-Type':'application/json'}
        if token=='agent': values['Authorization']='Bearer '+self.bridge.agent_token
        elif token=='operator': values['Authorization']='Bearer '+self.bridge.operator_token
        elif token is not None: values['Authorization']='Bearer '+token
        values.update(headers or {})
        raw=canonical(body) if isinstance(body,dict) else body
        connection.request(method,path,body=raw,headers=values)
        response=connection.getresponse(); result=(response.status,dict(response.getheaders()),json.loads(response.read()))
        connection.close(); return result
    def test_unauthenticated_status_denied(self): self.assertEqual(self.request('/v1/status',token=None)[0],401)
    def test_bad_token_denied(self): self.assertEqual(self.request('/v1/status',token='wrong')[0],403)
    def test_agent_can_read_status(self): self.assertEqual(self.request('/v1/status')[0],200)
    def test_nonascii_token_refused(self):
        self.assertEqual(self.request('/v1/status', headers={'Authorization':'Bearer caf\u00e9'})[0],403)
    def test_oversized_token_refused(self):
        self.assertEqual(self.request('/v1/status', headers={'Authorization':'Bearer '+'a'*300})[0],403)
    def test_response_no_store(self): self.assertEqual(self.request('/v1/status')[1]['Cache-Control'],'no-store')
    def test_unapproved_origin_denied_even_with_token(self):
        self.assertEqual(self.request('/v1/status',headers={'Origin':'https://untrusted.invalid'})[0],403)
    def test_null_origin_denied(self): self.assertEqual(self.request('/v1/status',headers={'Origin':'null'})[0],403)
    def test_exact_approved_origin_echoed_not_wildcard(self):
        result=self.request('/v1/status',headers={'Origin':'http://localhost:8000'})
        self.assertEqual(result[0],200); self.assertEqual(result[1]['Access-Control-Allow-Origin'],'http://localhost:8000')
    def test_dns_rebinding_host_denied(self):
        self.assertEqual(self.request('/v1/status',headers={'Host':f'hostile.invalid:{self.bridge.port}'})[0],403)
    def test_tokens_in_query_not_accepted(self): self.assertEqual(self.request('/v1/status?token=x')[0],400)
    def test_agent_cannot_access_operator_approval(self):
        self.assertEqual(self.request('/v1/operator/approve',method='POST',body={'action_id':'x','digest':'x'})[0],403)
    def test_agent_cannot_read_proposal_payloads(self): self.assertEqual(self.request('/v1/operator/actions')[0],403)
    def test_operator_can_read_actions(self): self.assertEqual(self.request('/v1/operator/actions',token='operator')[0],200)
    def test_memory_bypass_old_route_not_exposed(self):
        self.assertEqual(self.request('/api/remember',method='POST',body={'content':'should not save'})[0],404)
    def test_model_mode_change_rejected(self):
        body={'tool':'lelock_status','arguments_json':'{}','request_id':'bad-mode','mode':'yolo'}
        self.assertEqual(self.request('/v1/invoke',method='POST',body=body)[0],409)
    def test_duplicate_json_keys_rejected(self):
        raw='{"tool":"lelock_status","tool":"other","arguments_json":"{}","request_id":"dupe"}'
        self.assertEqual(self.request('/v1/invoke',method='POST',body=raw)[0],409)
    def test_top_level_array_rejected(self): self.assertEqual(self.request('/v1/invoke',method='POST',body='[]')[0],409)
    def test_form_request_rejected(self):
        self.assertEqual(self.request('/v1/invoke',method='POST',body='x=y',headers={'Content-Type':'application/x-www-form-urlencoded'})[0],409)
    def test_loopback_client_real_roundtrip(self):
        client=Client(f'http://127.0.0.1:{self.bridge.port}',self.bridge.agent_token)
        self.assertEqual(client.invoke('lelock_status',{})['status'],'done')
    def test_safe_http_action_requires_operator(self):
        body={'tool':'lelock_propose_text','arguments_json':canonical({'path':'http-created','content':'hello'}),'request_id':'http-write'}
        response=self.request('/v1/invoke',method='POST',body=body)
        self.assertEqual(response[2]['status'],'pending_approval')
        action={'action_id':response[2]['action_id'],'digest':response[2]['digest']}
        self.assertEqual(self.request('/v1/operator/approve',method='POST',body=action,token='operator')[2]['status'],'done')
    def test_weak_or_shared_tokens_rejected(self):
        with self.assertRaises(EntityError): Bridge(self.core,agent_token='a'*32,operator_token='a'*32)
    def test_wildcard_origin_configuration_rejected(self):
        with self.assertRaises(EntityError): Bridge(self.core,origins=('*',))
    def test_public_client_target_refused(self):
        with self.assertRaises(EntityError): Client('https://example.com','x'*32)
