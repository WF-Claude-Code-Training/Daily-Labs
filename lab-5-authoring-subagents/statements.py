"""Client statement generation — the top of this package's call graph."""

from __future__ import annotations

from drift import check_drift
from fees import advisory_fee
from rebalance import compute_trades


def build_statement(portfolio: list[dict], profile: dict[str, float]) -> str:
    """A plain-text client statement: fee, recommended trades, and any drift alerts.

    Never mentions pricing at all in its own body — but nothing in it is safe from a
    `get_price` change: every value it prints traces back through `advisory_fee`,
    `compute_trades`, or `check_drift`.
    """
    fee = advisory_fee(portfolio)
    trades = compute_trades(portfolio, profile)
    alerts = check_drift(portfolio, profile)

    lines = [f"Annual advisory fee: ${fee:,.2f}", f"Recommended trades: {len(trades)}"]
    for t in trades:
        lines.append(f"  {t['action']} {t['symbol']} (${t['dollar_amount']:,.2f})")
    if alerts:
        lines.append(f"Drift alerts: {', '.join(alerts)}")
    return "\n".join(lines)
