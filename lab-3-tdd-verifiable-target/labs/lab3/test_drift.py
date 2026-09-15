"""Tests for drift alert detection — the verifiable target for Lab 3.

Two tests pass with the current implementation (basic threshold detection).
One test FAILS — it defines the hysteresis behavior that Lab 3 must implement.
The fourth test passes accidentally (alerts for the wrong reason) and will
continue to pass once hysteresis is correctly implemented.
"""

from datetime import datetime, timedelta

import pytest

from labs.lab3.drift import DriftReading, check_drift_alert


def _reading(minutes_ago: int, drift_percent: float) -> DriftReading:
    """Helper to create a reading at a specific time offset."""
    return DriftReading(
        timestamp=datetime(2024, 1, 15, 10, 0) - timedelta(minutes=minutes_ago),
        drift_percent=drift_percent,
    )


# ── These tests PASS with the current implementation ─────────────────────────


def test_no_alert_when_within_threshold():
    """No alert if drift stays within the threshold."""
    readings = [
        _reading(10, 3.0),  # 3% drift — within 5% threshold
        _reading(5, 4.5),   # 4.5% drift — still within
        _reading(0, 2.0),   # 2% drift — within
    ]
    alert = check_drift_alert("P-001", readings, threshold_percent=5.0)
    assert alert is None


def test_alert_when_breach_exceeds_threshold():
    """Alert fires when drift exceeds threshold (no min_duration)."""
    readings = [
        _reading(10, 3.0),  # within
        _reading(5, 6.5),   # breach! 6.5% > 5%
        _reading(0, 4.0),   # back within
    ]
    alert = check_drift_alert("P-001", readings, threshold_percent=5.0, min_duration_minutes=0)
    assert alert is not None
    assert alert.portfolio_id == "P-001"
    assert alert.drift_percent == 6.5


# ── These tests FAIL — they are the verifiable target for Lab 3 ──────────────


def test_no_alert_for_brief_spike():
    """A spike lasting less than min_duration should NOT alert.

    This is the hysteresis behavior: ignore brief spikes that self-correct.
    The current implementation fails this — it alerts on any breach.
    """
    readings = [
        _reading(10, 3.0),  # within
        _reading(5, 7.0),   # spike! but only lasts 3 minutes
        _reading(2, 4.0),   # back within after 3 minutes
        _reading(0, 3.5),   # still within
    ]
    # With min_duration_minutes=5, a 3-minute spike should NOT alert
    alert = check_drift_alert("P-001", readings, threshold_percent=5.0, min_duration_minutes=5)
    assert alert is None, "Brief spike (< min_duration) should not fire an alert"


def test_alert_after_sustained_breach():
    """A breach lasting >= min_duration SHOULD alert.

    This confirms hysteresis lets through sustained breaches while filtering spikes.
    The current implementation may pass this accidentally (it alerts immediately),
    but combined with test_no_alert_for_brief_spike, both must pass together.
    """
    readings = [
        _reading(15, 3.0),  # within
        _reading(10, 6.0),  # breach starts
        _reading(5, 6.5),   # still breaching (5 minutes elapsed)
        _reading(0, 7.0),   # still breaching (10 minutes elapsed)
    ]
    # With min_duration_minutes=5, a 10-minute breach should alert
    alert = check_drift_alert("P-001", readings, threshold_percent=5.0, min_duration_minutes=5)
    assert alert is not None, "Sustained breach (>= min_duration) should fire an alert"
    assert alert.drift_percent >= 6.0
