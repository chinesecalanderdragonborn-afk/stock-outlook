"""Live-quote layer on Yahoo's consolidated feed (near-real-time; seconds
fresh for US equities and futures, which also trade overnight).

The heavy analysis pipeline stays on its own cadence — this module powers
the auto-refreshing UI fragments: the futures strip, live detail price,
and intraday charts (with pre/post-market data).
"""
from __future__ import annotations

import pandas as pd
import yfinance as yf

FUTURES = [
    ("ES=F", "S&P 500"), ("NQ=F", "Nasdaq 100"), ("YM=F", "Dow"),
    ("RTY=F", "Russell 2K"), ("CL=F", "Crude Oil"), ("GC=F", "Gold"),
    ("^VIX", "VIX"),
]

INTRADAY_SPECS = {"1D": ("1d", "1m"), "5D": ("5d", "5m")}


def futures_quotes() -> list[dict]:
    """Latest price + day change for the futures/index strip."""
    symbols = [s for s, _ in FUTURES]
    # threads=False: repeated threaded downloads in long-running fragments
    # can accumulate and destabilize small cloud containers
    df = yf.download(" ".join(symbols), period="5d", interval="1d",
                     group_by="ticker", auto_adjust=False,
                     progress=False, threads=False)
    out = []
    for sym, label in FUTURES:
        try:
            close = df[sym]["Close"].dropna()
            last, prev = float(close.iloc[-1]), float(close.iloc[-2])
            out.append({"symbol": sym, "label": label, "last": last,
                        "chg_pct": (last / prev - 1) * 100})
        except Exception:
            continue
    return out


def live_quote(ticker: str) -> dict | None:
    """Freshest available price incl. pre/post-market, with day change."""
    try:
        hist = yf.Ticker(ticker).history(period="2d", interval="1m",
                                         prepost=True, auto_adjust=False)
        close = hist["Close"].dropna()
        if close.empty:
            return None
        last = float(close.iloc[-1])
        asof = close.index[-1]
        prev = None
        try:
            prev = float(yf.Ticker(ticker).fast_info["previousClose"])
        except Exception:
            pass
        return {"last": last, "prev_close": prev,
                "chg_pct": None if not prev else (last / prev - 1) * 100,
                "asof": asof}
    except Exception:
        return None


def intraday(ticker: str, key: str) -> pd.DataFrame | None:
    """Intraday OHLCV incl. extended hours. key: '1D' or '5D'."""
    period, interval = INTRADAY_SPECS[key]
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval,
                                       prepost=True, auto_adjust=False)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    return df.dropna(subset=["Close"])
