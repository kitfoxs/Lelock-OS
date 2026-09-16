"""Publication-only regression tests, runnable without the missing application.
Temporary placeholder modules are fixture data, never replacement release source.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publication', ROOT / 'project/scripts/check_publication.py')
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Synthetic test')
        self.git('config', 'user.email', 'synthetic@example.invalid')
        (self.root / 'project').mkdir()
        (self.root / 'project/.gitignore').write_text((ROOT / 'project/.gitignore').read_text())
        shutil.copytree(ROOT / 'integrations/sillytavern', self.root / 'integrations/sillytavern')
        # Layout fixtures only: these tests do not execute template/CSS rendering.
        for name in ('settings.html', 'style.css'):
            (self.root / 'integrations/sillytavern' / name).write_text('SYNTHETIC LAYOUT FIXTURE\n')
        self.commit()

    def git(self, *args, check=True):
        return subprocess.run(['git', '-C', str(self.root), *args], check=check,
                              capture_output=True, text=True)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'Synthetic fixture')

    def source(self):
        for n in publication.REQUIRED:
            p = self.root / 'project/src/lelock' / n
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('# SYNTHETIC TEST FIXTURE ONLY\n')

    def check(self, name, **kwargs):
        return next(c['status'] for c in publication.inspect(self.root, **kwargs)['checks'] if c['check'] == name)

    def test_missing_source_cannot_pass(self):
        self.assertEqual(publication.inspect(self.root)['status'], 'FAIL')
        self.assertEqual(self.check('required_source'), 'FAIL')

    def test_untracked_source_cannot_pass(self):
        self.source()
        self.assertEqual(self.check('required_source'), 'PASS')
        self.assertEqual(self.check('committed_source'), 'FAIL')

    def test_staged_but_uncommitted_source_cannot_pass(self):
        self.source(); self.git('add', '.')
        self.assertEqual(self.check('committed_source'), 'FAIL')

    def test_committed_fixture_has_valid_layout(self):
        self.source(); self.commit()
        self.assertEqual(publication.inspect(self.root)['status'], 'PASS')

    def test_modified_committed_source_fails(self):
        self.source(); self.commit()
        (self.root / 'project/src/lelock/cli.py').write_text('# changed fixture\n')
        self.assertEqual(self.check('committed_source'), 'FAIL')

    def test_git_ignores_launcher_not_source(self):
        self.source()
        (self.root / 'project/lelock').write_text('# generated launcher fixture\n')
        self.assertEqual(self.git('check-ignore', '--no-index', 'project/lelock', check=False).returncode, 0)
        self.assertEqual(self.git('check-ignore', '--no-index', 'project/src/lelock/cli.py', check=False).returncode, 1)

    def test_old_ignore_rule_is_rejected(self):
        (self.root / 'project/.gitignore').write_text('lelock\n')
        self.assertEqual(self.check('launcher_ignore'), 'FAIL')

    def test_old_extension_imports_are_rejected(self):
        p = self.root / 'integrations/sillytavern/index.js'
        p.write_text(p.read_text().replace("from '../../../extensions.js'", "from '../../extensions.js'"))
        self.assertEqual(self.check('extension_imports'), 'FAIL')

    def test_missing_archives_fail_optional_gate(self):
        self.source(); self.commit()
        self.assertEqual(publication.inspect(self.root, True)['status'], 'FAIL')

    def test_checksum_gate_detects_wrong_archive(self):
        self.source(); self.commit()
        resources = self.root / 'project/resources'; resources.mkdir()
        upstream = self.root / 'upstream'; upstream.mkdir()
        data = b'SYNTHETIC ARCHIVE BYTES FOR DIGEST TEST ONLY'
        sources = {}
        for name in ('hermes', 'mempalace'):
            filename = name + '.zip'
            (upstream / filename).write_bytes(data)
            sources[name] = {'file': filename, 'sha256': hashlib.sha256(data).hexdigest()}
        (resources / 'source-lock.json').write_text(json.dumps({'sources': sources}))
        self.assertEqual(publication.inspect(self.root, True)['status'], 'PASS')
        (upstream / 'hermes.zip').write_bytes(b'changed')
        self.assertEqual(self.check('source_hermes', require_upstream=True), 'FAIL')

    def test_verify_refuses_missing_source_without_test_receipts(self):
        scripts = self.root / 'project/scripts'; scripts.mkdir()
        shutil.copy2(ROOT / 'project/scripts/verify.py', scripts / 'verify.py')
        result = subprocess.run([sys.executable, str(scripts / 'verify.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['tests_executed'], 0)
        self.assertFalse((self.root / 'receipts').exists())

    def test_bootstrap_refuses_missing_source_before_runtime_creation(self):
        scripts = self.root / 'project/scripts'; scripts.mkdir()
        resources = self.root / 'project/resources'; resources.mkdir()
        (resources / 'source-lock.json').write_text('{"sources":{}}')
        shutil.copy2(ROOT / 'project/scripts/bootstrap.py', scripts / 'bootstrap.py')
        result = subprocess.run([sys.executable, str(scripts / 'bootstrap.py')], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Application source is missing', result.stderr)
        self.assertFalse((self.root / 'project/.runtime').exists())


if __name__ == '__main__':
    unittest.main()
