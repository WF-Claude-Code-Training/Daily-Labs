"""Compute the trades needed to bring a portfolio back to its target allocation."""

from __future__ import annotations

from allocation import current_weights, target_weights
from pricing import get_price


def compute_trades(portfolio: list[dict], profile: dict[str, float]) -> list[dict]:
    """One trade per symbol whose current weight misses its target by more than 1%.

    Calls `get_price` directly (to size dollar amounts) and also depends on it indirectly
    through `current_weights`.
    """
    values = {p["symbol"]: p["qty"] * get_price(p["symbol"]) for p in portfolio}
    total = sum(values.values()) or 1.0
    current = current_weights(portfolio)
    target = target_weights(profile)

    trades = []
    for symbol, target_weight in target.items():
        drift = target_weight - current.get(symbol, 0.0)
        if abs(drift) > 0.01:
            trades.append({
                "symbol": symbol,
                "action": "BUY" if drift > 0 else "SELL",
                "dollar_amount": round(abs(drift) * total, 2),
            })
    return trades
