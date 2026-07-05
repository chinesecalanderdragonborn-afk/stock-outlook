"""Market data access layer built on yfinance (Yahoo Finance).

Yahoo aggregates licensed feeds from Reuters, Bloomberg, AP, CNBC, Barron's,
MarketWatch and other institutional publishers, which is what the news module
filters for downstream.
"""
from __future__ import annotations

import pandas as pd
import yfinance as yf


def fetch_history(tickers: list[str], period: str = "1y") -> dict[str, pd.DataFrame]:
    """Batch-download daily OHLCV history. Returns {ticker: DataFrame}."""
    raw = yf.download(
        tickers=" ".join(tickers),
        period=period,
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    out: dict[str, pd.DataFrame] = {}
    if raw is None or raw.empty:
        return out
    if isinstance(raw.columns, pd.MultiIndex):
        for t in tickers:
            if t in raw.columns.get_level_values(0):
                df = raw[t].dropna(how="all")
                if not df.empty:
                    out[t] = df
    else:  # single ticker
        out[tickers[0]] = raw.dropna(how="all")
    return out


def fetch_profile(ticker: str) -> dict:
    """Fundamental profile for one ticker (market cap, sector, valuation)."""
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        info = {}
    return {
        "ticker": ticker,
        "name": info.get("shortName") or ticker,
        "sector": info.get("sector") or "Unknown",
        "industry": info.get("industry") or "Unknown",
        "market_cap": info.get("marketCap"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "price_to_book": info.get("priceToBook"),
        "revenue_growth": info.get("revenueGrowth"),          # fraction, e.g. 0.15
        "earnings_growth": info.get("earningsGrowth")
                           or info.get("earningsQuarterlyGrowth"),
        "dividend_yield": info.get("dividendYield"),           # percent in recent yfinance
        "beta": info.get("beta"),
        "profit_margin": info.get("profitMargins"),
    }


def fetch_raw_news(ticker: str, count: int = 15) -> list[dict]:
    """Raw news items for a ticker; normalized to a flat dict per item."""
    try:
        items = yf.Ticker(ticker).news or []
    except Exception:
        items = []
    normalized = []
    for it in items[:count]:
        # yfinance >= 0.2.50 nests everything under 'content'
        c = it.get("content", it)
        provider = c.get("provider") or {}
        url = (c.get("canonicalUrl") or {}).get("url") or c.get("link") or ""
        normalized.append({
            "title": c.get("title") or "",
            "summary": c.get("summary") or c.get("description") or "",
            "publisher": provider.get("displayName") or it.get("publisher") or "",
            "published": c.get("pubDate") or it.get("providerPublishTime") or "",
            "url": url,
        })
    return normalized
