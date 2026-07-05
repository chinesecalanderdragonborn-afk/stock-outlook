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
PRESS_WIRES = {"business wire", "pr newswire", "globenewswire", "accesswire"}

_vader = SentimentIntensityAnalyzer()


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

    for item in raw_items:
        pub = (item.get("publisher") or "").strip().lower()
        is_trusted = pub in TRUSTED_PUBLISHERS
        is_wire = pub in PRESS_WIRES
        if not (is_trusted or is_wire):
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
