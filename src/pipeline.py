"""End-to-end analysis pipeline: fetch -> classify -> score -> predict.

Two passes: every ticker is scored on Yahoo news first, then the stocks with
the strongest provisional signals get their news deepened with Finviz
headlines and are re-scored. This keeps the batch fast (Finviz is scraped,
one request per ticker) while the names that matter most get the fullest
news picture.
"""
from __future__ import annotations

from . import classify, finviz_data, news, predictor, technicals
from .data import fetch_history, fetch_profile, fetch_raw_news

ENRICH_TOP = 12  # strongest-signal stocks that get Finviz-deepened news


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
        raw = [{**item, "origin": "Yahoo"} for item in fetch_raw_news(t)]
        news_result = news.analyze(raw)
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
            "news_enriched": False,
            "_raw_news": raw,
        })

    # second pass: deepen news for the strongest provisional signals
    results.sort(key=lambda r: abs(r["prediction"]["composite"]), reverse=True)
    for r in results[:ENRICH_TOP]:
        if progress_cb:
            progress_cb(1.0, f"enriching {r['ticker']}")
        fin_raw = [{**item, "origin": "Finviz"}
                   for item in finviz_data.stock_news(r["ticker"])]
        if not fin_raw:
            continue
        merged = news.analyze(r["_raw_news"] + fin_raw)
        r["news"] = merged
        r["news_enriched"] = True
        r["prediction"] = predictor.predict(
            r["tech"], merged, r["sector_info"].get("score", 0.0))
        r["headline"] = predictor.tier_sentence(r["ticker"], r["prediction"])

    for r in results:
        r.pop("_raw_news", None)

    if progress_cb:
        progress_cb(1.0, "done")
    results.sort(key=lambda r: r["prediction"]["composite"], reverse=True)
    return results
