"""Composite outlook engine.

Blends four signals — price action, credible-news sentiment, ascending-volume
confirmation, and sector rotation — into a directional outlook for the coming
1-3 weeks, expressed in three conviction tiers:

  WOULD  - every available signal aligned, decent news coverage: highest conviction
  COULD  - majority of signals agree: moderate conviction
  MIGHT  - weak or conflicting evidence: speculative watch-list only

This is statistical inference on public data, not financial advice.
"""
from __future__ import annotations

WEIGHTS = {"technical": 0.35, "news": 0.30, "volume": 0.20, "sector": 0.15}


def predict(tech: dict, news: dict, sector_score: float) -> dict:
    t = tech["score"]
    n = news["score"]
    v = tech.get("vol_score")
    s = sector_score

    # Only weight signals we actually have; missing ones (no qualifying news,
    # no volume data) redistribute their weight across the rest.
    comps = {"technical": t, "sector": s}
    if news["count"]:
        comps["news"] = n
    if v is not None:
        comps["volume"] = v
    weight_sum = sum(WEIGHTS[k] for k in comps)
    composite = sum(comps[k] * WEIGHTS[k] for k in comps) / weight_sum

    if composite > 0.12:
        direction = "Bullish"
    elif composite < -0.12:
        direction = "Bearish"
    else:
        direction = "Neutral"

    values = list(comps.values())
    aligned = sum(1 for x in values if (x > 0) == (composite > 0) and abs(x) > 0.05)

    if abs(composite) >= 0.40 and aligned == len(values) and news["count"] >= 3:
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

    if v is not None and abs(v) > 0.2:
        vr = tech.get("vol_ratio")
        vr_txt = f" (recent volume {vr:.1f}× the 3-month average)" if vr else ""
        if v > 0:
            reasons.append(f"ascending volume is confirming the move{vr_txt} "
                           "— accumulation")
        else:
            reasons.append(f"volume pattern warns of distribution or fading "
                           f"conviction{vr_txt}")

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
