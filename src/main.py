"""每日資安新聞推播：抓 RSS + NVD → 去重 → 分類 → 推 Discord / Telegram。"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from . import classifier, dedup
from .config import NVD_MIN_CVSS, RSS_SOURCES
from .fetchers import nvd, rss
from .notifiers import discord, telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("itnews")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid int for %s=%r; using default %d", name, raw, default)
        return default


def run() -> int:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    dry_run = os.getenv("DRY_RUN", "0") == "1"
    max_items = _env_int("MAX_ITEMS", 20)
    lookback_hours = _env_int("LOOKBACK_HOURS", 36)

    logger.info(
        "Starting run | dry_run=%s max_items=%d lookback_hours=%d",
        dry_run, max_items, lookback_hours,
    )

    # 1. 抓
    items = rss.fetch_all(RSS_SOURCES, lookback_hours)
    items.extend(nvd.fetch(lookback_hours, NVD_MIN_CVSS))
    logger.info("Fetched %d raw items", len(items))

    # 2. 去重
    state = dedup.prune(dedup.load())
    new_items = dedup.filter_new(items, state)
    logger.info("After dedup: %d new items", len(new_items))

    if not new_items:
        logger.info("Nothing new to push; exiting cleanly")
        dedup.save(state)
        return 0

    # 3. 分類 + 排序 + 取前 N 條
    classifier.classify_all(new_items)
    top = classifier.sort_and_limit(new_items, max_items)
    logger.info("Selected top %d items after classification", len(top))

    # 4. 推
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL", "")
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_chat = os.getenv("TELEGRAM_CHAT_ID", "")

    discord_sent = discord.send(discord_webhook, top, dry_run=dry_run)
    telegram_sent = telegram.send(tg_token, tg_chat, top, dry_run=dry_run)
    logger.info("Pushed: discord=%d telegram=%d", discord_sent, telegram_sent)

    # 5. 寫回 seen.json：只有真的推出去才標記，
    #    避免某次推播全失敗、下次就再也不重試；dry_run 不寫，方便重複測試
    if not dry_run and (discord_sent or telegram_sent):
        dedup.mark_seen(top, state)
        dedup.save(state)

    return 0


if __name__ == "__main__":
    sys.exit(run())
