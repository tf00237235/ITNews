"""依關鍵字字典為每筆條目打標籤、並算出重要性權重。"""

from __future__ import annotations

import re

from .config import FALLBACK_TAG, TAG_RULES

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


def classify(item: dict) -> dict:
    """為 item 加上 tags / priority；priority 越大越優先。"""
    haystack = " ".join([
        item.get("title", ""),
        item.get("summary", ""),
    ]).lower()

    tags: list[str] = []
    priority = 0

    for tag, (keywords, weight) in TAG_RULES.items():
        if tag == "#CVE":
            # CVE 有專屬 regex，比 keyword 嚴謹
            if CVE_RE.search(haystack):
                tags.append(tag)
                priority = max(priority, weight)
            continue
        for kw in keywords:
            if kw.lower() in haystack:
                tags.append(tag)
                priority = max(priority, weight)
                break

    # NVD 來源一定帶 #CVE 與 #漏洞
    if item.get("source") == "NVD":
        if "#CVE" not in tags:
            tags.append("#CVE")
        if "#漏洞" not in tags:
            tags.append("#漏洞")
        # CVSS 高分往上加權
        cvss = item.get("cvss") or 0
        if cvss >= 9.0:
            priority = max(priority, 95)
        elif cvss >= 7.0:
            priority = max(priority, 75)

    if not tags:
        tags = [FALLBACK_TAG]
        priority = 10

    item["tags"] = tags
    item["priority"] = priority
    return item


def classify_all(items: list[dict]) -> list[dict]:
    return [classify(it) for it in items]


def sort_and_limit(items: list[dict], max_items: int) -> list[dict]:
    """先依 priority 降冪，再依 published 新到舊，最後截前 max_items 條。"""
    def sort_key(it: dict):
        published = it.get("published")
        ts = published.timestamp() if published else 0
        return (-it.get("priority", 0), -ts)

    return sorted(items, key=sort_key)[:max_items]
