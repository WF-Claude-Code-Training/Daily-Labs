"""Advisory fee calculation."""

from __future__ import annotations

from pricing import get_price

ANNUAL_FEE_RATE = 0.01


def advisory_fee(portfolio: list[dict]) -> float:
    """Annual advisory fee: a flat rate on the portfolio's total market value.

    Calls `get_price` directly.
    """
    total = sum(p["qty"] * get_price(p["symbol"]) for p in portfolio)
    return round(total * ANNUAL_FEE_RATE, 2)
