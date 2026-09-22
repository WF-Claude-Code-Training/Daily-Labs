"""Stretch contracts for WM-116 and WM-117, optional, seeded failing.

**Not required for Lab 4's Definition of Done.** Pick these up if the pod is working and you
have time; skipping them entirely costs you nothing. If your room is running behind, this is the
file to leave alone.

  * **WM-116**: tiered risk policy, owned by Risk. Today every escalation below the threshold
    is MEDIUM, so a $12k break and a $900k break land in the same bucket.
  * **WM-117**: a machine-readable triage export, because Ops is screen-scraping our stdout.

Both are worth doing for the same reason WM-115 was: each one moves a value out of code and into
a file another team owns, which changes who can act and how fast. WM-117 is the one that will
teach you the most about your pod, because it needs a *new file*, notice which of your roles is
even able to create one, and what that implies about your hand-off.

    python3 -m pytest test_reconcile_stretch.py -v
"""

import csv
import io
import json
from pathlib import Path

import pytest

REFERENCE_DATA = Path(__file__).parent / "reference_data"
FIXTURES = Path(__file__).parent / "fixtures"


# ══ WM-116: Tiered risk policy, owned by Risk ═════════════════════════════════
#
# Today every escalation below the threshold is MEDIUM, so a $12k break and a $900k break land
# in the same bucket and advisors triage the wrong one first. Risk owns the bands; they live in
# reference_data/risk_policy.json, not in a constant.


def test_wm116_risk_level_for_classifies_by_band():
    from reconcile import load_risk_policy, risk_level_for

    policy = load_risk_policy(REFERENCE_DATA / "risk_policy.json")
    assert risk_level_for(10_000.0, policy) == "LOW"
    assert risk_level_for(500_000.0, policy) == "MEDIUM"
    assert risk_level_for(2_500_000.0, policy) == "HIGH"


def test_wm116_band_boundaries_are_inclusive():
    """A position exactly on a boundary takes the lower tier: no gap between bands."""
    from reconcile import load_risk_policy, risk_level_for

    policy = load_risk_policy(REFERENCE_DATA / "risk_policy.json")
    assert risk_level_for(50_000.0, policy) == "LOW"
    assert risk_level_for(50_000.01, policy) == "MEDIUM"


def test_wm116_small_break_escalates_low_not_medium():
    from reconcile import load_risk_policy, reconcile_positions

    policy = load_risk_policy(REFERENCE_DATA / "risk_policy.json")
    book = [{"symbol": "GOOG", "qty": 200, "price": 140.00}]      # $28,000 notional
    custodian = [{"symbol": "GOOG", "qty": 150, "price": 140.00}]
    results = reconcile_positions(book, custodian, risk_policy=policy)
    assert results[0].status == "ESCALATED"
    assert results[0].risk_level == "LOW"


def test_wm116_auto_resolve_ceiling_still_beats_a_matching_strategy():
    """The governance rule from Lab 4 survives the refactor: risk beats pattern-matching."""
    from reconcile import load_risk_policy, reconcile_positions

    policy = load_risk_policy(REFERENCE_DATA / "risk_policy.json")
    book = [{"symbol": "TSLA", "qty": 10000, "price": 250.001}]    # $2.5M, rounding explains it
    custodian = [{"symbol": "TSLA", "qty": 10000, "price": 250.00}]
    results = reconcile_positions(book, custodian, risk_policy=policy)
    assert results[0].status == "ESCALATED"
    assert results[0].risk_level == "HIGH"


def test_wm116_no_policy_means_todays_behavior():
    """back-compat: callers that pass no policy keep the MEDIUM/HIGH split they have now."""
    from reconcile import reconcile_positions

    book = [{"symbol": "GOOG", "qty": 200, "price": 140.00}]
    custodian = [{"symbol": "GOOG", "qty": 150, "price": 140.00}]
    results = reconcile_positions(book, custodian)
    assert results[0].risk_level == "MEDIUM"


# ══ WM-117: Machine-readable triage export for Ops ════════════════════════════
#
# The pretty-printed report is for humans. Ops needs to ingest the run: one row per position,
# stable columns, every symbol accounted for.

EXPECTED_COLUMNS = {"symbol", "status", "strategy", "risk_level", "attempted_strategies", "detail"}


def _fixture_report():
    from reconcile import load_positions, triage

    book = load_positions(FIXTURES / "book_positions.csv")
    custodian = load_positions(FIXTURES / "custodian_file.csv")
    return triage(book, custodian)


def test_wm117_every_symbol_appears_exactly_once_in_the_export():
    """The non-negotiable property from WM-106, carried into the export format."""
    from export import triage_rows

    rows = triage_rows(_fixture_report())
    symbols = [r["symbol"] for r in rows]
    assert len(symbols) == len(set(symbols)), "no duplicate rows"
    assert set(symbols) == {"AAPL", "MSFT", "KO", "SAP", "GOOG", "TSLA", "NVDA", "ORCL"}


def test_wm117_rows_have_a_stable_column_set():
    from export import triage_rows

    for row in triage_rows(_fixture_report()):
        assert set(row) == EXPECTED_COLUMNS, "every row carries every column, even when empty"


def test_wm117_json_export_parses_and_round_trips():
    from export import render_json, triage_rows

    payload = json.loads(render_json(_fixture_report()))
    assert len(payload) == len(triage_rows(_fixture_report()))
    orcl = next(r for r in payload if r["symbol"] == "ORCL")
    assert orcl["status"] == "ESCALATED"
    assert orcl["attempted_strategies"], "an escalation must show what was tried"


def test_wm117_csv_export_has_a_header_and_one_row_per_symbol():
    from export import render_csv

    reader = csv.DictReader(io.StringIO(render_csv(_fixture_report())))
    rows = list(reader)
    assert set(reader.fieldnames or []) == EXPECTED_COLUMNS
    assert len(rows) == 8


def test_wm117_csv_attempted_strategies_is_a_single_flat_cell():
    """A list has to be flattened to survive CSV: pick a separator and be consistent."""
    from export import render_csv

    rows = list(csv.DictReader(io.StringIO(render_csv(_fixture_report()))))
    goog = next(r for r in rows if r["symbol"] == "GOOG")
    assert "rounding_tolerance" in goog["attempted_strategies"]
    assert "\n" not in goog["attempted_strategies"]


@pytest.mark.parametrize("fmt", ["json", "csv"])
def test_wm117_matched_positions_are_exported_too(fmt):
    """MATCHED needs no *action*, but Ops still reconciles counts. It must be in the export."""
    from export import render_csv, render_json

    output = render_json(_fixture_report()) if fmt == "json" else render_csv(_fixture_report())
    assert "AAPL" in output
