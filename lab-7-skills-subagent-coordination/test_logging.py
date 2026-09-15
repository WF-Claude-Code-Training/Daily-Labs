"""Tests for WM-109 structured logging — the verifiable target for this lab.

`fees.py`, `reconcile.py`, and `drift.py` don't call the shared structured logger yet — that's
the exercise. These tests are seeded to fail until the fix threads `agentic_framing.logging_utils`
through all three, per `README.md`.

Each test asserts on the *shape* of the emitted event (event name + the fields an auditor would
need), not on domain values earlier labs are responsible for getting right (e.g. the exact fee
amount, or whether hysteresis is implemented) — so this suite stays a clean signal for the
logging work specifically. `stock_split_adjustment` in `reconcile.py` is still stubbed and
`drift.py`'s hysteresis TODO is still open, on purpose — neither one blocks this lab.
"""

from datetime import datetime, timedelta

from agentic_framing.logging_utils import capture_log_events
from labs.lab1.fees import annual_advisory_fee
from labs.lab3.drift import DriftReading, check_drift_alert
from labs.lab4.reconcile import reconcile_positions


# ── Fee calculation ──────────────────────────────────────────────────────────


def test_fee_calculation_logs_fee_calculated_event():
    with capture_log_events("fees") as events:
        annual_advisory_fee(1_000_000)

    fee_events = [e for e in events if e["event"] == "fee_calculated"]
    assert len(fee_events) == 1, "annual_advisory_fee should log exactly one fee_calculated event"
    assert fee_events[0]["aum"] == 1_000_000
    assert isinstance(fee_events[0]["fee"], (int, float))


def test_fee_calculation_logs_one_event_per_call():
    with capture_log_events("fees") as events:
        annual_advisory_fee(500_000)
        annual_advisory_fee(2_000_000)

    fee_events = [e for e in events if e["event"] == "fee_calculated"]
    assert [e["aum"] for e in fee_events] == [500_000, 2_000_000]


# ── Reconciliation ───────────────────────────────────────────────────────────


def test_reconcile_logs_position_resolved_for_explained_mismatch():
    book = [{"symbol": "KO", "qty": 100, "price": 61.231, "settle_date": "2024-01-10"}]
    custodian = [{"symbol": "KO", "qty": 100, "price": 61.23, "settle_date": "2024-01-10"}]

    with capture_log_events("reconcile") as events:
        reconcile_positions(book, custodian)

    resolved_events = [e for e in events if e["event"] == "position_resolved"]
    assert len(resolved_events) == 1
    assert resolved_events[0]["symbol"] == "KO"
    assert resolved_events[0]["strategy"] == "rounding_tolerance"


def test_reconcile_logs_position_escalated_for_genuine_break():
    book = [{"symbol": "GOOG", "qty": 50, "price": 140.00, "settle_date": "2024-01-10"}]
    custodian = [{"symbol": "GOOG", "qty": 75, "price": 140.00, "settle_date": "2024-01-10"}]

    with capture_log_events("reconcile") as events:
        reconcile_positions(book, custodian)

    escalated_events = [e for e in events if e["event"] == "position_escalated"]
    assert len(escalated_events) == 1
    assert escalated_events[0]["symbol"] == "GOOG"
    assert "risk_level" in escalated_events[0]


def test_reconcile_does_not_log_for_exact_matches():
    book = [{"symbol": "MSFT", "qty": 10, "price": 400.00, "settle_date": "2024-01-10"}]
    custodian = [{"symbol": "MSFT", "qty": 10, "price": 400.00, "settle_date": "2024-01-10"}]

    with capture_log_events("reconcile") as events:
        reconcile_positions(book, custodian)

    assert events == [], "exact matches are routine — no audit-worthy event to log"


# ── Drift alerts ─────────────────────────────────────────────────────────────


def _reading(minutes_ago: int, drift_percent: float) -> DriftReading:
    return DriftReading(
        timestamp=datetime(2024, 1, 15, 10, 0) - timedelta(minutes=minutes_ago),
        drift_percent=drift_percent,
    )


def test_drift_alert_logs_when_it_fires():
    readings = [_reading(5, 3.0), _reading(0, 6.5)]

    with capture_log_events("drift") as events:
        alert = check_drift_alert("P-001", readings, threshold_percent=5.0, min_duration_minutes=0)

    assert alert is not None
    fired_events = [e for e in events if e["event"] == "drift_alert_fired"]
    assert len(fired_events) == 1
    assert fired_events[0]["portfolio_id"] == "P-001"
    assert fired_events[0]["drift_percent"] == 6.5


def test_drift_alert_does_not_log_when_no_alert_fires():
    readings = [_reading(5, 2.0), _reading(0, 3.0)]

    with capture_log_events("drift") as events:
        alert = check_drift_alert("P-001", readings, threshold_percent=5.0, min_duration_minutes=0)

    assert alert is None
    assert events == [], "no breach means nothing audit-worthy happened"
