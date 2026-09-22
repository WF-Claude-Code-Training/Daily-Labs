#!/usr/bin/env python3
"""Verifiable target for WM-118 (`statement_delta`): deliberately not a pytest file.

Every other required ticket in this course ships with its acceptance tests pre-written, so a
subagent never has to originate one from scratch, the whole point of `test-author`'s first job
("turn acceptance criteria into failing tests") never comes up. This ticket is the one exception:
there is no `test_statement_delta.py` for you to read. `test-author` writes it, from the ticket
text in `backlog/WM-118-statement-comparison.md` and the docstring on the stub in
`statement_delta.py`, nobody hands it the contract pre-parsed.

This script is a **floor**, not the spec: three fixed scenarios with known-correct answers,
computed against the already-migrated fee/rebalance/drift functions (not by hand, arithmetic
mistakes are exactly how a checker like this gets built wrong). It exists so there's still a
deterministic, offline pass/fail independent of whatever `test-author` wrote, the same way
`check_impact_note.py` and `check_pod.py` check things a pytest suite in this course doesn't.
It does **not** replace `test-author`'s tests, and it deliberately does not test every edge case
the ticket raises (see the note on same-symbol amount changes, below), that gap is real, and
noticing it is part of the exercise, not an oversight to quietly patch.

    python3 check_statement_delta.py
"""

from __future__ import annotations

import sys

Q1, TODAY = "2026-03-31", "2026-07-24"

# Three scenarios, each pinned against the real fee/trades/drift functions with as_of_date
# already threaded through (WM-114). If your migration has a bug, this will fail here before
# it fails somewhere more confusing.
SCENARIOS = [
    {
        "label": "fee changes, nothing else does",
        "portfolio": [{"symbol": "AAPL", "qty": 100}, {"symbol": "MSFT", "qty": 50}],
        "profile": {"AAPL": 0.5, "MSFT": 0.5},
        "from_date": Q1, "to_date": TODAY,
        "expect": {"fee_delta": 39.25, "trades_added": [], "trades_removed": [],
                   "alerts_added": [], "alerts_removed": []},
    },
    {
        "label": "trades that existed at from_date no longer do",
        "portfolio": [{"symbol": "AAPL", "qty": 62}, {"symbol": "KO", "qty": 150}],
        "profile": {"AAPL": 0.5, "KO": 0.5},
        "from_date": Q1, "to_date": TODAY,
        "expect": {"fee_delta": 19.64, "trades_added": [], "trades_removed": ["AAPL", "KO"],
                   "alerts_added": [], "alerts_removed": []},
    },
    {
        "label": "a drift alert that fired at from_date clears by to_date",
        "portfolio": [{"symbol": "KO", "qty": 100}, {"symbol": "SAP", "qty": 50}],
        "profile": {"KO": 0.5, "SAP": 0.5},
        "from_date": Q1, "to_date": TODAY,
        # Both symbols still trade at both dates here, only the dollar amount changes, and
        # that's the presence-based-diffing limitation below. trades_added/removed are
        # correctly [] under that definition; only the alert clearing is asserted as a change.
        "expect": {"fee_delta": 10.62, "trades_added": [], "trades_removed": [],
                   "alerts_added": [], "alerts_removed": ["KO", "SAP"]},
    },
    {
        "label": "same date twice is a no-op",
        "portfolio": [{"symbol": "AAPL", "qty": 100}],
        "profile": {"AAPL": 1.0},
        "from_date": TODAY, "to_date": TODAY,
        "expect": {"fee_delta": 0.0, "trades_added": [], "trades_removed": [],
                   "alerts_added": [], "alerts_removed": []},
    },
]


def main() -> int:
    try:
        from statement_delta import statement_delta
    except ImportError as exc:
        print(f"Can't import statement_delta.statement_delta: {exc}")
        print("Nothing to check yet, this is expected before WM-118 is implemented.")
        return 1

    print("WM-118 statement_delta check")
    print("=" * 60)

    failures = 0
    for scenario in SCENARIOS:
        try:
            actual = statement_delta(scenario["portfolio"], scenario["profile"],
                                     scenario["from_date"], scenario["to_date"])
        except Exception as exc:  # noqa: BLE001 - surface any exception as a failure, not a crash
            print(f"[FAIL] {scenario['label']}: raised {type(exc).__name__}: {exc}")
            failures += 1
            continue

        mismatches = []
        for key, expected in scenario["expect"].items():
            got = actual.get(key) if isinstance(actual, dict) else None
            if got != expected:
                mismatches.append(f"{key}: expected {expected!r}, got {got!r}")

        if mismatches:
            print(f"[FAIL] {scenario['label']}")
            for m in mismatches:
                print(f"       {m}")
            failures += 1
        else:
            print(f"[ok]   {scenario['label']}")

    print("=" * 60)
    if failures:
        print(f"{failures}/{len(SCENARIOS)} scenario(s) failed.")
        return 1
    print(f"All {len(SCENARIOS)} scenarios passed.")
    print()
    print("This is a floor, not the spec: it does not check every property the ticket raises")
    print("(e.g. a trade whose symbol and action are unchanged but dollar amount moved). If")
    print("test-author's tests only cover what's checked here, that's a gap worth naming.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
