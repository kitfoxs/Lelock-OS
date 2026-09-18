import tempfile
import unittest
from pathlib import Path

from helpers import make_service
from lelock.common import LelockError
from lelock.server import LelockBridgeServer


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = make_service(self.root)
        self.bridge = LelockBridgeServer(self.service, host='127.0.0.1', port=0)

    def tearDown(self):
        self.bridge.shutdown()
        self.tmp.cleanup()

    def test_legacy_bridge_quarantined(self):
        with self.assertRaises(LelockError) as ctx:
            self.bridge.start(blocking=False)
        self.assertIn('Legacy unauthenticated bridge is quarantined', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
