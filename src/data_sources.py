from __future__ import annotations

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape

from .models import SourceItem


DEFAULT_SOURCE_CATALOG = {
    "official": {
        "weight": 0.95,
        "examples": ["SEC EDGAR", "央行/发改委/工信部公告", "上市公司公告", "交易所公告", "政府统计局"],
    },
    "institutional": {
        "weight": 0.85,
        "examples": ["基金公司观点", "投行公开会议", "卖方研报摘要", "投资者日/业绩会纪要"],
    },
    "news": {
        "weight": 0.75,
        "examples": ["Reuters", "Bloomberg", "CNBC", "财新", "证券时报", "第一财经"],
    },
    "expert_social": {
        "weight": 0.55,
        "examples": ["X/Twitter", "YouTube", "微信公众号", "微博", "小红书", "播客访谈"],
    },
    "mass_social": {
        "weight": 0.35,
        "examples": ["抖音", "Facebook", "Reddit", "百度贴吧", "雪球评论区"],
    },
}


def clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_google_news_rss(query: str, region: str = "global", limit: int = 12) -> list[SourceItem]:
    """Fetch Google News RSS results without requiring an API key.

    This connector is intentionally conservative. For production, replace it with
    paid/compliant APIs such as Serper, GDELT, AlphaSense, Factiva, or official feeds.
    """

    hl = "zh-CN" if region.lower() in {"cn", "china", "hk", "hong kong"} else "en-US"
    gl = "CN" if hl == "zh-CN" else "US"
    ceid = f"{gl}:{hl}"
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={ceid}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
    except Exception:
        return []

    items: list[SourceItem] = []
    for item in root.findall(".//item")[:limit]:
        title = clean_html(item.findtext("title", default=""))
        link = item.findtext("link", default="")
        summary = clean_html(item.findtext("description", default=""))
        published = item.findtext("pubDate", default="")
        source = item.findtext("source", default="Google News")
        items.append(
            SourceItem(
                title=title,
                url=link,
                source=source or "Google News",
                summary=summary,
                published=published,
                credibility=0.72,
            )
        )
    return items


def source_plan_for_topic(topic: str) -> dict[str, list[str]]:
    topic_lower = topic.lower()
    plan = {
        "must_have": ["official", "news"],
        "should_have": ["institutional"],
        "optional": ["expert_social"],
        "avoid_as_primary": ["mass_social"],
    }
    if any(k in topic_lower for k in ["semiconductor", "chip", "ai", "nvidia", "英伟达", "半导体", "算力"]):
        plan["must_have"].extend(["institutional"])
        plan["should_have"].extend(["expert_social"])
    if any(k in topic_lower for k in ["policy", "macro", "宏观", "政策"]):
        plan["must_have"].append("official")
    return plan
