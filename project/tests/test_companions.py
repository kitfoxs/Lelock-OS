import tempfile
import unittest
from pathlib import Path

from helpers import make_service
from lelock.common import read_json
from lelock.config import initialize, Config
from lelock.companions import (
    list_companions,
    find_companion,
    get_catalog,
    stage_companion,
    activate_companion,
    seed_companion_lore,
)


class CompanionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / 'home'
        self.ws = self.root / 'ws'
        initialize(
            self.home,
            self.ws,
            name='Test Companion',
            person='Kit',
            relationship='romance',
            endpoint='http://127.0.0.1:1234/v1',
            model='test',
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_catalog_integrity(self):
        catalog = get_catalog()
        self.assertEqual(catalog['schema'], 'lelock.companions-catalog/1')
        self.assertEqual(catalog['count'], 42)
        self.assertEqual(len(list_companions('fursona')), 14)
        self.assertEqual(len(list_companions('romance')), 14)
        self.assertEqual(len(list_companions('anime')), 14)

    def test_find_companion(self):
        c1 = find_companion('cinder_ashgrave')
        self.assertEqual(c1['name'], 'Cinder Ashgrave')
        c2 = find_companion('Selene Noctelle')
        self.assertEqual(c2['id'], 'selene_noctelle')
        c3 = find_companion('Amara')
        self.assertEqual(c3['name'], 'Amara Sunscale')
        c4 = find_companion('Akari')
        self.assertEqual(c4['name'], 'Akari Mizuno')
        self.assertEqual(c4['collection'], 'anime')

    def test_stage_and_activate_companion(self):
        staged = stage_companion(self.home, 'cinder_ashgrave')
        self.assertEqual(staged['data']['name'], 'Cinder Ashgrave')
        self.assertEqual(staged['collection'], 'fursona')

        res = activate_companion(self.home, 'cinder_ashgrave')
        self.assertEqual(res['name'], 'Cinder Ashgrave')

        soul = (self.home / 'SOUL.md').read_text('utf-8')
        self.assertIn('Cinder Ashgrave', soul)
        self.assertIn('Kit', soul)

        cfg = Config.load(self.home)
        self.assertEqual(cfg.companion_name, 'Cinder Ashgrave')

    def test_seed_companion_lore(self):
        fiction_root = self.root / 'fiction'
        service = make_service(fiction_root, scope='fiction')
        comp = find_companion('amara_sunscale')
        lore_res = seed_companion_lore(service, comp)
        self.assertEqual(lore_res['seeded_entries'], 8)
        self.assertTrue(len(lore_res['topics']) > 0)
        hits = service.recall('studio')
        self.assertTrue(len(hits['memories']) > 0)

        personal_service = make_service(self.root / 'personal', scope='personal')
        skipped = seed_companion_lore(personal_service, comp)
        self.assertEqual(skipped['seeded_entries'], 0)
        self.assertIn('skipped', skipped)


if __name__ == '__main__':
    unittest.main()
