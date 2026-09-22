"""Acceptance contract for WM-115: ops-loadable split reference data. Seeded failing.

This is the ticket you run through the pod in Part 4, and it is the only definition of "done"
you get for it. No pasted prompts: read a test, and you know exactly what the code owes you.

`test_reconcile.py` is the *existing* contract and must stay green throughout. One test below
exists only to pin that down: a change that turns a test there red is a regression, not
progress, and `contract-reviewer` is meant to catch it even when the suite looks fine.

    python3 -m pytest test_reconcile_epic.py -v

Each import happens *inside* a test body rather than at module scope, deliberately: an
unimplemented function fails its own tests instead of breaking collection for the whole file,
so the failure count stays a usable measure of how much is left.

WM-116 and WM-117 live in `test_reconcile_stretch.py`, optional, and not required for this
lab's Definition of Done.
"""

from pathlib import Path

REFERENCE_DATA = Path(__file__).parent / "reference_data"

# The ORCL rows from the fixtures: a 3-for-2 forward split (ratio 1.5), notional unchanged at
# $9,000 on both sides. Escalates today because 1.5 is not in KNOWN_SPLIT_RATIOS.
ORCL_BOOK = {"symbol": "ORCL", "qty": 100, "price": 90.00, "settle_date": "2026-07-24"}
ORCL_CUSTODIAN = {"symbol": "ORCL", "qty": 150, "price": 60.00, "settle_date": "2026-07-24"}


# ══ WM-115: Ops-loadable split-ratio reference data ════════════════════════════
#
# Ops must be able to add a newly announced split ratio without a code change, a deploy, or an
# engineer. Today KNOWN_SPLIT_RATIOS is a hardcoded tuple, so ORCL escalates every single night
# until someone ships a release.


def test_wm115_load_split_ratios_reads_the_reference_file():
    from reconcile import load_split_ratios

    ratios = load_split_ratios(REFERENCE_DATA / "split_ratios.json")
    assert 1.5 in ratios, "the ORCL 3-for-2 ratio Ops loaded must come through"
    for baseline in (2.0, 3.0, 4.0):
        assert baseline in ratios, f"{baseline} was already known and must not be lost"


def test_wm115_missing_reference_file_falls_back_instead_of_crashing():
    """A missing or unreadable reference file must not take down the nightly run.

    Degrading to the compiled-in defaults is correct: you reconcile with what you know and
    ORCL escalates, exactly as it does today. Raising here would mean a bad Ops deploy stops
    reconciliation for every household.
    """
    from reconcile import KNOWN_SPLIT_RATIOS, load_split_ratios

    ratios = load_split_ratios(REFERENCE_DATA / "does_not_exist.json")
    assert tuple(ratios) == tuple(KNOWN_SPLIT_RATIOS)


def test_wm115_build_strategies_binds_the_loaded_ratios():
    """`build_strategies` is the single source of truth for the strategy list.

    It must *construct* the list, not append to `DEFAULT_STRATEGIES`, otherwise once
    `stock_split_adjustment` is wired into the defaults (the warm-up ticket) you get it twice,
    one copy bound to the ops-loaded ratios and one to the compiled-in tuple, and which one
    wins depends on ordering. `DEFAULT_STRATEGIES` stays exactly as it is, for callers that
    already use it.
    """
    from reconcile import build_strategies, load_split_ratios

    ratios = load_split_ratios(REFERENCE_DATA / "split_ratios.json")
    names = [s.name for s in build_strategies(split_ratios=ratios)]
    assert names == [
        "rounding_tolerance",
        "settlement_date_offset",
        "currency_conversion",
        "stock_split_adjustment",
    ], "order matters: the cheap checks stay first, the split strategy goes last"
    assert len(names) == len(set(names)), "no strategy may appear twice"


def test_wm115_orcl_resolves_once_ops_loads_the_ratio():
    """The payoff: the escalation Lab 4 taught you was *correct* clears via a data change."""
    from reconcile import build_strategies, load_split_ratios, reconcile_positions

    strategies = build_strategies(split_ratios=load_split_ratios(REFERENCE_DATA / "split_ratios.json"))
    results = reconcile_positions([ORCL_BOOK], [ORCL_CUSTODIAN], strategies=strategies)
    assert results[0].status == "RESOLVED"
    assert results[0].strategy == "stock_split_adjustment"


def test_wm115_orcl_still_escalates_on_the_compiled_in_defaults():
    """back-compat: loading reference data is opt-in; the default path must not change.

    A caller who never passes reference data still gets today's behavior. Widening the default
    would silently start auto-resolving 3-for-2 splits for every existing caller.
    """
    from reconcile import build_strategies, reconcile_positions

    results = reconcile_positions([ORCL_BOOK], [ORCL_CUSTODIAN], strategies=build_strategies())
    assert results[0].status == "ESCALATED"


def test_wm115_an_unlisted_ratio_is_never_guessed():
    """A 5-for-1 split is not in the reference file: it must escalate, not pattern-match."""
    from reconcile import build_strategies, load_split_ratios, reconcile_positions

    book = [{"symbol": "AMD", "qty": 100, "price": 500.00, "settle_date": "2026-07-24"}]
    custodian = [{"symbol": "AMD", "qty": 500, "price": 100.00, "settle_date": "2026-07-24"}]
    strategies = build_strategies(split_ratios=load_split_ratios(REFERENCE_DATA / "split_ratios.json"))
    results = reconcile_positions(book, custodian, strategies=strategies)
    assert results[0].status == "ESCALATED"
