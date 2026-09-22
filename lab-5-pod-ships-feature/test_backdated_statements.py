"""Acceptance contract for WM-114: backdated statements. Seeded failing on purpose.

Lab 5 used to end with a markdown note *describing* this change's blast radius. It now ends
with the change **shipped**. The note is still a deliverable (it's how you plan the migration
and how you tell the advisor team what moved), but it is no longer the finish line.

The interesting thing about this suite is that roughly half of it tests that nothing changed:

  * `*_back_compat`: every existing caller, calling exactly as it does today, gets exactly
    today's answer. A migration that requires every call site to be updated in lockstep is not
    a migration, it's an outage.
  * `test_target_weights_signature_is_unchanged`: the one function in this package the change
    must NOT reach. This is the negative half of your impact map, made checkable. A migration
    that threads a parameter through everything is just as wrong as one that misses a caller,
    and it's much harder to argue with, because all the tests pass.

    python3 -m pytest test_backdated_statements.py -v

Imports live inside the test bodies so an unfinished call site fails its own tests rather than
breaking collection for the whole file.
"""

import inspect
import json
from pathlib import Path

import pytest

REFERENCE_DATA = Path(__file__).parent / "reference_data"

TODAY = "2026-07-24"
Q1_CLOSE = "2026-03-31"
Q2_CLOSE = "2026-06-30"

# 100 AAPL + 50 MSFT. Market value by date, from reference_data/price_history.json:
#   2026-07-24 (today): 100*150.00 + 50*300.00 = $30,000.00
#   2026-06-30:         100*142.50 + 50*288.00 = $28,650.00
#   2026-03-31:         100*128.00 + 50*265.50 = $26,075.00
PORTFOLIO = [{"symbol": "AAPL", "qty": 100}, {"symbol": "MSFT", "qty": 50}]
PROFILE = {"AAPL": 0.5, "MSFT": 0.5}

# A second household, also exactly 50/50 today, but AAPL and KO moved apart enough between
# Q1 close and today that a backdated run *does* generate trades:
#   2026-07-24: 62*150.00 = $9,300.00 | 150*62.00 = $9,300.00  -> 50.00% / 50.00%, no trades
#   2026-03-31: 62*128.00 = $7,936.00 | 150*58.00 = $8,700.00  -> 47.70% / 52.30%, 2.30% drift
SKEWED = [{"symbol": "AAPL", "qty": 62}, {"symbol": "KO", "qty": 150}]
SKEWED_PROFILE = {"AAPL": 0.5, "KO": 0.5}


# ══ The reference data and pricing.py agree ════════════════════════════════════


def test_price_history_today_matches_the_current_price_table():
    """The newest mark in each series must equal today's price.

    This is the invariant the whole back-compat story rests on: if the history's latest entry
    disagreed with `_PRICES`, then "backdate to today" and "don't backdate" would return
    different numbers, and every existing caller would quietly shift.
    """
    from pricing import get_price

    history = json.loads((REFERENCE_DATA / "price_history.json").read_text(encoding="utf-8"))
    assert history["as_of_today"] == TODAY
    for symbol, series in history["series"].items():
        assert series[TODAY] == get_price(symbol), f"{symbol}: history disagrees with _PRICES"


# ══ pricing.get_price: the function WM-114 actually changes ═══════════════════


def test_get_price_back_compat_no_as_of_date():
    from pricing import get_price

    assert get_price("AAPL") == 150.00
    assert get_price("MSFT") == 300.00


def test_get_price_returns_the_historical_mark():
    from pricing import get_price

    assert get_price("AAPL", as_of_date=Q1_CLOSE) == 128.00
    assert get_price("MSFT", as_of_date=Q2_CLOSE) == 288.00


def test_get_price_uses_the_most_recent_mark_at_or_before_the_date():
    """There is no mark for 2026-05-15. A statement as of that date uses the last known close.

    Interpolating, or reaching forward to the next mark, would put a price on a statement that
    did not exist on the day the statement claims to describe.
    """
    from pricing import get_price

    assert get_price("AAPL", as_of_date="2026-05-15") == 128.00


def test_get_price_before_the_first_mark_raises():
    from pricing import get_price

    with pytest.raises(KeyError):
        get_price("AAPL", as_of_date="2025-01-01")


def test_get_price_unknown_symbol_still_raises():
    from pricing import get_price

    with pytest.raises(KeyError):
        get_price("NOPE", as_of_date=Q1_CLOSE)


# ══ Direct callers ════════════════════════════════════════════════════════════


def test_advisory_fee_back_compat():
    from fees import advisory_fee

    assert advisory_fee(PORTFOLIO) == 300.00


def test_advisory_fee_backdated():
    from fees import advisory_fee

    assert advisory_fee(PORTFOLIO, as_of_date=Q1_CLOSE) == 260.75
    assert advisory_fee(PORTFOLIO, as_of_date=Q2_CLOSE) == 286.50


def test_current_weights_back_compat():
    from allocation import current_weights

    weights = current_weights(PORTFOLIO)
    assert weights["AAPL"] == pytest.approx(0.5)
    assert weights["MSFT"] == pytest.approx(0.5)


def test_current_weights_backdated():
    """At Q1 close the same share counts were a different split: 49.09% / 50.91%."""
    from allocation import current_weights

    weights = current_weights(PORTFOLIO, as_of_date=Q1_CLOSE)
    assert weights["AAPL"] == pytest.approx(12_800 / 26_075, rel=1e-6)
    assert weights["MSFT"] == pytest.approx(13_275 / 26_075, rel=1e-6)


def test_compute_trades_back_compat():
    from rebalance import compute_trades

    assert compute_trades(PORTFOLIO, PROFILE) == []
    assert compute_trades(SKEWED, SKEWED_PROFILE) == []


def test_compute_trades_backdated_sizes_against_historical_value():
    """This one catches a *partial* migration, which is why it's worth reading carefully.

    `compute_trades` reaches pricing twice: once directly, to size the dollar amounts, and once
    indirectly through `current_weights`. Forward `as_of_date` to only one of them and the
    weights come from Q1 while the portfolio total comes from today. The trades land on the
    right symbols, in the right direction, for the wrong amount ($427.11 instead of $382.02).
    Every other test in this file still passes when that happens.
    """
    from rebalance import compute_trades

    trades = compute_trades(SKEWED, SKEWED_PROFILE, as_of_date=Q1_CLOSE)
    assert {t["symbol"] for t in trades} == {"AAPL", "KO"}
    assert {t["action"] for t in trades} == {"BUY", "SELL"}
    for trade in trades:
        assert trade["dollar_amount"] == pytest.approx(382.02, abs=0.05), (
            "sized off the $16,636 Q1 value, not today's $18,600"
        )


# ══ Transitive callers, the ones a grep for "get_price(" never finds ══════════


def test_check_drift_back_compat():
    from drift import check_drift

    assert check_drift(PORTFOLIO, PROFILE) == []


def test_check_drift_accepts_as_of_date():
    """`check_drift` never calls `get_price`, and is fully exposed to this change anyway.

    It reaches pricing through `current_weights`. If it did not accept and forward an
    `as_of_date`, a backdated statement's drift section would silently describe *today*.
    """
    from drift import check_drift

    assert "as_of_date" in inspect.signature(check_drift).parameters
    assert check_drift(PORTFOLIO, PROFILE, as_of_date=Q1_CLOSE) == []


def test_build_statement_back_compat():
    from statements import build_statement

    statement = build_statement(PORTFOLIO, PROFILE)
    assert "$300.00" in statement


def test_build_statement_backdated_uses_historical_prices():
    from statements import build_statement

    statement = build_statement(PORTFOLIO, PROFILE, as_of_date=Q1_CLOSE)
    assert "$260.75" in statement
    assert "$300.00" not in statement, "a backdated statement must not leak today's fee"


def test_build_statement_states_the_as_of_date_on_its_face():
    """An advisor reissuing a statement must be able to tell which one they're holding.

    A backdated statement that looks identical to a current one is a compliance problem, not a
    formatting nit. This is the requirement WM-114's one-line ticket never mentions.
    """
    from statements import build_statement

    assert Q1_CLOSE in build_statement(PORTFOLIO, PROFILE, as_of_date=Q1_CLOSE)


# ══ The negative half of the impact map ═══════════════════════════════════════


def test_target_weights_signature_is_unchanged():
    """`target_weights` returns a static profile. It must NOT grow an `as_of_date`.

    This is the function `check_impact_note.py` expects your note to name as unaffected. Here
    it is as a test: threading the parameter through it would be over-migration: a change that
    looks thorough, passes every other test, and adds a parameter no caller can ever vary.
    """
    from allocation import target_weights

    assert list(inspect.signature(target_weights).parameters) == ["profile"]


def test_every_backdatable_entry_point_takes_as_of_date_as_a_keyword():
    """One consistent keyword name across the whole call graph, not `date`, not `asof`.

    A migration that spells the same concept three ways is how the next engineer introduces a
    bug: they pass `as_of=` to the one function that calls it `as_of_date=` and get today's
    price with no error.
    """
    from allocation import current_weights
    from drift import check_drift
    from fees import advisory_fee
    from pricing import get_price
    from rebalance import compute_trades
    from statements import build_statement

    for func in (get_price, current_weights, advisory_fee, compute_trades, check_drift,
                 build_statement):
        params = inspect.signature(func).parameters
        assert "as_of_date" in params, f"{func.__name__} is missing as_of_date"
        assert params["as_of_date"].default is None, (
            f"{func.__name__}: as_of_date must default to None so existing callers are untouched"
        )
