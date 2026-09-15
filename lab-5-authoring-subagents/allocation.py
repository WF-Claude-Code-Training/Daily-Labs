"""Target vs. current portfolio allocation."""

from __future__ import annotations

from pricing import get_price


def current_weights(portfolio: list[dict]) -> dict[str, float]:
    """Each position's share of the portfolio's total market value. Calls `get_price` directly."""
    values = {p["symbol"]: p["qty"] * get_price(p["symbol"]) for p in portfolio}
    total = sum(values.values()) or 1.0
    return {symbol: value / total for symbol, value in values.items()}


def target_weights(profile: dict[str, float]) -> dict[str, float]:
    """The household's target allocation — a static profile, no pricing involved at all."""
    return dict(profile)
