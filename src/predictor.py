"""Composite outlook engine.

Blends price action, credible-news sentiment, and sector rotation into a
directional outlook for the coming 1-3 weeks, expressed in three conviction
tiers:

  WOULD  - all signals aligned, decent news coverage: highest conviction
  COULD  - majority of signals agree: moderate conviction
  MIGHT  - weak or conflicting evidence: speculative watch-list only

This is statistical inference on public data, not financial advice.
"""
from __future__ import annotations

WEIGHTS = {"technical": 0.45, "news": 0.35, "sector": 0.20}


def predict(tech: dict, news: dict, sector_score: float) -> dict:
    t = tech["score"]
    n = news["score"]
    s = sector_score

    # If there is no qualifying news, redistribute its weight to price action.
    if news["count"] == 0:
        composite = (t * (WEIGHTS["technical"] + WEIGHTS["news"])
                     + s * WEIGHTS["sector"])
    else:
        composite = t * WEIGHTS["technical"] + n * WEIGHTS["news"] + s * WEIGHTS["sector"]

    if composite > 0.12:
        direction = "Bullish"
    elif composite < -0.12:
        direction = "Bearish"
    else:
        direction = "Neutral"

    signs = [x for x in (t, n if news["count"] else None, s) if x is not None]
    aligned = sum(1 for x in signs if (x > 0) == (composite > 0) and abs(x) > 0.05)

    if abs(composite) >= 0.40 and aligned >= len(signs) and news["count"] >= 3:
        tier = "WOULD"
    elif abs(composite) >= 0.20 and aligned >= 2:
        tier = "COULD"
    else:
        tier = "MIGHT"

    reasons = []
    if abs(t) > 0.15:
        reasons.append(f"price action is {'constructive' if t > 0 else 'deteriorating'} "
                       f"(technical score {t:+.2f})")
    if news["count"]:
        mood = "positive" if n > 0.1 else "negative" if n < -0.1 else "mixed"
        reasons.append(f"{news['count']} credible headlines skew {mood} ({n:+.2f})")
    else:
        reasons.append("no recent coverage from trusted publishers")
    if abs(s) > 0.15:
        reasons.append(f"its sector is {'leading' if s > 0 else 'lagging'} the S&P 500")

    rsi = tech.get("rsi")
    if rsi is not None and rsi > 75:
        reasons.append(f"RSI {rsi:.0f} is overbought — pullback risk even in an uptrend")
    elif rsi is not None and rsi < 30:
        reasons.append(f"RSI {rsi:.0f} is oversold — bounce potential")

    return {
        "composite": round(composite, 3),
        "direction": direction,
        "tier": tier,
        "reasons": reasons,
    }


def tier_sentence(ticker: str, pred: dict) -> str:
    d = pred["direction"].lower()
    move = {"bullish": "move higher", "bearish": "move lower",
            "neutral": "trade sideways"}[d]
    verb = {"WOULD": "would likely", "COULD": "could", "MIGHT": "might"}[pred["tier"]]
    return f"{ticker} {verb} {move} over the coming week(s)."
