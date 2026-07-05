"""News analysis restricted to established, credible publishers.

Only headlines from the whitelist below are scored. Blog aggregators,
promotional stock-picking sites, and anonymous sources are dropped.
Company press-release wires are kept but flagged (primary source, but
self-published so inherently one-sided).
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

TRUSTED_PUBLISHERS = {
    "reuters", "bloomberg", "associated press", "ap finance", "cnbc",
    "the wall street journal", "wall street journal", "barron's", "barrons",
    "marketwatch", "financial times", "yahoo finance", "investor's business daily",
    "investopedia", "fortune", "forbes", "the economist", "axios",
    "business insider",
}
# Finviz's market feed reports sources as domains rather than display names
TRUSTED_DOMAINS = {
    "reuters.com", "bloomberg.com", "apnews.com", "cnbc.com", "wsj.com",
    "barrons.com", "marketwatch.com", "ft.com", "finance.yahoo.com",
    "investors.com", "investopedia.com", "fortune.com", "forbes.com",
    "economist.com", "axios.com", "businessinsider.com", "foxbusiness.com",
}
PRESS_WIRES = {"business wire", "pr newswire", "globenewswire", "accesswire"}

_vader = SentimentIntensityAnalyzer()


def is_trusted(publisher: str) -> bool:
    """Accept both display names ('Bloomberg') and domains ('www.bloomberg.com')."""
    pub = (publisher or "").strip().lower()
    if pub in TRUSTED_PUBLISHERS:
        return True
    host = pub.split("/")[0].removeprefix("www.")
    return any(host == d or host.endswith("." + d) for d in TRUSTED_DOMAINS)


def sentiment_of(text: str) -> float:
    return _vader.polarity_scores(text)["compound"]


def dedupe(items: list[dict]) -> list[dict]:
    """Drop items whose normalized title was already seen (multi-feed merges)."""
    seen, out = set(), []
    for item in items:
        key = "".join(ch for ch in item.get("title", "").lower() if ch.isalnum())
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _parse_ts(value) -> datetime | None:
    if not value:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, OSError):
        return None


def analyze(raw_items: list[dict], max_age_days: int = 14) -> dict:
    """Filter to trusted sources, score sentiment, weight by recency.

    Returns {'score': [-1,1], 'count': n, 'items': [...]}.
    """
    now = datetime.now(timezone.utc)
    kept, weighted_sum, weight_total = [], 0.0, 0.0

    for item in dedupe(raw_items):
        pub = (item.get("publisher") or "").strip().lower()
        trusted = is_trusted(pub)
        is_wire = pub in PRESS_WIRES
        if not (trusted or is_wire):
            continue

        ts = _parse_ts(item.get("published"))
        age_days = (now - ts).total_seconds() / 86400 if ts else max_age_days
        if age_days > max_age_days:
            continue

        text = f"{item.get('title', '')}. {item.get('summary', '')}"
        sentiment = _vader.polarity_scores(text)["compound"]

        # recency decay (half-life 5 days); press wires get half weight
        weight = math.pow(0.5, age_days / 5.0) * (0.5 if is_wire else 1.0)
        weighted_sum += sentiment * weight
        weight_total += weight
        kept.append({**item, "sentiment": sentiment, "age_days": round(age_days, 1),
                     "source_type": "press release" if is_wire else "news"})

    kept.sort(key=lambda x: x["age_days"])
    score = weighted_sum / weight_total if weight_total else 0.0
    return {"score": max(-1.0, min(1.0, score)), "count": len(kept), "items": kept}
