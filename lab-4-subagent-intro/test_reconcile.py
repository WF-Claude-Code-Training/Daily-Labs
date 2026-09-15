"""Tests for WM-106 reconciliation triage — the verifiable target for Lab 4.

Deterministic and offline: the whole suite runs with no API key and no network access.

The first five tests are the acceptance criteria from the ticket reframing (match /
auto-resolve / escalate / dollar-risk override); the rest cover the report and fixtures.
"""

from pathlib import Path

from reconcile import (
    DEFAULT_STRATEGIES,
    dollar_risk,
    load_positions,
    reconcile_positions,
    triage,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ── The acceptance criteria from the ticket reframing ─────────────────────────────


def test_exact_match_needs_no_action():
    book = [{"symbol": "AAPL", "qty": 100, "price": 150.00}]
    custodian = [{"symbol": "AAPL", "qty": 100, "price": 150.00}]
    results = reconcile_positions(book, custodian)
    assert results[0].status == "MATCHED"


def test_rounding_mismatch_auto_resolves():
    book = [{"symbol": "AAPL", "qty": 100, "price": 150.001}]
    custodian = [{"symbol": "AAPL", "qty": 100, "price": 150.00}]
    results = reconcile_positions(book, custodian)
    assert results[0].status == "RESOLVED"
    assert results[0].strategy == "rounding_tolerance"


def test_settlement_date_offset_auto_resolves():
    book = [{"symbol": "MSFT", "qty": 50, "settle_date": "2026-07-24"}]
    custodian = [{"symbol": "MSFT", "qty": 50, "settle_date": "2026-07-25"}]
    results = reconcile_positions(book, custodian)
    assert results[0].status == "RESOLVED"
    assert results[0].strategy == "settlement_date_offset"


def test_unexplained_quantity_mismatch_escalates():
    """No known strategy explains a raw quantity mismatch — must escalate, not guess."""
    book = [{"symbol": "GOOG", "qty": 200, "price": 140.00}]
    custodian = [{"symbol": "GOOG", "qty": 150, "price": 140.00}]
    results = reconcile_positions(book, custodian)
    assert results[0].status == "ESCALATED"
    assert results[0].risk_level in ("MEDIUM", "HIGH")
    assert results[0].attempted_strategies  # proof it wasn't a silent skip


def test_high_dollar_mismatch_always_escalates_even_if_pattern_matches():
    """Risk threshold overrides pattern-matching — large dollar amounts escalate regardless."""
    book = [{"symbol": "TSLA", "qty": 10000, "price": 250.001}]
    custodian = [{"symbol": "TSLA", "qty": 10000, "price": 250.00}]
    results = reconcile_positions(book, custodian)
    assert results[0].status == "ESCALATED"  # dollar delta too large to auto-resolve


# ── Additional coverage: strategies, currency, missing, dollar-risk ────────────


def test_currency_conversion_auto_resolves():
    book = [{"symbol": "SAP", "qty": 200, "price": 100.00}]
    custodian = [{"symbol": "SAP", "qty": 200, "price": 108.00}]  # ratio 1.08 (a known FX rate)
    results = reconcile_positions(book, custodian)
    assert results[0].status == "RESOLVED"
    assert results[0].strategy == "currency_conversion"


# ── LAB 4 EXERCISE — this is the verifiable target for Part 2 (currently failing) ──────────


def test_stock_split_auto_resolves():
    """A 2-for-1 split: custodian qty doubles, price halves, notional unchanged.

    Fails until `stock_split_adjustment` in `reconcile.py` is implemented and added to
    `DEFAULT_STRATEGIES` — see README.md Part 2.
    """
    book = [{"symbol": "BRKB", "qty": 100, "price": 200.00, "settle_date": "2026-07-24"}]
    custodian = [{"symbol": "BRKB", "qty": 200, "price": 100.00, "settle_date": "2026-07-24"}]
    results = reconcile_positions(book, custodian)
    assert results[0].status == "RESOLVED"
    assert results[0].strategy == "stock_split_adjustment"


def test_missing_position_escalates_and_is_not_dropped():
    book = [{"symbol": "NVDA", "qty": 75, "price": 120.00}]
    custodian = []
    results = reconcile_positions(book, custodian)
    assert len(results) == 1  # nothing silently dropped
    assert results[0].status == "ESCALATED"
    assert results[0].attempted_strategies == []


def test_high_dollar_escalation_is_flagged_high_risk():
    book = [{"symbol": "TSLA", "qty": 10000, "price": 250.001}]
    custodian = [{"symbol": "TSLA", "qty": 10000, "price": 250.00}]
    results = reconcile_positions(book, custodian)
    assert results[0].risk_level == "HIGH"


def test_dollar_risk_is_notional_exposure():
    assert dollar_risk({"qty": 10000, "price": 250.0}) == 2_500_000.0
    assert dollar_risk({"qty": 50}, None) == 0.0  # no price -> no notional


def test_every_input_symbol_appears_exactly_once():
    book = load_positions(FIXTURES / "book_positions.csv")
    custodian = load_positions(FIXTURES / "custodian_file.csv")
    results = reconcile_positions(book, custodian)
    symbols_in = {p["symbol"] for p in book} | {p["symbol"] for p in custodian}
    symbols_out = [r.symbol for r in results]
    assert sorted(symbols_out) == sorted(symbols_in)
    assert len(symbols_out) == len(set(symbols_out))  # no duplicates, no drops


# ── The report ──────────────────────────────────────────────────────────────


def test_triage_groups_verdicts_over_the_fixtures():
    book = load_positions(FIXTURES / "book_positions.csv")
    custodian = load_positions(FIXTURES / "custodian_file.csv")
    result = triage(book, custodian)

    matched = {r.symbol for r in result.matched}
    resolved = {r.symbol: r.strategy for r in result.resolved}
    escalated = {r.symbol for r in result.escalated}

    assert matched == {"AAPL"}
    assert resolved == {
        "KO": "rounding_tolerance",
        "MSFT": "settlement_date_offset",
        "SAP": "currency_conversion",
    }
    assert escalated == {"GOOG", "TSLA", "NVDA", "ORCL"}


def test_triage_records_an_action_per_non_matched_verdict():
    book = load_positions(FIXTURES / "book_positions.csv")
    custodian = load_positions(FIXTURES / "custodian_file.csv")
    result = triage(book, custodian)
    # 3 resolved + 4 escalated = 7 actions in the audit trail; MATCHED needs no action.
    assert len(result.actions) == 7


def test_default_strategies_are_the_three_known_normalizations():
    assert [s.name for s in DEFAULT_STRATEGIES] == [
        "rounding_tolerance",
        "settlement_date_offset",
        "currency_conversion",
    ]
