"""Plotly chart builders — theme-aware (night / day palettes).

All figures share: transparent backgrounds, high-contrast candles, unified
crosshair hover, scroll-zoom + pan, and weekend gaps removed.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CHART_CONFIG = {
    "scrollZoom": True,
    "displaylogo": False,
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
    "doubleClick": "reset",
}

DARK_CHART = {
    "up": "#00FF87", "down": "#FF2E55",
    "up_fill": "rgba(0,255,135,0.85)", "down_fill": "rgba(255,46,85,0.85)",
    "up_vol": "rgba(0,255,135,0.45)", "down_vol": "rgba(255,46,85,0.45)",
    "sma_fast": "#22D3EE", "sma_slow": "#FFC24B",
    "text": "#E6EDF3", "muted": "#8B95A9",
    "grid": "rgba(230,237,243,0.07)",
    "tooltip_bg": "#0F1626", "tooltip_border": "rgba(0,255,135,0.4)",
    "spike": "rgba(0,255,135,0.5)", "spike_y": "rgba(0,255,135,0.35)",
    "btn_bg": "rgba(255,255,255,0.05)", "btn_active": "rgba(0,255,135,0.25)",
    "btn_border": "rgba(255,255,255,0.12)",
    "slider_bg": "rgba(255,255,255,0.04)", "slider_border": "rgba(255,255,255,0.1)",
    "zero": "rgba(230,237,243,0.35)",
}

LIGHT_CHART = {
    "up": "#009E60", "down": "#E11D48",
    "up_fill": "rgba(0,158,96,0.9)", "down_fill": "rgba(225,29,72,0.9)",
    "up_vol": "rgba(0,158,96,0.35)", "down_vol": "rgba(225,29,72,0.35)",
    "sma_fast": "#0E7490", "sma_slow": "#B45309",
    "text": "#0E1726", "muted": "#5B6B84",
    "grid": "rgba(14,23,38,0.08)",
    "tooltip_bg": "#FFFFFF", "tooltip_border": "rgba(0,158,96,0.5)",
    "spike": "rgba(0,158,96,0.55)", "spike_y": "rgba(0,158,96,0.4)",
    "btn_bg": "rgba(14,23,38,0.05)", "btn_active": "rgba(0,158,96,0.2)",
    "btn_border": "rgba(14,23,38,0.15)",
    "slider_bg": "rgba(14,23,38,0.04)", "slider_border": "rgba(14,23,38,0.12)",
    "zero": "rgba(14,23,38,0.35)",
}


def _base_layout(fig: go.Figure, height: int, p: dict) -> None:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=p["text"], size=12),
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=p["tooltip_bg"], bordercolor=p["tooltip_border"],
                        font=dict(color=p["text"], size=13,
                                  family="Inter, sans-serif")),
        dragmode="pan",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=12, color=p["muted"])),
    )
    fig.update_xaxes(gridcolor=p["grid"], zeroline=False, linecolor=p["grid"],
                     showspikes=True, spikecolor=p["spike"],
                     spikethickness=1, spikedash="dot", spikemode="across",
                     tickfont=dict(color=p["muted"]))
    fig.update_yaxes(gridcolor=p["grid"], zeroline=False, linecolor=p["grid"],
                     showspikes=True, spikecolor=p["spike_y"],
                     spikethickness=1, spikedash="dot",
                     tickfont=dict(color=p["muted"]))


def price_figure(hist: pd.DataFrame, ticker: str, p: dict = DARK_CHART) -> go.Figure:
    """Candlestick + volume panel with themed up/down coloring and range tools."""
    df = hist.dropna(subset=["Open", "High", "Low", "Close"])
    close = df["Close"]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.78, 0.22], vertical_spacing=0.04)

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name=ticker,
        increasing=dict(line=dict(color=p["up"], width=1.1),
                        fillcolor=p["up_fill"]),
        decreasing=dict(line=dict(color=p["down"], width=1.1),
                        fillcolor=p["down_fill"]),
        whiskerwidth=0.6,
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=close.rolling(50).mean(), name="SMA 50",
        line=dict(color=p["sma_fast"], width=1.4),
        hovertemplate="SMA50 $%{y:,.2f}<extra></extra>",
    ), row=1, col=1)
    if len(close) >= 200:
        fig.add_trace(go.Scatter(
            x=df.index, y=close.rolling(200).mean(), name="SMA 200",
            line=dict(color=p["sma_slow"], width=1.4, dash="dot"),
            hovertemplate="SMA200 $%{y:,.2f}<extra></extra>",
        ), row=1, col=1)

    if "Volume" in df:
        vol_colors = [p["up_vol"] if c >= o else p["down_vol"]
                      for o, c in zip(df["Open"], df["Close"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"], name="Volume",
            marker=dict(color=vol_colors, line_width=0),
            hovertemplate="Vol %{y:,.0f}<extra></extra>",
        ), row=2, col=1)

    _base_layout(fig, height=560, p=p)

    fig.update_xaxes(
        row=1, col=1,
        rangeslider=dict(visible=False),
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(step="all", label="All"),
            ],
            bgcolor=p["btn_bg"], activecolor=p["btn_active"],
            bordercolor=p["btn_border"], borderwidth=1,
            font=dict(color=p["text"], size=12),
            x=0, y=1.08,
        ),
    )
    # thin range-slider on the volume (bottom) axis for quick scrubbing
    fig.update_xaxes(row=2, col=1, rangeslider=dict(
        visible=True, thickness=0.06, bgcolor=p["slider_bg"],
        bordercolor=p["slider_border"], borderwidth=1))
    # hide weekends so candles sit flush together
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    fig.update_yaxes(row=1, col=1, tickprefix="$", side="right")
    fig.update_yaxes(row=2, col=1, showticklabels=False, showspikes=False)

    # default view: last 6 months
    if len(df) > 126:
        fig.update_xaxes(range=[df.index[-126], df.index[-1]])

    return fig


def sector_figure(rows: list[tuple], p: dict = DARK_CHART) -> go.Figure:
    """Horizontal sector relative-strength bars. rows: (name, etf, rel, ret)."""
    fig = go.Figure(go.Bar(
        x=[r[2] * 100 for r in rows],
        y=[f"{r[0]}  ·  {r[1]}" for r in rows],
        orientation="h",
        marker=dict(
            color=[p["up"] if r[2] > 0 else p["down"] for r in rows],
            opacity=0.85, line_width=0,
        ),
        text=[f"{r[2] * 100:+.1f}%" for r in rows],
        textposition="outside",
        textfont=dict(size=12, color=p["text"]),
        hovertemplate="%{y}<br>vs SPY: %{x:+.1f}%<extra></extra>",
    ))
    _base_layout(fig, height=470, p=p)
    fig.update_layout(hovermode="y", dragmode=False, showlegend=False,
                      margin=dict(l=10, r=55, t=30, b=10),
                      xaxis_title="1-month return relative to SPY (%)")
    fig.add_vline(x=0, line=dict(color=p["zero"], width=1))
    span = max(abs(r[2]) for r in rows) * 100 * 1.35 if rows else 10
    fig.update_xaxes(range=[-span, span], showspikes=False)
    fig.update_yaxes(showspikes=False)
    return fig
