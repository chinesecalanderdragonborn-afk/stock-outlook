"""Weekly Stock Outlook — news, price action, volume, and sector analysis.

Run with:  streamlit run app.py
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from src import charts, finviz_data, live, pipeline, sectors
from src import news as news_mod
from src.charts import CHART_CONFIG
from src.classify import CAP_ORDER
from src.universe import CORE_UNIVERSE

st.set_page_config(page_title="Weekly Stock Outlook", page_icon="📈", layout="wide")

# ---------------------------------------------------------------- theme system
DARK_UI = {
    "bg": "#0A0E17", "glow1": "rgba(0,255,135,0.07)", "glow2": "rgba(34,211,238,0.06)",
    "panel": "rgba(15,22,38,0.85)", "side": "rgba(13,18,32,0.92)",
    "text": "#E6EDF3", "muted": "#8B95A9", "line": "rgba(230,237,243,0.08)",
    "green": "#00FF87", "red": "#FF2E55", "cyan": "#22D3EE", "amber": "#FFC24B",
    "green_soft": "rgba(0,255,135,0.12)", "green_border": "rgba(0,255,135,0.4)",
    "red_soft": "rgba(255,46,85,0.10)", "red_border": "rgba(255,46,85,0.35)",
    "amber_soft": "rgba(255,194,75,0.12)", "amber_border": "rgba(255,194,75,0.4)",
    "cyan_soft": "rgba(34,211,238,0.10)", "cyan_border": "rgba(34,211,238,0.3)",
    "chip": "rgba(255,255,255,0.05)", "chip_border": "rgba(230,237,243,0.12)",
    "chipbar": "rgba(255,255,255,0.035)", "track": "rgba(255,255,255,0.06)",
    "midline": "rgba(230,237,243,0.25)", "neutral_text": "#B9C2D4",
    "shadow": "none",
    "tab_sel": "linear-gradient(135deg, rgba(0,255,135,0.16), rgba(34,211,238,0.10))",
}

LIGHT_UI = {
    "bg": "#F4F7FB", "glow1": "rgba(0,158,96,0.08)", "glow2": "rgba(14,116,144,0.07)",
    "panel": "#FFFFFF", "side": "#FDFEFF",
    "text": "#0E1726", "muted": "#5B6B84", "line": "rgba(14,23,38,0.10)",
    "green": "#009E60", "red": "#E11D48", "cyan": "#0E7490", "amber": "#B45309",
    "green_soft": "rgba(0,158,96,0.10)", "green_border": "rgba(0,158,96,0.45)",
    "red_soft": "rgba(225,29,72,0.08)", "red_border": "rgba(225,29,72,0.4)",
    "amber_soft": "rgba(180,83,9,0.10)", "amber_border": "rgba(180,83,9,0.4)",
    "cyan_soft": "rgba(14,116,144,0.08)", "cyan_border": "rgba(14,116,144,0.35)",
    "chip": "rgba(14,23,38,0.045)", "chip_border": "rgba(14,23,38,0.12)",
    "chipbar": "rgba(14,23,38,0.04)", "track": "rgba(14,23,38,0.07)",
    "midline": "rgba(14,23,38,0.3)", "neutral_text": "#42526B",
    "shadow": "0 1px 2px rgba(16,24,40,0.06), 0 2px 8px rgba(16,24,40,0.08)",
    "tab_sel": "linear-gradient(135deg, rgba(0,158,96,0.14), rgba(14,116,144,0.10))",
}


def apply_native_theme(light: bool) -> None:
    """Retint Streamlit's built-in widgets (dataframes, dropdowns, toggles)."""
    try:
        from streamlit import config as _cfg
        vals = ({"theme.base": "light", "theme.primaryColor": "#009E60",
                 "theme.backgroundColor": "#F4F7FB",
                 "theme.secondaryBackgroundColor": "#FFFFFF",
                 "theme.textColor": "#0E1726"} if light else
                {"theme.base": "dark", "theme.primaryColor": "#00FF87",
                 "theme.backgroundColor": "#0A0E17",
                 "theme.secondaryBackgroundColor": "#111827",
                 "theme.textColor": "#E6EDF3"})
        for key, val in vals.items():
            _cfg.set_option(key, val)
    except Exception:
        pass  # native widgets keep the default theme; custom CSS still applies


IS_LIGHT = bool(st.session_state.get("light_mode", False))
apply_native_theme(IS_LIGHT)
UI = LIGHT_UI if IS_LIGHT else DARK_UI
CHART_PAL = charts.LIGHT_CHART if IS_LIGHT else charts.DARK_CHART

_root = ":root {" + "".join(
    f"--{k.replace('_', '-')}: {v};" for k, v in UI.items()) + "}"

st.markdown("<style>" + _root + """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, .stApp, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
    background:
        radial-gradient(1100px 700px at 85% -10%, var(--glow1), transparent 60%),
        radial-gradient(900px 600px at -10% 15%, var(--glow2), transparent 60%),
        var(--bg);
    color: var(--text);
}
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.6rem; max-width: 1350px; }

.stApp, .kpi, .news-card, .bucket, div[data-testid="stExpander"],
section[data-testid="stSidebar"] {
    transition: background 0.3s ease, border-color 0.3s ease, color 0.3s ease;
}

section[data-testid="stSidebar"] {
    background: var(--side);
    border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
/* hardening: keep sidebar text readable even if the native theme lags */
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label {
    color: var(--text);
}

/* tabs → segmented pill bar */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px; background: var(--chipbar);
    padding: 6px; border-radius: 14px; border: 1px solid var(--line);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px; padding: 8px 20px; background: transparent;
    color: var(--muted); font-weight: 600; font-size: 0.92rem;
}
.stTabs [aria-selected="true"] {
    background: var(--tab-sel);
    color: var(--green) !important;
    box-shadow: inset 0 0 0 1px var(--green-border);
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* expanders → cards */
div[data-testid="stExpander"] {
    background: var(--panel); border: 1px solid var(--line);
    border-radius: 14px; overflow: hidden; margin-bottom: 4px;
    box-shadow: var(--shadow);
}
div[data-testid="stExpander"] summary { font-weight: 600; }
div[data-testid="stExpander"]:hover { border-color: var(--green-border); }

/* hero */
.hero h1 {
    font-size: 2.5rem; font-weight: 900; letter-spacing: -0.03em;
    margin: 0 0 2px 0; line-height: 1.1; color: var(--text);
}
.hero .grad {
    background: linear-gradient(90deg, var(--green), var(--cyan));
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { color: var(--muted); margin: 4px 0 0 0; font-size: 0.98rem; }

/* pills & chips */
.pill {
    display: inline-block; padding: 4px 14px; border-radius: 999px;
    font-size: 0.74rem; font-weight: 800; letter-spacing: 0.06em;
    text-transform: uppercase; margin-right: 6px; margin-bottom: 4px;
}
.pill-would { background: var(--green-soft); color: var(--green); border: 1px solid var(--green-border); }
.pill-could { background: var(--amber-soft); color: var(--amber); border: 1px solid var(--amber-border); }
.pill-might { background: var(--chip); color: var(--neutral-text); border: 1px solid var(--chip-border); }
.pill-bull  { background: var(--green-soft); color: var(--green); border: 1px solid var(--green-border); }
.pill-bear  { background: var(--red-soft); color: var(--red); border: 1px solid var(--red-border); }
.pill-flat  { background: var(--cyan-soft); color: var(--cyan); border: 1px solid var(--cyan-border); }
.pill-info  { background: var(--chip); color: var(--neutral-text); border: 1px solid var(--chip-border); }

/* KPI cards */
.kpi {
    background: var(--panel); border: 1px solid var(--line);
    border-radius: 16px; padding: 14px 16px; height: 100%; min-width: 0;
    box-shadow: var(--shadow);
}
.kpi * { word-break: keep-all; overflow-wrap: normal; }
.kpi .lab { color: var(--muted); font-size: 0.68rem; font-weight: 700;
            letter-spacing: 0.06em; text-transform: uppercase;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kpi .val { font-size: clamp(1.05rem, 1.5vw, 1.65rem); font-weight: 800;
            font-family: 'JetBrains Mono', monospace; white-space: nowrap;
            margin-top: 2px; line-height: 1.25; color: var(--text); }
.kpi .sub { color: var(--muted); font-size: 0.76rem; margin-top: 2px; }
.kpi.glow-green { border-color: var(--green-border); box-shadow: inset 0 0 24px var(--green-soft); }
.kpi.glow-red   { border-color: var(--red-border);  box-shadow: inset 0 0 24px var(--red-soft); }

/* diverging signal bars */
.sig-row { display: flex; align-items: center; gap: 12px; margin: 7px 0; }
.sig-lab { width: 105px; color: var(--muted); font-size: 0.8rem; font-weight: 600; }
.sig-track { position: relative; flex: 1; height: 10px;
             background: var(--track); border-radius: 6px; }
.sig-track::after { content: ""; position: absolute; left: 50%; top: -3px; bottom: -3px;
                    width: 1px; background: var(--midline); }
.sig-fill { position: absolute; top: 0; bottom: 0; border-radius: 6px; }
.sig-val { width: 52px; text-align: right; font-family: 'JetBrains Mono', monospace;
           font-size: 0.82rem; font-weight: 700; }

/* news cards */
.news-card {
    background: var(--panel); border: 1px solid var(--line);
    border-left: 3px solid var(--tone, var(--muted));
    border-radius: 12px; padding: 13px 16px; margin-bottom: 10px;
    box-shadow: var(--shadow);
}
.news-card a { color: var(--text); font-weight: 600; text-decoration: none; font-size: 0.95rem; }
.news-card a:hover { color: var(--green); }
.news-card .meta { color: var(--muted); font-size: 0.78rem; margin-top: 4px; }

/* bucket cards */
.bucket {
    background: var(--panel); border: 1px solid var(--line);
    border-radius: 16px; padding: 16px 18px; margin-bottom: 14px;
    box-shadow: var(--shadow);
}
.bucket .head { display: flex; justify-content: space-between; align-items: baseline; }
.bucket .name { font-weight: 800; font-size: 1.02rem; color: var(--text); }
.bucket .tally { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; }
.bucket .members { color: var(--muted); font-size: 0.84rem; margin-top: 8px; line-height: 1.7; }
.bucket .members b.up { color: var(--green); font-weight: 700; }
.bucket .members b.dn { color: var(--red); font-weight: 700; }

/* live futures strip */
.tickrow { display: flex; gap: 10px; flex-wrap: wrap; }
.tick {
    flex: 1; min-width: 118px; background: var(--panel);
    border: 1px solid var(--line); border-radius: 12px;
    padding: 8px 12px; box-shadow: var(--shadow);
}
.tick .tlab { color: var(--muted); font-size: 0.68rem; font-weight: 700;
              letter-spacing: 0.05em; text-transform: uppercase; white-space: nowrap; }
.tick .tval { font-family: 'JetBrains Mono', monospace; font-weight: 700;
              font-size: 0.95rem; color: var(--text); white-space: nowrap; }
.tick .tchg { font-family: 'JetBrains Mono', monospace; font-weight: 700;
              font-size: 0.78rem; white-space: nowrap; }

h1, h2, h3, h4, h5 { letter-spacing: -0.02em; color: var(--text); }
div[data-testid="stMetric"] {
    background: var(--panel); border: 1px solid var(--line);
    border-radius: 16px; padding: 14px 18px; box-shadow: var(--shadow);
}
</style>""", unsafe_allow_html=True)

TIER_PILL = {"WOULD": "<span class='pill pill-would'>Would</span>",
             "COULD": "<span class='pill pill-could'>Could</span>",
             "MIGHT": "<span class='pill pill-might'>Might</span>"}
DIR_PILL = {"Bullish": "<span class='pill pill-bull'>▲ Bullish</span>",
            "Bearish": "<span class='pill pill-bear'>▼ Bearish</span>",
            "Neutral": "<span class='pill pill-flat'>► Neutral</span>"}
TIER_HELP = {"WOULD": "signals aligned · high conviction",
             "COULD": "majority of signals agree",
             "MIGHT": "speculative · weak evidence"}


# ---------------------------------------------------------------- cached data
@st.cache_data(ttl=3600, show_spinner=False)
def load_sector_scores():
    return sectors.sector_strength()


@st.cache_data(ttl=3600, show_spinner=False, max_entries=2)
def load_results(tickers: tuple[str, ...]):
    return pipeline.analyze_universe(list(tickers), load_sector_scores())


@st.cache_data(ttl=900, show_spinner=False)
def load_screen(signal: str, cap_label: str, sector: str):
    df = finviz_data.run_screen(signal, cap_label, sector)
    if df is None:
        raise ConnectionError("Finviz unreachable")  # raise so failures aren't cached
    return df


@st.cache_data(ttl=600, show_spinner=False)
def load_market_news():
    feed = finviz_data.market_news()
    if feed is None:
        raise ConnectionError("Finviz unreachable")
    return feed


@st.cache_data(ttl=900, show_spinner=False)
def load_stock_news(ticker: str):
    return news_mod.analyze(finviz_data.stock_news(ticker))


@st.cache_data(ttl=55, show_spinner=False)
def load_futures_quotes():
    return live.futures_quotes()


@st.cache_data(ttl=25, show_spinner=False, max_entries=16)
def load_live_quote(ticker: str):
    return live.live_quote(ticker)


@st.cache_data(ttl=60, show_spinner=False, max_entries=16)
def load_intraday(ticker: str, key: str):
    return live.intraday(ticker, key)


def fmt_cap(v):
    if not v:
        return "—"
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6)):
        if v >= div:
            return f"${v / div:,.1f}{unit}"
    return f"${v:,.0f}"


def kpi(col, label, value, sub="", glow=""):
    col.markdown(f"<div class='kpi {glow}'><div class='lab'>{label}</div>"
                 f"<div class='val'>{value}</div><div class='sub'>{sub}</div></div>",
                 unsafe_allow_html=True)


def signal_bars(pairs: list[tuple[str, float]]) -> str:
    rows = []
    for label, v in pairs:
        v = max(-1.0, min(1.0, v))
        color = "var(--green)" if v >= 0 else "var(--red)"
        if v >= 0:
            fill = f"left:50%; width:{v * 50:.1f}%; background:{color};"
        else:
            fill = f"right:50%; width:{-v * 50:.1f}%; background:{color};"
        rows.append(
            f"<div class='sig-row'><div class='sig-lab'>{label}</div>"
            f"<div class='sig-track'><div class='sig-fill' style='{fill}'></div></div>"
            f"<div class='sig-val' style='color:{color}'>{v:+.2f}</div></div>")
    return "".join(rows)


# ---------------------------------------------------------------- sidebar
st.sidebar.markdown("## 📈 Weekly Stock Outlook")
st.sidebar.toggle("☀️ Light mode", key="light_mode",
                  help="Switch between night and day themes")
st.sidebar.caption(
    "Signals from **price action**, **credible news** (Reuters, Bloomberg, AP, "
    "CNBC, WSJ, Barron's, MarketWatch…), **ascending volume**, and "
    "**sector rotation**."
)

extra = st.sidebar.text_input("Add tickers (comma-separated)", "",
                              placeholder="e.g. ORCL, SHOP")
tickers = CORE_UNIVERSE + [t.strip().upper() for t in extra.split(",") if t.strip()]

if st.sidebar.button("🔄 Refresh data (clears cache)", width="stretch"):
    st.cache_data.clear()

with st.spinner("Analyzing universe — first load takes a couple of minutes..."):
    results = load_results(tuple(tickers))
    sector_scores = load_sector_scores()

st.sidebar.markdown("#### Filters")
cap_filter = st.sidebar.multiselect("Market cap", CAP_ORDER, default=[])
style_filter = st.sidebar.multiselect("Investor style",
                                      sorted({r["style"] for r in results}), default=[])
sector_filter = st.sidebar.multiselect("Sector",
                                       sorted({r["profile"]["sector"] for r in results}),
                                       default=[])
tier_filter = st.sidebar.multiselect("Conviction tier", ["WOULD", "COULD", "MIGHT"],
                                     default=[])

filtered = [
    r for r in results
    if (not cap_filter or r["cap_class"] in cap_filter)
    and (not style_filter or r["style"] in style_filter)
    and (not sector_filter or r["profile"]["sector"] in sector_filter)
    and (not tier_filter or r["prediction"]["tier"] in tier_filter)
]

st.sidebar.markdown("---")
st.sidebar.warning(
    "**Not financial advice.** These are statistical readings of public data. "
    "Treat every tier, including WOULD, as a probability lean — never a certainty."
)

# ---------------------------------------------------------------- hero + KPIs
bulls = [r for r in filtered if r["prediction"]["direction"] == "Bullish"]
bears = [r for r in filtered if r["prediction"]["direction"] == "Bearish"]
high_conv = [r for r in filtered if r["prediction"]["tier"] == "WOULD"]
covered = [r for r in filtered if r["news"]["count"] > 0]
avg_tone = (sum(r["news"]["score"] for r in covered) / len(covered)) if covered else 0.0

today = datetime.now().strftime("%A, %B %d, %Y")
st.markdown(
    "<div class='hero'><h1>Weekly <span class='grad'>Stock Outlook</span></h1>"
    f"<p>{today} · directional leans for the coming 1–3 weeks · price action + "
    "credible news + volume + sector rotation · showing "
    f"{len(filtered)} of {len(results)} stocks</p></div>",
    unsafe_allow_html=True)
st.write("")

k1, k2, k3, k4 = st.columns(4)
kpi(k1, "Bullish leans", f"▲ {len(bulls)}",
    f"{sum(1 for r in bulls if r['prediction']['tier'] == 'WOULD')} high conviction",
    "glow-green")
kpi(k2, "Bearish leans", f"▼ {len(bears)}",
    f"{sum(1 for r in bears if r['prediction']['tier'] == 'WOULD')} high conviction",
    "glow-red")
kpi(k3, "Conviction", f"{len(high_conv)}", "stocks with all signals aligned")
kpi(k4, "News tone", f"{avg_tone:+.2f}", f"{len(covered)} stocks with trusted coverage")
st.write("")


@st.fragment(run_every=90)
def live_futures_strip():
    try:
        quotes = load_futures_quotes()
    except Exception:
        quotes = []
    if not quotes:
        st.caption("live futures quotes unavailable right now")
        return
    chips = []
    for q in quotes:
        color = "var(--green)" if q["chg_pct"] >= 0 else "var(--red)"
        arrow = "▲" if q["chg_pct"] >= 0 else "▼"
        price = f"{q['last']:,.2f}"
        chips.append(
            f"<div class='tick'><div class='tlab'>{q['label']}</div>"
            f"<div class='tval'>{price}</div>"
            f"<div class='tchg' style='color:{color}'>{arrow} "
            f"{q['chg_pct']:+.2f}%</div></div>")
    st.markdown(f"<div class='tickrow'>{''.join(chips)}</div>",
                unsafe_allow_html=True)
    st.caption(f"⚡ live — futures trade nearly 24h · auto-updates every 90s · "
               f"last update {datetime.now().strftime('%H:%M:%S')}")


live_futures_strip()
st.write("")

tab_outlook, tab_scanner, tab_sectors, tab_news, tab_buckets, tab_detail = st.tabs(
    ["🎯 Outlook", "📡 Scanner", "🏭 Sectors", "📰 Market News",
     "🗂️ Cap & Style", "🔍 Stock Detail"])

# ---------------------------------------------------------------- outlook tab
with tab_outlook:
    col_bull, col_bear = st.columns(2)

    def outlook_block(col, title, subset, empty_msg):
        with col:
            st.subheader(title)
            if not subset:
                st.caption(empty_msg)
            for tier in ("WOULD", "COULD", "MIGHT"):
                group = [r for r in subset if r["prediction"]["tier"] == tier]
                if not group:
                    continue
                st.markdown(f"{TIER_PILL[tier]} <span style='color:var(--muted);"
                            f"font-size:0.85rem'>{TIER_HELP[tier]}</span>",
                            unsafe_allow_html=True)
                for r in group:
                    p = r["prediction"]
                    with st.expander(f"{r['ticker']} · {r['profile']['name']} · "
                                     f"{p['composite']:+.2f}"):
                        st.markdown(f"*{r['headline']}*")
                        st.markdown("\n".join(f"- {reason}" for reason in p["reasons"]))
                        st.markdown(
                            f"<span class='pill pill-info'>{r['cap_class']} cap</span>"
                            f"<span class='pill pill-info'>{r['style']}</span>"
                            f"<span class='pill pill-info'>{r['profile']['sector']}</span>",
                            unsafe_allow_html=True)

    outlook_block(col_bull, "▲ Bullish", bulls, "No bullish leans under current filters.")
    outlook_block(col_bear, "▼ Bearish", bears, "No bearish leans under current filters.")

    neutral = [r for r in filtered if r["prediction"]["direction"] == "Neutral"]
    if neutral:
        st.markdown("##### ► Neutral / range-bound")
        st.caption(", ".join(r["ticker"] for r in neutral))

    st.markdown("### Full ranking")
    table = pd.DataFrame([{
        "Ticker": r["ticker"],
        "Name": r["profile"]["name"],
        "Outlook": r["prediction"]["direction"],
        "Tier": r["prediction"]["tier"],
        "Score": r["prediction"]["composite"],
        "Cap": r["cap_class"],
        "Style": r["style"],
        "Sector": r["profile"]["sector"],
        "1W %": None if r["tech"]["ret_1w"] is None else round(r["tech"]["ret_1w"] * 100, 1),
        "1M %": None if r["tech"]["ret_1m"] is None else round(r["tech"]["ret_1m"] * 100, 1),
        "RSI": None if r["tech"]["rsi"] is None else round(r["tech"]["rsi"]),
        "Vol trend": None if r["tech"]["vol_ratio"] is None
                     else round(r["tech"]["vol_ratio"], 2),
        "News #": r["news"]["count"],
        "Tone": round(r["news"]["score"], 2),
        "Mkt cap": fmt_cap(r["profile"]["market_cap"]),
    } for r in filtered])
    st.dataframe(
        table, width="stretch", hide_index=True, height=520,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score", min_value=-1.0, max_value=1.0, format="%+.2f"),
            "1W %": st.column_config.NumberColumn(format="%+.1f%%"),
            "1M %": st.column_config.NumberColumn(format="%+.1f%%"),
            "Vol trend": st.column_config.NumberColumn(
                format="%.2f×", help="10-day avg volume vs 3-month avg"),
            "Tone": st.column_config.NumberColumn(format="%+.2f"),
        })

# ---------------------------------------------------------------- scanner tab
with tab_scanner:
    st.subheader("Finviz market scanner")
    st.caption("Live signal screens across the **entire market** — not just the "
               "analyzed universe. Spot something interesting? Add its ticker in "
               "the sidebar to run the full outlook analysis on it.")
    f1, f2, f3 = st.columns(3)
    scan_signal = f1.selectbox("Signal", finviz_data.SIGNALS)
    scan_cap = f2.selectbox("Market cap", list(finviz_data.CAP_FILTERS))
    scan_sector = f3.selectbox("Sector", finviz_data.SECTOR_FILTERS)

    try:
        with st.spinner("Scanning..."):
            scan_df = load_screen(scan_signal, scan_cap, scan_sector)
    except Exception:
        scan_df = None

    if scan_df is None:
        st.warning("Finviz is unreachable right now (rate limit or site issue). "
                   "Try again in a minute.")
    elif scan_df.empty:
        st.info("No stocks match this scan right now.")
    else:
        view = scan_df.copy()
        view["Market Cap"] = view["Market Cap"].map(fmt_cap)
        if "Change" in view:
            view["Change"] = view["Change"] * 100
        st.dataframe(
            view, width="stretch", hide_index=True, height=560,
            column_config={
                "Change": st.column_config.NumberColumn(format="%+.2f%%"),
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Volume": st.column_config.NumberColumn(format="localized"),
                "P/E": st.column_config.NumberColumn(format="%.1f"),
            })
        st.caption(f"{len(view)} results · signal: {scan_signal} · data: finviz.com")

# ---------------------------------------------------------------- sectors tab
with tab_sectors:
    st.subheader("Sector rotation — 1-month performance vs S&P 500")
    rows = [(name, d["etf"], d["rel_1m"], d["ret_1m"])
            for name, d in sector_scores.items() if d["rel_1m"] is not None]
    rows.sort(key=lambda x: x[2])
    st.plotly_chart(charts.sector_figure(rows, CHART_PAL), width="stretch",
                    config={"displayModeBar": False})
    st.caption("Stocks in leading sectors get a tailwind in the composite score; "
               "lagging sectors a headwind.")

# ---------------------------------------------------------------- market news tab
with tab_news:
    head_l, head_r = st.columns([3, 1])
    head_l.subheader("Market-wide news — Finviz feed")
    trusted_only = head_r.toggle("Trusted publishers only", value=True)

    try:
        with st.spinner("Fetching news feed..."):
            feed = load_market_news()
    except Exception:
        feed = None

    if feed is None:
        st.warning("Finviz news feed is unreachable right now. Try again in a minute.")
    else:
        shown = [i for i in feed
                 if not trusted_only or news_mod.is_trusted(i["publisher"])]
        if not shown:
            st.info("No headlines from trusted publishers in the current feed — "
                    "flip the toggle to see all sources.")
        for item in shown[:40]:
            s = news_mod.sentiment_of(item["title"])
            tone = ("var(--green)" if s > 0.15 else
                    "var(--red)" if s < -0.15 else "var(--muted)")
            badge = "" if news_mod.is_trusted(item["publisher"]) else \
                "<span class='pill pill-info' style='margin-left:8px'>unvetted</span>"
            link = (f"<a href='{item['url']}' target='_blank'>{item['title']}</a>"
                    if item["url"] else item["title"])
            st.markdown(
                f"<div class='news-card' style='--tone:{tone}'>{link}{badge}"
                f"<div class='meta'>{item['publisher']} · {item['when']} · "
                f"tone <span style='color:{tone}'>{s:+.2f}</span></div></div>",
                unsafe_allow_html=True)
        st.caption(f"{min(len(shown), 40)} of {len(feed)} headlines · data: finviz.com")

# ---------------------------------------------------------------- buckets tab
with tab_buckets:
    def bucket_card(name, group):
        b = sum(1 for r in group if r["prediction"]["direction"] == "Bullish")
        s = sum(1 for r in group if r["prediction"]["direction"] == "Bearish")
        members = " · ".join(
            f"<b class='{'up' if r['prediction']['composite'] > 0 else 'dn'}'>"
            f"{r['ticker']}</b> {r['prediction']['composite']:+.2f}"
            for r in group)
        st.markdown(
            f"<div class='bucket'><div class='head'><span class='name'>{name}</span>"
            f"<span class='tally'><span style='color:var(--green)'>▲ {b}</span>"
            f"&nbsp;&nbsp;<span style='color:var(--red)'>▼ {s}</span>"
            f"&nbsp;&nbsp;<span style='color:var(--muted)'>{len(group)} stocks</span>"
            f"</span></div><div class='members'>{members}</div></div>",
            unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.subheader("By market cap")
        for cap in CAP_ORDER:
            group = [r for r in filtered if r["cap_class"] == cap]
            if group:
                bucket_card(f"{cap} cap", group)
    with right:
        st.subheader("By investor style")
        for style in sorted({r["style"] for r in filtered}):
            group = [r for r in filtered if r["style"] == style]
            if group:
                bucket_card(style, group)

# ---------------------------------------------------------------- detail tab
with tab_detail:
    pick = st.selectbox("Stock", [r["ticker"] for r in filtered] or ["—"],
                        label_visibility="collapsed")
    r = next((x for x in filtered if x["ticker"] == pick), None)
    if r:
        p, tech, prof = r["prediction"], r["tech"], r["profile"]
        tags = "".join(f"<span class='pill pill-info'>{t}</span>" for t in r["style_tags"])
        st.markdown(
            f"<h2 style='margin-bottom:2px'>{prof['name']} "
            f"<span style='color:var(--muted);font-weight:600'>({r['ticker']})</span></h2>"
            f"{TIER_PILL[p['tier']]}{DIR_PILL[p['direction']]}"
            f"<span class='pill pill-info'>{r['cap_class']} cap</span>"
            f"<span class='pill pill-info'>{r['style']}</span>"
            f"<span class='pill pill-info'>{prof['sector']}</span>{tags}",
            unsafe_allow_html=True)
        st.markdown(f"*{r['headline']}*")

        c1, c2, c3, c4, c5 = st.columns(5)

        @st.fragment(run_every=45)
        def live_price_kpi(ticker=r["ticker"], fallback=tech["last"]):
            q = load_live_quote(ticker)
            if q is None:
                kpi(st, "Price", f"${fallback:,.2f}", "daily close")
                return
            chg = "" if q["chg_pct"] is None else f"{q['chg_pct']:+.2f}% today · "
            asof = q["asof"].strftime("%H:%M") if q.get("asof") is not None else ""
            kpi(st, "Price · live", f"${q['last']:,.2f}",
                f"{chg}⚡ as of {asof} · incl. pre/post")

        with c1:
            live_price_kpi()
        kpi(c2, "Mkt cap", fmt_cap(prof["market_cap"]), f"{r['cap_class']} cap")
        kpi(c3, "Score", f"{p['composite']:+.2f}", TIER_HELP[p["tier"]])
        kpi(c4, "RSI (14)", "—" if tech["rsi"] is None else f"{tech['rsi']:.0f}",
            "overbought &gt; 70 · oversold &lt; 30")
        kpi(c5, "Volatility", f"{tech['volatility'] * 100:.0f}%", "30-day annualized")
        st.write("")

        col_sig, col_why = st.columns([1, 1])
        with col_sig:
            st.markdown("##### Signal breakdown")
            st.markdown(signal_bars([
                ("Price action", tech["score"]),
                ("News tone", r["news"]["score"]),
                ("Volume", tech.get("vol_score") or 0.0),
                ("Sector", r["sector_info"].get("score", 0.0)),
                ("Composite", p["composite"]),
            ]), unsafe_allow_html=True)
            if r.get("news_enriched"):
                st.caption("news scoring deepened with Finviz headlines")
        with col_why:
            st.markdown("##### Why")
            st.markdown("\n".join(f"- {reason}" for reason in p["reasons"]))

        tf = st.radio("Timeframe", ["⚡ 1D live", "⚡ 5D live", "1Y daily"],
                      horizontal=True, label_visibility="collapsed")

        if tf.startswith("⚡"):
            key = "1D" if "1D" in tf else "5D"

            @st.fragment(run_every=120)
            def live_chart(ticker=r["ticker"], key=key):
                idf = load_intraday(ticker, key)
                if idf is None or idf.empty:
                    st.info("No intraday data available for this ticker right now — "
                            "showing the daily chart instead.")
                    if r["history"] is not None:
                        st.plotly_chart(
                            charts.price_figure(r["history"], ticker, CHART_PAL),
                            width="stretch", config=CHART_CONFIG)
                    return
                st.plotly_chart(charts.intraday_figure(idf, ticker, CHART_PAL),
                                width="stretch", config=CHART_CONFIG)
                st.caption(f"⚡ {key} · {'1-min' if key == '1D' else '5-min'} candles "
                           "incl. pre/post-market · dotted line = VWAP · "
                           "auto-updates every 2 min · "
                           f"last update {datetime.now().strftime('%H:%M:%S')}")

            live_chart()
        elif r["history"] is not None:
            st.plotly_chart(charts.price_figure(r["history"], r["ticker"], CHART_PAL),
                            width="stretch", config=CHART_CONFIG)
            st.caption("🖱️ Scroll to zoom · drag to pan · buttons for 1M–All ranges · "
                       "drag the strip below the volume panel to scrub · "
                       "double-click to reset")

        st.markdown("### Recent credible news")
        with st.spinner("Merging Yahoo + Finviz coverage..."):
            fin_news = load_stock_news(r["ticker"])
        merged = news_mod.dedupe(
            [{"origin": "Yahoo", **i} for i in r["news"]["items"]]
            + [{"origin": "Finviz", **i} for i in fin_news["items"]])
        merged.sort(key=lambda x: x["age_days"])

        if merged:
            for item in merged:
                tone = ("var(--green)" if item["sentiment"] > 0.15
                        else "var(--red)" if item["sentiment"] < -0.15
                        else "var(--muted)")
                src = item["publisher"] + (
                    " · press release" if item["source_type"] == "press release" else "")
                title = item["title"]
                link = f"<a href='{item['url']}' target='_blank'>{title}</a>" \
                    if item["url"] else title
                st.markdown(
                    f"<div class='news-card' style='--tone:{tone}'>{link}"
                    f"<div class='meta'>{src} · {item['age_days']:.0f}d ago · "
                    f"tone <span style='color:{tone}'>{item['sentiment']:+.2f}</span>"
                    f" · via {item['origin']}</div></div>",
                    unsafe_allow_html=True)
        else:
            st.info("No recent coverage from trusted publishers — outlook relies on "
                    "price action, volume, and sector strength only.")

# ---------------------------------------------------------------- theme bounce
# Native widget theming is read when a run *starts*, so a theme change lands
# one run late. Bounce once at the END of the script (after every widget has
# been instantiated, so their state survives the rerun).
if st.session_state.get("_applied_theme", False) != IS_LIGHT:
    st.session_state["_applied_theme"] = IS_LIGHT
    st.rerun()
