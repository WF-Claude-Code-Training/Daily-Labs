"""Acceptance contract for the second half of WM-109, querying the audit trail.

Seeded failing: `audit_query.py` does not exist yet.

An audit trail nobody can query is not an audit trail; it's a disk-space bill. WM-109's ticket
stops at "emit structured events," which is why the compliance analyst who asked for it still
can't answer the question they actually have: *"show me every HIGH-risk escalation from the
2am run."* This suite is that question, made checkable.

The fixture (`fixtures/audit_trail.jsonl`) is a captured night's output, supplied so this half
of the ticket can be built and verified **independently of the logging half**. It contains 12
valid events and three lines that are not events: a blank line, a log-rotation marker, and a
truncated write. Real log files contain all three, and a query tool that dies on any of them is
a tool the analyst stops trusting at exactly the wrong moment.

    python3 -m pytest test_audit_query.py -v
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent
TRAIL = REPO_ROOT / "fixtures" / "audit_trail.jsonl"

TOTAL_VALID_EVENTS = 12


# ══ Parsing: survive a real log file ══════════════════════════════════════════


def test_load_events_reads_every_valid_event():
    from audit_query import load_events

    assert len(load_events(TRAIL)) == TOTAL_VALID_EVENTS


def test_load_events_skips_junk_lines_without_raising():
    """Blank line, rotation marker, truncated JSON: skipped, not fatal, not counted."""
    from audit_query import load_events

    events = load_events(TRAIL)
    assert all(isinstance(e, dict) and "event" in e for e in events)


def test_load_events_is_not_silently_lossy():
    """Skipping a malformed line is correct. Skipping it *silently* is how you lose an audit.

    The count of lines that couldn't be parsed has to be reachable, or nobody can tell the
    difference between "quiet night" and "half the file didn't parse."
    """
    from audit_query import load_events, unparsed_line_count

    load_events(TRAIL)
    assert unparsed_line_count(TRAIL) == 3


# ══ Querying: the questions compliance actually asks ══════════════════════════


def test_query_by_event_name():
    from audit_query import load_events, query

    events = load_events(TRAIL)
    assert len(query(events, event="fee_calculated")) == 3
    assert len(query(events, event="position_escalated")) == 4
    assert len(query(events, event="drift_alert_fired")) == 2


def test_query_by_risk_level_answers_the_compliance_question():
    """"Show me every HIGH-risk escalation", the reason this tool exists."""
    from audit_query import load_events, query

    hits = query(load_events(TRAIL), event="position_escalated", risk_level="HIGH")
    assert [e["symbol"] for e in hits] == ["TSLA"]


def test_query_by_symbol():
    from audit_query import load_events, query

    assert len(query(load_events(TRAIL), symbol="ORCL")) == 1


def test_query_by_time_window_is_inclusive():
    from audit_query import load_events, query

    events = load_events(TRAIL)
    window = query(events, since="2026-07-24T02:01:00", until="2026-07-24T02:02:00")
    assert len(window) == 4  # three resolutions plus the first escalation


def test_query_with_no_filters_returns_everything():
    """A query tool whose default is "nothing" gets used wrong on the first try."""
    from audit_query import load_events, query

    events = load_events(TRAIL)
    assert len(query(events)) == TOTAL_VALID_EVENTS


def test_query_filters_combine_as_and_not_or():
    from audit_query import load_events, query

    events = load_events(TRAIL)
    assert query(events, event="fee_calculated", symbol="ORCL") == []


def test_query_for_something_absent_returns_empty_not_an_error():
    from audit_query import load_events, query

    assert query(load_events(TRAIL), event="account_closed") == []


def test_query_does_not_mutate_its_input():
    """The analyst will run five queries against one load. They must not interfere."""
    from audit_query import load_events, query

    events = load_events(TRAIL)
    before = json.dumps(events, sort_keys=True)
    query(events, event="position_escalated", risk_level="HIGH")
    assert json.dumps(events, sort_keys=True) == before


# ══ Summarizing ═══════════════════════════════════════════════════════════════


def test_summarize_counts_by_event_name():
    from audit_query import load_events, summarize

    assert summarize(load_events(TRAIL)) == {
        "fee_calculated": 3,
        "position_resolved": 3,
        "position_escalated": 4,
        "drift_alert_fired": 2,
    }


def test_summarize_of_nothing_is_empty_not_an_error():
    from audit_query import summarize

    assert summarize([]) == {}


# ══ The CLI: what the analyst actually types ═════════════════════════════════


def _cli(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "audit_query.py"), *args],
        text=True, capture_output=True, cwd=REPO_ROOT,
    )


def test_cli_filters_and_exits_zero():
    result = _cli(str(TRAIL), "--event", "position_escalated", "--risk-level", "HIGH")
    assert result.returncode == 0, result.stderr
    assert "TSLA" in result.stdout
    assert "GOOG" not in result.stdout


def test_cli_summary_mode():
    result = _cli(str(TRAIL), "--summary")
    assert result.returncode == 0, result.stderr
    assert "position_escalated" in result.stdout
    assert "4" in result.stdout


def test_cli_reports_unparsed_lines_to_stderr():
    """Visible on stderr so it can't be missed, but not fatal. The query still runs."""
    result = _cli(str(TRAIL), "--summary")
    assert result.returncode == 0
    assert "3" in result.stderr


def test_cli_missing_file_fails_loudly():
    result = _cli("fixtures/no_such_trail.jsonl", "--summary")
    assert result.returncode != 0


@pytest.mark.parametrize("flag", ["--event", "--symbol", "--risk-level"])
def test_cli_supports_each_documented_filter(flag):
    result = _cli(str(TRAIL), flag, "nonexistent-value")
    assert result.returncode == 0, f"{flag} should be accepted: {result.stderr}"
