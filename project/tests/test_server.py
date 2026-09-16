import json
from pathlib import Path
import tempfile
import urllib.request
import unittest

from helpers import make_service, FixturePalace
from lelock.server import LelockBridgeServer


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = make_service(self.root)
        # Start server on dynamic port 0
        self.bridge = LelockBridgeServer(self.service, host='127.0.0.1', port=0)
        self.bridge.start(blocking=False)
        self.port = self.bridge.server.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"

    def tearDown(self):
        self.bridge.shutdown()
        self.tmp.cleanup()

    def _get(self, path):
        req = urllib.request.Request(f"{self.base}{path}")
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))

    def _post(self, path, payload):
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(f"{self.base}{path}", data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))

    def test_status_endpoint(self):
        status, body = self._get('/status')
        self.assertEqual(status, 200)
        self.assertTrue(body['ok'])
        self.assertEqual(body['companion'], 'Samantha')
        self.assertEqual(body['pending_proposals_count'], 0)

    def test_proposals_and_approval_flow(self):
        # 1. Propose write
        status, p_res = self._post('/api/proposals/create', {
            'action': 'write',
            'path': 'test_agent_script.py',
            'content': 'print("Hello from SillyTavern Companion!")\n'
        })
        self.assertEqual(status, 200)
        self.assertTrue(p_res['ok'])
        prop_id = p_res['proposal']['proposal_id']

        # 2. Check pending
        status, pend = self._get('/api/proposals/pending')
        self.assertEqual(status, 200)
        self.assertEqual(len(pend['proposals']), 1)
        self.assertEqual(pend['proposals'][0]['id'], prop_id)

        # 3. Approve proposal
        status, a_res = self._post('/api/proposals/approve', {'id': prop_id})
        self.assertEqual(status, 200)
        self.assertTrue(a_res['ok'])

        # 4. Read back committed file
        status, f_res = self._post('/api/read-file', {'path': 'test_agent_script.py'})
        self.assertEqual(status, 200)
        self.assertIn('Hello from SillyTavern', f_res['file']['content'])

    def test_memory_remember_and_recall(self):
        # Remember
        status, rem_res = self._post('/api/remember', {
            'content': 'Kit loves dark roasted coffee with oat milk.',
            'kind': 'preference',
        })
        self.assertEqual(status, 200)
        self.assertTrue(rem_res['ok'])

        # Recall
        status, rec_res = self._post('/api/recall', {
            'query': 'coffee',
        })
        self.assertEqual(status, 200)
        self.assertTrue(rec_res['ok'])
        self.assertEqual(rec_res['status'], 'found')
        self.assertEqual(len(rec_res['memories']), 1)
        self.assertIn('dark roasted coffee', rec_res['memories'][0]['content'])
