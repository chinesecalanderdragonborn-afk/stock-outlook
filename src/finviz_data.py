"""Finviz integration: signal screener, market-wide news, per-stock news.

Finviz has no official API — this uses the finvizfinance scraper package.
Every function degrades gracefully (None / empty list) if Finviz is
unreachable or rate-limits us, so the rest of the app keeps working.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def _clean(text) -> str:
    """Collapse whitespace and drop mojibake replacement chars from Finviz."""
    return " ".join(str(text).replace("�", "").split())
from finvizfinance import util as _fv_util
from finvizfinance.news import News as _FinvizNews
from finvizfinance.quote import finvizfinance as _FinvizQuote
from finvizfinance.screener.overview import Overview as _Overview

# finvizfinance ships a 2020-era User-Agent and bare headers, which Finviz's
# bot detection rejects from datacenter IPs (e.g. Streamlit Cloud). Patch in a
# realistic modern browser fingerprint; the dict is read at request time.
_fv_util.headers.update({
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0.0.0 Safari/537.36"),
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
               "image/avif,image/webp,*/*;q=0.8"),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://finviz.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
})

# Curated subset of Finviz screener signals, most useful first
SIGNALS = [
    "Top Gainers", "Top Losers", "Most Active", "Most Volatile",
    "Unusual Volume", "Oversold", "Overbought", "New High", "New Low",
    "Upgrades", "Downgrades", "Recent Insider Buying",
    "Recent Insider Selling", "Major News", "Channel Up", "Channel Down",
]

CAP_FILTERS = {
    "Any": None,
    "Mega (≥$200B)": "Mega ($200bln and more)",
    "Large ($10B–$200B)": "Large ($10bln to $200bln)",
    "Mid ($2B–$10B)": "Mid ($2bln to $10bln)",
    "Small ($300M–$2B)": "Small ($300mln to $2bln)",
    "Micro ($50M–$300M)": "Micro ($50mln to $300mln)",
}

SECTOR_FILTERS = [
    "Any", "Basic Materials", "Communication Services", "Consumer Cyclical",
    "Consumer Defensive", "Energy", "Financial", "Healthcare", "Industrials",
    "Real Estate", "Technology", "Utilities",
]


def run_screen(signal: str, cap_label: str = "Any", sector: str = "Any",
               limit: int = 40) -> pd.DataFrame | None:
    """Run a Finviz screener signal with optional cap/sector filters."""
    try:
        screen = _Overview()
        filters = {}
        if CAP_FILTERS.get(cap_label):
            filters["Market Cap."] = CAP_FILTERS[cap_label]
        if sector and sector != "Any":
            filters["Sector"] = sector
        screen.set_filter(signal=signal, filters_dict=filters)
        df = screen.screener_view(limit=limit, verbose=0)
        if df is None or df.empty:
            return pd.DataFrame()
        return df.reset_index(drop=True)
    except Exception:
        return None  # Finviz unreachable / rate-limited / layout changed


def market_news() -> list[dict] | None:
    """Finviz market-wide news feed, normalized. None if unreachable."""
    try:
        feed = _FinvizNews().get_news()
    except Exception:
        return None
    items = []
    df = feed.get("news")
    if df is None:
        return []
    for _, row in df.iterrows():
        items.append({
            "title": _clean(row.get("Title", "")),
            "publisher": str(row.get("Source", "")).strip(),
            "when": str(row.get("Date", "")).strip(),
            "url": str(row.get("Link", "")).strip(),
        })
    return items


def stock_news(ticker: str) -> list[dict]:
    """Per-stock Finviz headlines, normalized to the same shape the
    news analyzer accepts (title/summary/publisher/published/url)."""
    try:
        df = _FinvizQuote(ticker).ticker_news()
    except Exception:
        return []
    if df is None or df.empty:
        return []
    items = []
    for _, row in df.iterrows():
        ts = row.get("Date")
        published = ""
        if isinstance(ts, (datetime, pd.Timestamp)):
            published = pd.Timestamp(ts).tz_localize(timezone.utc).isoformat() \
                if pd.Timestamp(ts).tzinfo is None else pd.Timestamp(ts).isoformat()
        items.append({
            "title": _clean(row.get("Title", "")),
            "summary": "",
            "publisher": str(row.get("Source", "")).strip(),
            "published": published,
            "url": str(row.get("Link", "")).strip(),
        })
    return items
