# Weekly Stock Outlook

A dashboard that studies **previous news, price action, and sector rotation** to
produce directional leans ("might / could / would") for the coming 1–3 weeks.

## How it works

Three signals are computed per stock and blended into a composite score:

| Signal | Weight | What it measures |
|---|---|---|
| Price action | 45% | 1M/3M momentum, trend vs SMA 50/200, MACD, RSI (over/oversold) |
| Credible news | 35% | VADER sentiment on headlines from **trusted publishers only** (Reuters, Bloomberg, AP, CNBC, WSJ, Barron's, MarketWatch, FT…), recency-weighted with a 5-day half-life. Blog spam and stock-promo sites are discarded. Press-release wires count at half weight. |
| Sector rotation | 20% | The stock's sector ETF (XLK, XLF, …) 1-month return relative to SPY |

If a stock has no qualifying news, the news weight shifts to price action rather
than counting silence as neutral sentiment.

### Finviz integration

- **📡 Scanner tab** — live Finviz signal screens (Top Gainers, Unusual Volume,
  Oversold, New Highs, Insider Buying…) across the whole market, filterable by
  cap tier and sector.
- **📰 Market News tab** — Finviz's aggregated market-wide feed, filtered to
  trusted publishers by default, each headline sentiment-scored.
- **Stock Detail news** — per-stock Finviz headlines merged (and deduplicated)
  with the Yahoo feed, so coverage runs much deeper. The composite *score*
  still uses the Yahoo feed only, keeping the batch analysis fast.

### Conviction tiers

- 🟢 **WOULD** — composite ≥ |0.40|, *all* signals aligned, ≥3 credible headlines
- 🟡 **COULD** — composite ≥ |0.20|, majority of signals agree
- ⚪ **MIGHT** — weak or conflicting evidence; watch-list only

### Classification

- **Market cap:** Mega (≥$200B) · Large ($10–200B) · Mid ($2–10B) · Small ($300M–2B) · Micro (<$300M)
- **Investor style:** Growth / Value / Blend / Speculative, from P/E, forward P/E,
  P/B, revenue & earnings growth, and dividend yield — plus tags such as
  Dividend/Income, Defensive, and High Beta.

## Run it

```powershell
cd C:\Users\14783\stock-outlook
.venv\Scripts\streamlit run app.py
```

First load analyzes ~60 stocks and takes a couple of minutes; results are cached
for an hour. Add your own tickers in the sidebar.

## Data source

All data comes from Yahoo Finance via `yfinance` — prices, fundamentals, and its
licensed news feed (which syndicates Reuters, Bloomberg, AP, CNBC, and others).
No API key required.

## Disclaimer

**Not financial advice.** This tool performs statistical inference on public
data. Even the highest-conviction "WOULD" tier is a probability lean, not a
certainty — markets are moved by news that has not happened yet.
