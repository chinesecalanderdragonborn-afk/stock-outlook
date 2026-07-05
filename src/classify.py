"""Stock classification: market-cap tiers and investor-style buckets."""
from __future__ import annotations

CAP_ORDER = ["Mega", "Large", "Mid", "Small", "Micro", "Unknown"]


def cap_class(market_cap: float | None) -> str:
    """Standard market-cap tiers."""
    if not market_cap:
        return "Unknown"
    if market_cap >= 200e9:
        return "Mega"
    if market_cap >= 10e9:
        return "Large"
    if market_cap >= 2e9:
        return "Mid"
    if market_cap >= 300e6:
        return "Small"
    return "Micro"


def style_class(profile: dict) -> tuple[str, list[str]]:
    """Primary investor style (Growth / Value / Blend / Speculative)
    plus secondary tags (Dividend, Defensive, High Beta)."""
    pe = profile.get("trailing_pe")
    fpe = profile.get("forward_pe")
    pb = profile.get("price_to_book")
    rev_g = profile.get("revenue_growth")
    earn_g = profile.get("earnings_growth")
    dy = profile.get("dividend_yield") or 0
    beta = profile.get("beta")
    margin = profile.get("profit_margin")
    sector = profile.get("sector", "")

    # dividend_yield changed to percent units in recent yfinance; normalize
    if dy and dy < 0.5:
        dy = dy * 100

    growth_pts = 0
    value_pts = 0
    if rev_g is not None and rev_g > 0.15:
        growth_pts += 2
    elif rev_g is not None and rev_g > 0.08:
        growth_pts += 1
    if earn_g is not None and earn_g > 0.15:
        growth_pts += 1
    if pe is not None and pe > 35:
        growth_pts += 1
    if pe is not None and 0 < pe < 16:
        value_pts += 2
    elif pe is not None and 0 < pe < 22:
        value_pts += 1
    if fpe is not None and 0 < fpe < 14:
        value_pts += 1
    if pb is not None and 0 < pb < 2.5:
        value_pts += 1
    if dy > 2.5:
        value_pts += 1

    unprofitable = (pe is None) and (margin is None or margin < 0)
    if unprofitable and cap_class(profile.get("market_cap")) in ("Small", "Micro"):
        primary = "Speculative"
    elif growth_pts >= value_pts + 2:
        primary = "Growth"
    elif value_pts >= growth_pts + 2:
        primary = "Value"
    else:
        primary = "Blend"

    tags = []
    if dy >= 3:
        tags.append("Dividend/Income")
    if sector in ("Utilities", "Consumer Defensive", "Healthcare") and (beta or 1) < 0.9:
        tags.append("Defensive")
    if beta is not None and beta > 1.4:
        tags.append("High Beta")
    return primary, tags
