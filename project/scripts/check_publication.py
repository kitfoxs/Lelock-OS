#!/usr/bin/env python3
"""Offline publication checks. No package install, network request or app import.
A PASS means this bounded layout check passed, not runtime/security acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import posixpath
import re
import subprocess
from pathlib import Path

REQUIRED = ('__init__.py', '__main__.py', 'cli.py', 'runtime.py', 'palace.py', 'hermes_plugin.py')
EXPECTED_IMPORTS = {
    '../../../extensions.js', '../../../../script.js', '../../../tool-calling.js',
    '../../../slash-commands/SlashCommandParser.js', '../../../slash-commands/SlashCommand.js',
    '../../../slash-commands/SlashCommandArgument.js', '../../../popup.js',
}


def inspect(root: Path, require_upstream: bool = False) -> dict:
    root = root.resolve()
    checks = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({'check': name, 'status': 'PASS' if passed else 'FAIL', 'detail': detail})

    package = root / 'project/src/lelock'
    missing = [n for n in REQUIRED if not (package / n).is_file() or (package / n).is_symlink()]
    add('required_source', not missing, 'Missing/non-regular: ' + ', '.join(missing) if missing else 'Required entry modules exist.')
    # Compare actual Python source bytes to committed HEAD, not merely a staged index.
    # This catches the original problem: a passing local suite with untracked source.
    try:
        result = subprocess.run(['git', '-C', str(root), 'ls-tree', '-r', '-z', '--name-only',
                                 'HEAD', '--', 'project/src/lelock'], capture_output=True, check=True)
        tracked = set(result.stdout.decode().split('\0')) - {''}
        problems = []
        paths = set('project/src/lelock/' + n for n in REQUIRED)
        paths.update(p.relative_to(root).as_posix() for p in package.rglob('*.py'))
        for rel in sorted(paths):
            file = root / rel
            if rel not in tracked:
                problems.append(rel + ': not committed')
            elif file.is_symlink() or not file.is_file():
                problems.append(rel + ': not a regular file')
            else:
                blob = subprocess.run(['git', '-C', str(root), 'cat-file', 'blob', 'HEAD:' + rel],
                                      capture_output=True, check=True).stdout
                if file.read_bytes() != blob:
                    problems.append(rel + ': differs from HEAD')
        add('committed_source', not problems, '; '.join(problems) or 'Python source matches committed HEAD.')
    except (OSError, UnicodeError, subprocess.CalledProcessError):
        add('committed_source', False, 'A Git checkout with a readable HEAD is required; this is not a ZIP certification.')
    ignore = root / 'project/.gitignore'
    rules = ignore.read_text().splitlines() if ignore.is_file() else []
    add('launcher_ignore', '/lelock' in rules and 'lelock' not in rules,
        'Use /lelock in project/.gitignore; a bare lelock hides the source package.')
    extension = root / 'integrations/sillytavern'
    try:
        manifest = json.loads((extension / 'manifest.json').read_text())
        add('extension_manifest', manifest.get('js') == 'index.js' and
            manifest.get('hooks', {}).get('activate') == 'init' and
            all((extension / n).is_file() for n in ('index.js', 'settings.html', 'style.css')),
            'Manifest/assets must be installed together in third-party/lelock-os, not at the monorepo root.')
        js = (extension / 'index.js').read_text()
        imports = set(re.findall(r"^import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", js, re.MULTILINE))
        resolved = {posixpath.normpath(posixpath.join('/scripts/extensions/third-party/lelock-os', p)) for p in imports}
        add('extension_imports', imports == EXPECTED_IMPORTS and '/script.js' in resolved
            and '/scripts/extensions.js' in resolved, 'Static URL layout only; not an executed SillyTavern integration.')
    except (OSError, ValueError, TypeError, AttributeError):
        add('extension_manifest', False, 'Missing or invalid extension files.')
    if require_upstream:
        try:
            lock = json.loads((root / 'project/resources/source-lock.json').read_text())
            for name in ('hermes', 'mempalace'):
                item = lock['sources'][name]
                filename = item['file']
                if Path(filename).name != filename or '\\' in filename:
                    raise ValueError('unsafe source filename')
                archive = root / 'upstream' / filename
                if not archive.is_file() or archive.is_symlink():
                    add('source_' + name, False, 'Missing regular upstream/' + filename)
                    continue
                digest = hashlib.sha256()
                with archive.open('rb') as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                        digest.update(chunk)
                add('source_' + name, digest.hexdigest() == item['sha256'], 'Exact archive checksum: ' + filename)
        except (OSError, ValueError, KeyError, TypeError):
            add('upstream_lock', False, 'Missing or invalid source lock.')
    return {'gate': 'publication_layout', 'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'FAIL',
            'checks': checks, 'does_not_prove': ['application tests', 'complete dependency install', 'bridge authentication',
            'actual Palace/model', 'macOS or human acceptance']}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-upstream', action='store_true', help='Also verify the two local locked source archives.')
    args = parser.parse_args()
    report = inspect(Path(__file__).resolve().parents[2], args.require_upstream)
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
