"""Drift alerting: has the portfolio moved too far from its target allocation?"""

from __future__ import annotations

from allocation import current_weights, target_weights

DRIFT_ALERT_THRESHOLD = 0.05


def check_drift(portfolio: list[dict], profile: dict[str, float]) -> list[str]:
    """Symbols whose current weight has drifted from target by more than the threshold.

    Never calls `get_price` itself, but depends on it indirectly through `current_weights`.
    """
    current = current_weights(portfolio)
    target = target_weights(profile)
    return [
        symbol for symbol, target_weight in target.items()
        if abs(target_weight - current.get(symbol, 0.0)) > DRIFT_ALERT_THRESHOLD
    ]
