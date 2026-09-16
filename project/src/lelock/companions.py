"""Preloaded companions catalog, staging, activation, and lorebook seeding.
Bundles rich character cards and world lore for instant default companion setup.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

from .common import LelockError, read_json
from .cards import stage, activate

RESOURCE_DIR = Path(__file__).resolve().parents[2] / 'resources' / 'companions'
CATALOG_PATH = RESOURCE_DIR / 'catalog.json'

_CATALOG_CACHE: dict[str, Any] | None = None


def get_catalog() -> dict[str, Any]:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is None:
        if not CATALOG_PATH.is_file():
            raise LelockError('Preloaded companions catalog is not found.')
        _CATALOG_CACHE = read_json(CATALOG_PATH, max_bytes=200_000)
    return _CATALOG_CACHE


def list_companions(collection: str | None = None) -> list[dict[str, Any]]:
    catalog = get_catalog()
    companions = catalog.get('companions', [])
    if collection:
        col = collection.strip().lower()
        companions = [c for c in companions if c.get('collection') == col]
    return companions


def find_companion(query: str) -> dict[str, Any]:
    q = query.strip().lower().replace('-', '_').replace(' ', '_')
    companions = list_companions()

    # 1. Exact ID match
    for c in companions:
        if c['id'] == q:
            return c

    # 2. Exact Name match (case-insensitive)
    for c in companions:
        if c['name'].lower() == query.strip().lower():
            return c

    # 3. Substring match
    matches = [c for c in companions if q in c['id'] or query.strip().lower() in c['name'].lower()]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        names = ', '.join(m['name'] for m in matches)
        raise LelockError(f"Ambiguous companion query '{query}'. Matches: {names}")

    raise LelockError(f"Preloaded companion '{query}' not found. Run 'lelock companions' to view available companions.")


def get_companion_card_path(comp: dict[str, Any]) -> Path:
    p = RESOURCE_DIR / comp['card_path']
    if not p.is_file():
        raise LelockError(f"Card file missing for companion '{comp['name']}'.")
    return p


def get_companion_world_info_path(comp: dict[str, Any]) -> Path | None:
    wi = comp.get('world_info_path')
    if not wi:
        return None
    p = RESOURCE_DIR / wi
    return p if p.is_file() else None


def stage_companion(home: Path, query: str) -> dict[str, Any]:
    comp = find_companion(query)
    card_path = get_companion_card_path(comp)
    staged = stage(home, card_path)
    staged['companion_id'] = comp['id']
    staged['collection'] = comp['collection']
    return staged


def activate_companion(home: Path, query: str) -> dict[str, Any]:
    comp = find_companion(query)
    staged = stage_companion(home, query)
    result = activate(home, staged['id'])
    result['companion_id'] = comp['id']
    result['collection'] = comp['collection']
    result['short_description'] = comp['short_description']
    return result


def seed_companion_lore(service: Any, comp: dict[str, Any]) -> dict[str, Any]:
    from .service import make_record
    wi_path = get_companion_world_info_path(comp)
    if not wi_path:
        return {'seeded_entries': 0, 'topics': []}

    try:
        data = json.loads(wi_path.read_text('utf-8'))
    except Exception as exc:
        raise LelockError(f"Failed to read lorebook for {comp['name']}: {exc}") from exc

    entries = data.get('entries', {})
    topics = []
    kind = 'fiction' if service.scope == 'fiction' else 'fact'

    for entry in entries.values():
        if entry.get('disable'):
            continue
        comment = entry.get('comment', '').strip()
        content = entry.get('content', '').strip()
        if not content:
            continue
        text_content = f"[{comp['name']} Lore — {comment}] {content}" if comment else f"[{comp['name']} Lore] {content}"
        rec = make_record(text_content, kind=kind)
        service.store(rec)
        if comment:
            topics.append(comment)

    return {'seeded_entries': len(topics), 'topics': topics}
