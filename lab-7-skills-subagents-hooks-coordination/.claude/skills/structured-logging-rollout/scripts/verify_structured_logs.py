#!/usr/bin/env python3
"""Verify structured-logging coverage for one or more domains — the Skill's Bash-run checker.

Deterministic, stdlib-only, no API key. Meant to be invoked via Bash during Phase D of the
structured-logging-rollout Skill, so its logic never has to be read into the conversation's
context — only its pass/fail output does.

Usage:
    python3 scripts/verify_structured_logs.py                 # check every known domain
    python3 scripts/verify_structured_logs.py fees drift       # check just these domains

Exit code 0 if every checked domain logs the expected event(s); 1 otherwise, with a report of
exactly which domain/event is missing.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

# Run from anywhere in this package: put the package root (this script's great-great-grandparent
# — .claude/skills/structured-logging-rollout/scripts/ -> package root) on sys.path.
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from agentic_framing.logging_utils import capture_log_events  # noqa: E402


def _check_fees() -> list[str]:
    from fees import annual_advisory_fee

    problems: list[str] = []
    with capture_log_events("fees") as events:
        annual_advisory_fee(1_000_000)

    fee_events = [e for e in events if e.get("event") == "fee_calculated"]
    if not fee_events:
        problems.append("fees: no 'fee_calculated' event logged by annual_advisory_fee()")
    elif "aum" not in fee_events[0] or "fee" not in fee_events[0]:
        problems.append(f"fees: 'fee_calculated' event is missing aum/fee fields: {fee_events[0]}")
    return problems


def _check_reconcile() -> list[str]:
    from reconcile import reconcile_positions

    problems: list[str] = []
    book = [{"symbol": "KO", "qty": 100, "price": 61.231, "settle_date": "2024-01-10"}]
    custodian = [{"symbol": "KO", "qty": 100, "price": 61.23, "settle_date": "2024-01-10"}]
    with capture_log_events("reconcile") as events:
        reconcile_positions(book, custodian)

    resolved = [e for e in events if e.get("event") == "position_resolved"]
    if not resolved:
        problems.append(
            "reconcile: no 'position_resolved' event logged for an explained mismatch"
        )
    elif "symbol" not in resolved[0] or "strategy" not in resolved[0]:
        problems.append(f"reconcile: 'position_resolved' missing symbol/strategy: {resolved[0]}")

    book = [{"symbol": "GOOG", "qty": 50, "price": 140.00, "settle_date": "2024-01-10"}]
    custodian = [{"symbol": "GOOG", "qty": 75, "price": 140.00, "settle_date": "2024-01-10"}]
    with capture_log_events("reconcile") as events:
        reconcile_positions(book, custodian)

    escalated = [e for e in events if e.get("event") == "position_escalated"]
    if not escalated:
        problems.append("reconcile: no 'position_escalated' event logged for a genuine break")
    elif "symbol" not in escalated[0] or "risk_level" not in escalated[0]:
        problems.append(
            f"reconcile: 'position_escalated' missing symbol/risk_level: {escalated[0]}"
        )
    return problems


def _check_drift() -> list[str]:
    from datetime import datetime, timedelta

    from drift import DriftReading, check_drift_alert

    problems: list[str] = []
    readings = [
        DriftReading(timestamp=datetime(2024, 1, 15, 10, 0) - timedelta(minutes=5), drift_percent=3.0),
        DriftReading(timestamp=datetime(2024, 1, 15, 10, 0), drift_percent=6.5),
    ]
    with capture_log_events("drift") as events:
        alert = check_drift_alert("P-001", readings, threshold_percent=5.0, min_duration_minutes=0)

    if alert is None:
        problems.append("drift: check_drift_alert unexpectedly returned no alert — can't verify logging")
        return problems

    fired = [e for e in events if e.get("event") == "drift_alert_fired"]
    if not fired:
        problems.append("drift: no 'drift_alert_fired' event logged when an alert fires")
    elif "portfolio_id" not in fired[0] or "drift_percent" not in fired[0]:
        problems.append(f"drift: 'drift_alert_fired' missing portfolio_id/drift_percent: {fired[0]}")
    return problems


CHECKS: dict[str, Callable[[], list[str]]] = {
    "fees": _check_fees,
    "reconcile": _check_reconcile,
    "drift": _check_drift,
}


def main(argv: list[str]) -> int:
    domains = argv or list(CHECKS.keys())
    unknown = [d for d in domains if d not in CHECKS]
    if unknown:
        print(f"Unknown domain(s): {', '.join(unknown)}. Known: {', '.join(CHECKS)}")
        return 1

    all_problems: list[str] = []
    for domain in domains:
        try:
            problems = CHECKS[domain]()
        except ImportError as exc:
            problems = [f"{domain}: import failed — {exc}"]
        if problems:
            all_problems.extend(problems)
        else:
            print(f"PASS  {domain}: structured logging verified")

    if all_problems:
        print("\nFAIL:")
        for problem in all_problems:
            print(f"  - {problem}")
        return 1

    print("\nAll checked domains log the expected structured events.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
