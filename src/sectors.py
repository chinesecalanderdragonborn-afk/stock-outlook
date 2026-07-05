"""Sector rotation analysis via SPDR sector ETFs relative to SPY."""
from __future__ import annotations

import numpy as np

from .data import fetch_history
from .universe import BENCHMARK, SECTOR_ETFS


def sector_strength() -> dict[str, dict]:
    """1-month relative strength of each sector vs the S&P 500.

    Returns {sector_name: {'etf', 'ret_1m', 'rel_1m', 'score'}}.
    Score is in [-1, 1]: positive = sector leading the market.
    """
    etfs = list(SECTOR_ETFS.values()) + [BENCHMARK]
    hist = fetch_history(etfs, period="6mo")

    def ret_1m(t: str) -> float | None:
        df = hist.get(t)
        if df is None or len(df) < 22:
            return None
        close = df["Close"].dropna()
        return float(close.iloc[-1] / close.iloc[-22] - 1)

    spy = ret_1m(BENCHMARK) or 0.0
    out = {}
    for sector, etf in SECTOR_ETFS.items():
        r = ret_1m(etf)
        if r is None:
            out[sector] = {"etf": etf, "ret_1m": None, "rel_1m": None, "score": 0.0}
            continue
        rel = r - spy
        out[sector] = {
            "etf": etf, "ret_1m": r, "rel_1m": rel,
            "score": float(np.clip(rel / 0.05, -1, 1)),
        }
    return out
