"""Stock universe definitions spanning all market-cap tiers and sectors."""

# Curated universe: liquid, well-covered names across every cap tier so the
# cap/style buckets are all populated. Users can add their own tickers in the UI.
CORE_UNIVERSE = [
    # Mega caps (>= $200B)
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B",
    "JPM", "V", "UNH", "XOM", "JNJ", "PG", "LLY", "AVGO", "COST", "WMT",
    # Large caps ($10B - $200B)
    "AMD", "NFLX", "CRM", "DIS", "NKE", "PFE", "T", "BA", "CAT", "GS",
    "SBUX", "UBER", "PLTR", "DE", "MMM", "GE", "CVS", "TGT", "F", "GM",
    # Mid caps ($2B - $10B)
    "ETSY", "CROX", "WSM", "DKS", "CHWY", "RIVN", "SOFI", "DKNG",
    "AFRM", "U", "ROKU", "PINS", "LYFT", "MAT", "HOG",
    # Small caps ($300M - $2B)
    "RXRX", "FUBO", "JOBY", "PTON", "RUN", "PLUG", "BLNK", "OPEN",
    "CLOV", "GPRO",
    # Micro caps (< $300M) — thinly covered, treated as speculative
    "NNDM", "SENS", "WKHS", "SLDP",
]

# Sector name (as reported by Yahoo Finance) -> SPDR sector ETF proxy
SECTOR_ETFS = {
    "Technology": "XLK",
    "Financial Services": "XLF",
    "Healthcare": "XLV",
    "Energy": "XLE",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Industrials": "XLI",
    "Basic Materials": "XLB",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
}

BENCHMARK = "SPY"
