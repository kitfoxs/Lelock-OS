"""Lelock OS HTTP Bridge Server.
Exposes a lightweight, loopback-bound REST API for SillyTavern and other client integrations.
"""
from __future__ import annotations
import http.server
import json
import socketserver
from pathlib import Path
import threading
from typing import Any

from .common import LelockError, canonical, display
from .config import Config
from .service import Service, make_record
from .cards import stage, activate
from .companions import seed_companion_lore


class LelockBridgeHandler(http.server.BaseHTTPRequestHandler):
    service: Service

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy standard HTTP access logs in terminal
        pass

    def _send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def _read_body_json(self) -> dict:
        length = int(self.headers.get('Content-Length', 0))
        if length <= 0:
            return {}
        if length > 2 * 1024 * 1024:  # 2MB max payload
            raise LelockError('Payload too large.')
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode('utf-8'))
        except (ValueError, UnicodeDecodeError) as exc:
            raise LelockError('Invalid JSON body.') from exc

    def do_GET(self) -> None:
        path = self.path.split('?')[0].rstrip('/')
        try:
            if path in {'', '/status', '/api/status'}:
                cfg = self.service.config
                props = self.service.journal.proposals()
                self._send_json(200, {
                    'ok': True,
                    'companion': cfg.companion_name,
                    'workspace': cfg.workspace,
                    'scope': self.service.scope,
                    'home': str(self.service.home),
                    'profile_id': cfg.profile_id,
                    'pending_proposals_count': len(props),
                    'palace_wing': self.service.wing,
                })
            elif path in {'/api/proposals/pending', '/proposals/pending'}:
                props = self.service.journal.proposals()
                formatted = []
                for p in props:
                    item = dict(p)
                    try:
                        item['payload'] = json.loads(item['payload'])
                    except Exception:
                        pass
                    formatted.append(item)
                self._send_json(200, {
                    'ok': True,
                    'proposals': formatted,
                })
            elif path == '/api/memory-list':
                refs = self.service.journal.refs(self.service.scope)
                self._send_json(200, {
                    'ok': True,
                    'scope': self.service.scope,
                    'memories': refs,
                })
            else:
                self._send_json(404, {'ok': False, 'error': f'Not found: {path}'})
        except Exception as exc:
            self._send_json(500, {'ok': False, 'error': str(exc)})

    def do_POST(self) -> None:
        path = self.path.split('?')[0].rstrip('/')
        try:
            body = self._read_body_json()
            if path in {'/api/recall', '/recall'}:
                query = body.get('query', '')
                limit = int(body.get('limit', 5))
                result = self.service.recall(query, limit=limit)
                self._send_json(200, {
                    'ok': True,
                    'memories': result.get('memories', []),
                    'status': result.get('status', 'no_evidence'),
                    'scope': result.get('scope', self.service.scope),
                })
            elif path in {'/api/remember', '/remember'}:
                content = body.get('content', '')
                kind = body.get('kind', 'fact')
                source = body.get('source', 'sillytavern-operator')
                record = make_record(content, kind=kind, scope=self.service.scope, source=source)
                drawer_id = self.service.store(record)
                self._send_json(200, {
                    'ok': True,
                    'record_id': record['id'],
                    'drawer_id': drawer_id,
                    'kind': kind,
                    'scope': self.service.scope,
                })
            elif path in {'/api/read-file', '/read-file'}:
                rel_path = body.get('path', '')
                result = self.service.workspace.read(rel_path)
                self._send_json(200, {
                    'ok': True,
                    'file': result,
                })
            elif path in {'/api/proposals/create', '/proposals/create'}:
                action = body.get('action', 'write')
                if action == 'write':
                    rel_path = body.get('path', '')
                    content = body.get('content', '')
                    prop = self.service.write_proposal(rel_path, content)
                    self._send_json(200, {'ok': True, 'proposal': prop})
                elif action == 'memory':
                    content = body.get('content', '')
                    kind = body.get('kind', 'fact')
                    prop = self.service.memory_proposal(content, kind=kind)
                    self._send_json(200, {'ok': True, 'proposal': prop})
                else:
                    self._send_json(400, {'ok': False, 'error': f'Unknown action: {action}'})
            elif path in {'/api/proposals/approve', '/proposals/approve'}:
                prop_id = body.get('id', '')
                if not prop_id:
                    raise LelockError('Proposal ID is required.')
                res = self.service.approve(prop_id)
                self._send_json(200, {'ok': True, 'result': res})
            elif path in {'/api/proposals/reject', '/proposals/reject'}:
                prop_id = body.get('id', '')
                if not prop_id:
                    raise LelockError('Proposal ID is required.')
                res = self.service.reject(prop_id)
                self._send_json(200, {'ok': True, 'result': res})
            elif path in {'/api/sync-card', '/sync-card'}:
                card_data = body.get('card')
                seed_lore = bool(body.get('seed_lore', True))
                if not card_data or not isinstance(card_data, dict):
                    raise LelockError('Card object is required.')
                # Stage and activate card directly into current home
                staged = stage(self.service.home, card_data)
                activated = activate(self.service.home, staged['id'])
                lore_count = 0
                lore_topics = []
                if seed_lore:
                    # Look for embedded character_book
                    char_book = card_data.get('data', {}).get('character_book') or card_data.get('character_book')
                    if char_book and isinstance(char_book, dict):
                        entries = char_book.get('entries', [])
                        for ent in entries:
                            if not isinstance(ent, dict):
                                continue
                            content = ent.get('content', '')
                            comment = ent.get('comment', '') or ent.get('name', '')
                            keys = ent.get('keys', [])
                            if not content.strip():
                                continue
                            lore_content = f"LORE ({comment}): {content.strip()}"
                            if keys:
                                lore_content += f"\nKEYWORDS: {', '.join(str(k) for k in keys)}"
                            rec = make_record(lore_content, kind='fact', scope=self.service.scope, source='character-book-sync')
                            self.service.store(rec)
                            lore_count += 1
                            lore_topics.append(comment or 'lore-entry')
                self._send_json(200, {
                    'ok': True,
                    'companion': activated['name'],
                    'lore_seeded_count': lore_count,
                    'lore_topics': lore_topics,
                })
            else:
                self._send_json(404, {'ok': False, 'error': f'Not found: {path}'})
        except LelockError as exc:
            self._send_json(400, {'ok': False, 'error': str(exc)})
        except Exception as exc:
            self._send_json(500, {'ok': False, 'error': str(exc)})


class LelockBridgeServer:
    def __init__(self, service: Service, host: str = '127.0.0.1', port: int = 8780):
        self.service = service
        self.host = host
        self.port = port
        self.server: http.server.ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self, blocking: bool = True) -> None:
        raise LelockError(
            "Legacy unauthenticated bridge is quarantined. Use python -m lelock_entity serve "
            "with an explicit owned profile and migrate the client to the v1 authenticated API."
        )
        handler = type('ConfiguredLelockBridgeHandler', (LelockBridgeHandler,), {'service': self.service})
        self.server = http.server.ThreadingHTTPServer((self.host, self.port), handler)
        if blocking:
            self.server.serve_forever()
        else:
            self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self._thread.start()

    def shutdown(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self._thread:
                self._thread.join(timeout=2.0)
