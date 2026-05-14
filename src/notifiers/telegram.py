"""Telegram Bot API 推播：每筆一則 HTML 訊息。"""

from __future__ import annotations

import html
import logging
import time

import requests

logger = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _format(item: dict) -> str:
    title = html.escape(item.get("title", ""))
    link = item.get("link", "")
    source = html.escape(item.get("source", ""))
    tags = " ".join(item.get("tags", []))
    summary = html.escape(item.get("summary") or "")
    if len(summary) > 300:
        summary = summary[:297] + "..."

    lines = [
        f"<b>[{source}]</b> <a href=\"{link}\">{title}</a>",
    ]
    if summary:
        lines.append(summary)
    if tags:
        lines.append(tags)
    return "\n\n".join(lines)


def send(token: str, chat_id: str, items: list[dict], dry_run: bool = False) -> int:
    if not items:
        return 0
    if (not token or not chat_id) and not dry_run:
        logger.warning("Telegram token / chat_id 未設定；跳過 Telegram")
        return 0

    url = API_URL.format(token=token) if token else ""
    success = 0
    for it in items:
        text = _format(it)
        if dry_run:
            logger.info("[DRY_RUN] Telegram would send:\n%s\n", text)
            success += 1
            continue

        try:
            resp = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            if resp.status_code == 429:
                retry = float(resp.json().get("parameters", {}).get("retry_after", 2))
                logger.warning("Telegram rate-limited; sleeping %.1fs", retry)
                time.sleep(retry + 0.5)
                resp = requests.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    },
                    timeout=15,
                )
            resp.raise_for_status()
            success += 1
            time.sleep(0.5)
        except requests.RequestException as exc:
            logger.error("Telegram send failed: %s", exc)

    return success
