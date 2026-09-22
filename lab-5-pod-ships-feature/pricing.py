"""Price lookups for the Lab 5 toy portfolio codebase.

`get_price` is the function WM-114 proposes changing: adding an `as_of_date` parameter so
statements can be backdated to a historical price. Everything else in this package exists so
that change has a real blast radius to trace. This file is deliberately the smallest, most
innocuous-looking one, which is exactly the point.
"""

from __future__ import annotations

# A tiny in-memory price table. This lab is about tracing dependencies, not real market data.
_PRICES = {
    "AAPL": 150.00,
    "MSFT": 300.00,
    "KO": 62.00,
    "SAP": 108.00,
}


def get_price(symbol: str) -> float:
    """Current price for `symbol`. WM-114 proposes adding an `as_of_date` parameter here."""
    if symbol not in _PRICES:
        raise KeyError(f"no price for {symbol}")
    return _PRICES[symbol]
