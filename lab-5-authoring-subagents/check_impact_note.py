"""Deterministic checker for the WM-114 change-impact note (Lab 5's verifiable target).

Not a test suite — there's no code to change in this lab, just a note to write. This checks
that the note names every function actually affected if `get_price`'s signature changes, so
"I read the code" turns into something checkable instead of a vibe.

Usage:
    python3 check_impact_note.py impact_note.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# (function, file) pairs that call get_price directly.
DIRECT_CALLERS = [
    ("current_weights", "allocation.py"),
    ("compute_trades", "rebalance.py"),
    ("advisory_fee", "fees.py"),
]

# Functions that don't call get_price directly but depend on it transitively through a direct
# caller above — easy to miss if you stop at a grep for "get_price(".
TRANSITIVE_CALLERS = [
    ("check_drift", "drift.py"),           # via current_weights
    ("build_statement", "statements.py"),  # via advisory_fee, compute_trades, check_drift
]


def check(note_text: str) -> int:
    missing = []
    for label, group in (("direct caller", DIRECT_CALLERS), ("transitive caller", TRANSITIVE_CALLERS)):
        for func, file in group:
            if not re.search(rf"\b{re.escape(func)}\b", note_text):
                missing.append(f"  [ ] {label}: `{func}` ({file}) not mentioned")

    total = len(DIRECT_CALLERS) + len(TRANSITIVE_CALLERS)
    print("WM-114 change-impact note check")
    print("=" * 40)
    if not missing:
        print(f"All {total} required call sites are named in the note.")
        return 0

    print("Missing from the note:")
    for line in missing:
        print(line)
    print(f"\n{total - len(missing)}/{total} required call sites found.")
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 check_impact_note.py <path-to-note.md>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 2
    return check(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
