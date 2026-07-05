"""End-to-end analysis pipeline: fetch -> classify -> score -> predict."""
from __future__ import annotations

from . import classify, news, predictor, technicals
from .data import fetch_history, fetch_profile, fetch_raw_news


def analyze_universe(tickers: list[str], sector_scores: dict[str, dict],
                     progress_cb=None) -> list[dict]:
    """Run the full pipeline. Returns one result dict per analyzable ticker."""
    tickers = list(dict.fromkeys(t.strip().upper() for t in tickers if t.strip()))
    history = fetch_history(tickers, period="1y")

    results = []
    for i, t in enumerate(tickers):
        if progress_cb:
            progress_cb(i / max(len(tickers), 1), t)

        tech = technicals.analyze(history.get(t))
        if tech is None:  # not enough price data — skip
            continue

        profile = fetch_profile(t)
        news_result = news.analyze(fetch_raw_news(t))
        sector = profile["sector"]
        sector_info = sector_scores.get(sector, {})
        pred = predictor.predict(tech, news_result, sector_info.get("score", 0.0))

        style, tags = classify.style_class(profile)
        results.append({
            "ticker": t,
            "profile": profile,
            "cap_class": classify.cap_class(profile["market_cap"]),
            "style": style,
            "style_tags": tags,
            "tech": tech,
            "news": news_result,
            "sector_info": sector_info,
            "prediction": pred,
            "headline": predictor.tier_sentence(t, pred),
            "history": history.get(t),
        })

    if progress_cb:
        progress_cb(1.0, "done")
    results.sort(key=lambda r: r["prediction"]["composite"], reverse=True)
    return results
