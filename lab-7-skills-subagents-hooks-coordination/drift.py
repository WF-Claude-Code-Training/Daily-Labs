"""Drift alert detection for portfolio monitoring.

A portfolio "drifts" when its actual allocation deviates from its target allocation.
This module detects when drift exceeds a threshold and fires an alert.

Lab 3 (an earlier lab in this course, not included in this package) adds **hysteresis** to
reduce false positives: a brief spike that self-corrects should not fire an alert. Only
sustained breaches (lasting >= min_duration_minutes) should alert. This lab's logging work does
not depend on whether that fix has been applied: see `test_logging.py`'s docstring.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DriftReading:
    """A single drift measurement at a point in time."""

    timestamp: datetime
    drift_percent: float  # how far the portfolio is from target, as a percentage


@dataclass
class DriftAlert:
    """An alert fired when drift exceeds threshold."""

    portfolio_id: str
    drift_percent: float
    threshold_percent: float
    timestamp: datetime
    message: str


def check_drift_alert(
    portfolio_id: str,
    readings: list[DriftReading],
    threshold_percent: float = 5.0,
    min_duration_minutes: int = 0,
) -> DriftAlert | None:
    """Check if the portfolio should fire a drift alert.

    Args:
        portfolio_id: Identifier for the portfolio being monitored.
        readings: Time-series of drift measurements, oldest first.
        threshold_percent: Drift percentage that triggers an alert (default 5%).
        min_duration_minutes: Minimum duration (in minutes) the drift must exceed
            the threshold before alerting. Set to 0 for immediate alerts.

    Returns:
        A DriftAlert if the threshold is breached for at least min_duration_minutes,
        None otherwise.

    Hysteresis behavior: brief spikes that self-correct within min_duration_minutes
    do not fire alerts. Only sustained breaches trigger notifications.
    """
    if not readings:
        return None

    # Sort readings by timestamp (oldest first)
    sorted_readings = sorted(readings, key=lambda r: r.timestamp)

    # Current implementation: alert immediately on ANY breach.
    # TODO: Add hysteresis: only alert if breach lasts >= min_duration_minutes.
    #       Brief spikes that self-correct should NOT fire alerts.
    for reading in sorted_readings:
        if abs(reading.drift_percent) > threshold_percent:
            # Alert immediately: ignores min_duration_minutes
            return DriftAlert(
                portfolio_id=portfolio_id,
                drift_percent=reading.drift_percent,
                threshold_percent=threshold_percent,
                timestamp=reading.timestamp,
                message=f"Portfolio {portfolio_id} drifted {reading.drift_percent:.1f}% "
                f"(threshold: {threshold_percent}%)",
            )

    return None
