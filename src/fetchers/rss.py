"""通用 RSS 抓取器：把每筆條目正規化成統一 dict 結構。"""

from __future__ import annotations

import html
import logging
import re
from datetime import datetime, timezone
from typing import Iterable

import feedparser
from dateutil import parser as dateparser

logger = logging.getLogger(__name__)

USER_AGENT = "ITNewsBot/1.0 (+https://github.com/)"

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str | None) -> str:
    if not text:
        return ""
    cleaned = _TAG_RE.sub("", text)
    return html.unescape(cleaned).strip()


def _parse_published(entry) -> datetime | None:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if not value:
            continue
        try:
            dt = dateparser.parse(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def fetch(source: dict, lookback_hours: int) -> list[dict]:
    """抓單一 RSS source；只回傳 lookback_hours 內的條目。"""
    url = source["url"]
    name = source["name"]
    lang = source.get("lang", "en")

    try:
        parsed = feedparser.parse(url, agent=USER_AGENT)
    except Exception as exc:  # noqa: BLE001 - feedparser 任何錯都當失敗
        logger.warning("RSS fetch failed for %s: %s", name, exc)
        return []

    if parsed.bozo and not parsed.entries:
        logger.warning("RSS parse failed for %s: %s", name, parsed.bozo_exception)
        return []

    cutoff = datetime.now(timezone.utc).timestamp() - lookback_hours * 3600
    items: list[dict] = []

    for entry in parsed.entries:
        link = entry.get("link")
        title = _strip_html(entry.get("title"))
        if not link or not title:
            continue

        published = _parse_published(entry)
        if published and published.timestamp() < cutoff:
            continue

        summary = _strip_html(entry.get("summary") or entry.get("description"))
        items.append({
            "title": title,
            "link": link,
            "summary": summary[:400],
            "source": name,
            "lang": lang,
            "published": published,
        })

    logger.info("RSS %s -> %d items in lookback window", name, len(items))
    return items


def fetch_all(sources: Iterable[dict], lookback_hours: int) -> list[dict]:
    aggregated: list[dict] = []
    for src in sources:
        aggregated.extend(fetch(src, lookback_hours))
    return aggregated
