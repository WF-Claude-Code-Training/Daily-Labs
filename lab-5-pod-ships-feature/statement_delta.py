"""WM-118: compare two statement dates for the same household. Not yet implemented.

There is deliberately no `test_statement_delta.py` in this folder. Every other required ticket
in this course ships with its test suite pre-written; this one doesn't, on purpose. It's the
only place all day `test-author` gets to do its actual first job (turn acceptance criteria into
failing tests) instead of its second (repair a test a change made stale).

Read `backlog/WM-118-statement-comparison.md`, decide what "changed" means, have `test-author`
write the tests, then implement `statement_delta` to satisfy them.

`check_statement_delta.py` is a deterministic floor, a few fixed scenarios with known-correct
answers, not the spec. It intentionally does not cover every case the ticket raises. Passing it
is necessary, not sufficient.
"""

from __future__ import annotations


def statement_delta(portfolio: list[dict], profile: dict[str, float],
                    from_date: str, to_date: str) -> dict:
    """Compare a household's statement at `from_date` against `to_date`.

    Return a dict describing what changed. At minimum, callers need to know: did the advisory
    fee change, and by how much; which trades were recommended at one date but not the other;
    which drift alerts fired at one date but not the other. The exact shape of "which trades"
    and "which alerts", matched by symbol? by symbol and action?, is a decision the ticket
    leaves open; make it deliberately, and have `test-author`'s tests state it explicitly rather
    than leaving it implicit in the implementation.
    """
    raise NotImplementedError("WM-118: see backlog/WM-118-statement-comparison.md")
