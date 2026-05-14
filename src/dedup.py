"""把已推播過的連結雜湊存到 state/seen.json，避免重複洗版。"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_PATH = Path(__file__).resolve().parent.parent / "state" / "seen.json"
RETENTION_DAYS = 30


def _hash(link: str) -> str:
    return hashlib.sha256(link.encode("utf-8")).hexdigest()


def load() -> dict[str, str]:
    if not STATE_PATH.exists():
        return {}
    try:
        with STATE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read seen.json (%s); starting fresh", exc)
        return {}


def save(state: dict[str, str]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


def prune(state: dict[str, str]) -> dict[str, str]:
    cutoff = datetime.now(timezone.utc).timestamp() - RETENTION_DAYS * 86400
    pruned = {}
    for key, iso in state.items():
        try:
            ts = datetime.fromisoformat(iso).timestamp()
        except ValueError:
            continue
        if ts >= cutoff:
            pruned[key] = iso
    return pruned


def filter_new(items: list[dict], state: dict[str, str]) -> list[dict]:
    new_items = []
    for it in items:
        link = it.get("link")
        if not link:
            continue
        key = _hash(link)
        if key in state:
            continue
        new_items.append(it)
    return new_items


def mark_seen(items: list[dict], state: dict[str, str]) -> dict[str, str]:
    now = datetime.now(timezone.utc).isoformat()
    for it in items:
        link = it.get("link")
        if link:
            state[_hash(link)] = now
    return state
