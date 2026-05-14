"""Discord webhook 推播：每筆做成 embed。"""

from __future__ import annotations

import logging
import time

import requests

logger = logging.getLogger(__name__)

# tag 對應到 embed 顏色（decimal）；命中第一個 tag 就用它的色
TAG_COLOR = {
    "#零日": 0xE74C3C,        # 紅
    "#勒索軟體": 0xC0392B,
    "#APT": 0x8E44AD,         # 紫
    "#資料外洩": 0xE67E22,    # 橘
    "#供應鏈": 0xD35400,
    "#CVE": 0xE91E63,         # 粉紅
    "#漏洞": 0xF1C40F,        # 黃
    "#補丁": 0x3498DB,        # 藍
    "#惡意軟體": 0x95A5A6,
    "#釣魚": 0x16A085,
    "#雲端": 0x2980B9,
    "#Web": 0x1ABC9C,
    "#行動裝置": 0x9B59B6,
    "#工具": 0x27AE60,
    "#資安": 0x7F8C8D,
}
DEFAULT_COLOR = 0x607D8B


def _color_for(tags: list[str]) -> int:
    for tag in tags:
        if tag in TAG_COLOR:
            return TAG_COLOR[tag]
    return DEFAULT_COLOR


def _embed(item: dict) -> dict:
    tags = item.get("tags", [])
    description = item.get("summary") or ""
    if len(description) > 350:
        description = description[:347] + "..."
    if tags:
        description = (description + "\n\n" if description else "") + " ".join(tags)

    embed = {
        "title": item["title"][:256],
        "url": item["link"],
        "description": description[:4096],
        "color": _color_for(tags),
        "footer": {"text": item.get("source", "")},
    }
    published = item.get("published")
    if published:
        embed["timestamp"] = published.isoformat()
    return embed


def send(webhook_url: str, items: list[dict], dry_run: bool = False) -> int:
    """一次最多 10 個 embed（Discord 限制），分批送出；回傳成功筆數。"""
    if not items:
        return 0
    if not webhook_url and not dry_run:
        logger.warning("DISCORD_WEBHOOK_URL not set; skipping Discord")
        return 0

    success = 0
    batch_size = 10
    for i in range(0, len(items), batch_size):
        chunk = items[i : i + batch_size]
        payload = {
            "username": "ITNews Bot",
            "embeds": [_embed(it) for it in chunk],
        }
        if dry_run:
            logger.info("[DRY_RUN] Discord would send %d embeds", len(chunk))
            success += len(chunk)
            continue

        try:
            resp = requests.post(webhook_url, json=payload, timeout=15)
            if resp.status_code == 429:
                retry = float(resp.headers.get("Retry-After", "2"))
                logger.warning("Discord rate-limited; sleeping %.1fs", retry)
                time.sleep(retry + 0.5)
                resp = requests.post(webhook_url, json=payload, timeout=15)
            resp.raise_for_status()
            success += len(chunk)
            time.sleep(1)  # 簡單節流，避免 webhook 撞 rate limit
        except requests.RequestException as exc:
            logger.error("Discord send failed for batch starting at %d: %s", i, exc)

    return success
