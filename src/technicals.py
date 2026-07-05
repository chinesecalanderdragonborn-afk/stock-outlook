"""Price-action analysis: momentum, trend, and mean-reversion indicators."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _rsi(close: pd.Series, window: int = 14) -> float | None:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    if loss.iloc[-1] == 0:
        return 100.0
    rs = gain.iloc[-1] / loss.iloc[-1]
    val = 100 - 100 / (1 + rs)
    return None if np.isnan(val) else float(val)


def analyze(df: pd.DataFrame) -> dict | None:
    """Compute indicators and a composite technical score in [-1, 1]."""
    if df is None or len(df) < 60:
        return None
    close = df["Close"].dropna()
    if len(close) < 60:
        return None
    last = float(close.iloc[-1])

    def ret(days: int) -> float | None:
        if len(close) <= days:
            return None
        return float(last / close.iloc[-1 - days] - 1)

    sma20 = float(close.rolling(20).mean().iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None

    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    macd_hist = float((macd - signal).iloc[-1])
    macd_hist_prev = float((macd - signal).iloc[-6]) if len(close) > 6 else macd_hist

    rsi = _rsi(close)
    vol_30d = float(close.pct_change().tail(30).std() * np.sqrt(252))
    hi_52w = float(close.tail(252).max())
    lo_52w = float(close.tail(252).min())
    pos_52w = (last - lo_52w) / (hi_52w - lo_52w) if hi_52w > lo_52w else 0.5

    vol_ratio = None
    if "Volume" in df and df["Volume"].notna().sum() > 60:
        v = df["Volume"].dropna()
        base = float(v.tail(63).mean())
        if base > 0:
            vol_ratio = float(v.tail(10).mean() / base)

    r5, r21, r63 = ret(5), ret(21), ret(63)

    # --- ascending-volume signal in [-1, 1] ---
    # Expanding volume *with* the price trend = accumulation (confirms the move);
    # expanding volume against it, or a rally on drying-up volume = distribution
    # or fading conviction. Blended with 21-day up-day vs down-day volume balance.
    vol_score = None
    if vol_ratio is not None and r21 is not None:
        v = df["Volume"].dropna().tail(21)
        chg = close.pct_change().reindex(v.index)
        up_vol = float(v[chg > 0].sum())
        down_vol = float(v[chg < 0].sum())
        total = up_vol + down_vol
        updown = (up_vol - down_vol) / total if total > 0 else 0.0
        expansion = float(np.clip((vol_ratio - 1) / 0.4, -1, 1))
        trend_dir = 1.0 if r21 > 0 else -1.0
        confirm = trend_dir * expansion
        vol_score = float(np.clip(0.5 * confirm + 0.5 * updown, -1, 1))

    # --- scoring: each component in [-1, 1], then weighted ---
    parts: list[tuple[float, float]] = []  # (score, weight)
    if r21 is not None:
        parts.append((float(np.clip(r21 / 0.10, -1, 1)), 0.30))
    if r63 is not None:
        parts.append((float(np.clip(r63 / 0.20, -1, 1)), 0.15))
    trend = 0.0
    trend += 0.5 if last > sma50 else -0.5
    if sma200 is not None:
        trend += 0.5 if last > sma200 else -0.5
    parts.append((trend, 0.25))
    parts.append((float(np.clip(macd_hist - macd_hist_prev, -1, 1))
                  if abs(macd_hist) > 1e-9 else 0.0, 0.10))
    if rsi is not None:
        if rsi > 75:
            parts.append((-0.6, 0.20))   # overbought — near-term pullback risk
        elif rsi < 30:
            parts.append((0.4, 0.20))    # oversold — bounce candidate
        elif rsi > 55:
            parts.append((0.3, 0.20))
        elif rsi < 45:
            parts.append((-0.3, 0.20))
        else:
            parts.append((0.0, 0.20))

    total_w = sum(w for _, w in parts)
    score = sum(s * w for s, w in parts) / total_w if total_w else 0.0

    return {
        "score": float(np.clip(score, -1, 1)),
        "last": last, "ret_1w": r5, "ret_1m": r21, "ret_3m": r63,
        "sma20": sma20, "sma50": sma50, "sma200": sma200,
        "rsi": rsi, "macd_hist": macd_hist, "volatility": vol_30d,
        "pos_52w": pos_52w, "vol_ratio": vol_ratio, "vol_score": vol_score,
    }
