"""Top-of-book spread, size imbalance and USD depth; no full-book inference."""

import math


def book_features(row):
    try:
        bid, ask, bid_size, ask_size = [
            float(row[key]) for key in ("bid_px", "ask_px", "bid_sz", "ask_sz")
        ]
    except (TypeError, ValueError, KeyError):
        return None
    if (
        not all(math.isfinite(v) for v in (bid, ask, bid_size, ask_size))
        or not 0 < bid <= ask
        or min(bid_size, ask_size) < 0
        or bid_size + ask_size <= 0
    ):
        return None
    mid = (bid + ask) / 2
    return {
        "spread_bps": (ask - bid) / mid * 10000,
        "obi": (bid_size - ask_size) / (bid_size + ask_size),
        "log_depth": math.log1p(bid * bid_size + ask * ask_size),
    }
