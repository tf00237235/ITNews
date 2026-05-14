"""NVD CVE 2.0 API：抓 lookback 期間內、CVSS >= 門檻的高風險 CVE。"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import requests

logger = logging.getLogger(__name__)

API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
USER_AGENT = "ITNewsBot/1.0 (+https://github.com/)"


def _format(dt: datetime) -> str:
    # NVD 要求 ISO-8601，毫秒精度
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000")


def _pick_cvss(metrics: dict) -> tuple[float | None, str | None]:
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key) or []
        if not entries:
            continue
        cvss = entries[0].get("cvssData", {})
        score = cvss.get("baseScore")
        severity = cvss.get("baseSeverity") or entries[0].get("baseSeverity")
        if score is not None:
            return float(score), severity
    return None, None


def fetch(lookback_hours: int, min_cvss: float) -> list[dict]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=lookback_hours)
    # 用 pubStartDate 只抓真的新公布的 CVE，避免 NVD 對舊 CVE 做敘述修訂時被當作「新」推播
    params = {
        "pubStartDate": _format(start),
        "pubEndDate": _format(now),
        "resultsPerPage": 100,
    }
    try:
        resp = requests.get(
            API_URL,
            params=params,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("NVD fetch failed: %s", exc)
        return []

    items: list[dict] = []
    for vuln in payload.get("vulnerabilities", []):
        cve = vuln.get("cve", {})
        cve_id = cve.get("id")
        if not cve_id:
            continue

        score, severity = _pick_cvss(cve.get("metrics", {}))
        if score is None or score < min_cvss:
            continue

        descriptions = cve.get("descriptions", []) or []
        desc_en = next((d["value"] for d in descriptions if d.get("lang") == "en"), "")

        published_raw = cve.get("published") or cve.get("lastModified")
        published = None
        if published_raw:
            try:
                published = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
            except ValueError:
                published = None

        items.append({
            "title": f"[{cve_id}] CVSS {score} ({severity or 'N/A'})",
            "link": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            "summary": desc_en[:400],
            "source": "NVD",
            "lang": "en",
            "published": published,
            "cve_id": cve_id,
            "cvss": score,
        })

    logger.info("NVD -> %d high-severity CVEs in lookback window", len(items))
    return items
