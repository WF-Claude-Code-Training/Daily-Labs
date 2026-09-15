"""Reconciliation triage for portfolio positions (WM-106).

A nightly reconciliation compares our internal *book* of positions against the *custodian
file*. The naive ask (WM-106) is "compare them and print the mismatches" — but taken literally
that dumps every discrepancy on an advisor, most of which are explainable noise. Positions
disagree for two very different reasons:

- **Explainable differences** a known normalization *strategy* accounts for: a price off by a
  rounding tolerance, a settlement date off by the usual one-day offset, a price expressed in a
  different currency.
- **Genuine breaks** no strategy explains: a real quantity gap, or a position missing on one
  side entirely — these must be **escalated** to a human, never guessed at or silently dropped.

`reconcile_positions` is the core of this: for each position it works through the known
strategies in order — Read the two sides, Decide which strategy to try, Act (apply it), Observe
whether it explains the difference — and returns a per-position verdict of `MATCHED`,
`RESOLVED` (with the strategy that explained it), or `ESCALATED` (with the strategies it tried
and a risk level). A **dollar-risk threshold** overrides everything: a position whose notional
exposure is large escalates for human review *even if* a strategy appears to explain it, because
a big number is not something you auto-resolve on a pattern match.

Everything here is deterministic and offline — no API key, no network call, nothing to mock.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# A price difference at or below this many dollars-per-share is sub-cent rounding noise.
PRICE_ROUNDING_TOLERANCE = 0.01
# Settlement dates this many calendar days apart are the normal T+1 settlement offset.
SETTLEMENT_OFFSET_DAYS = 1
# Known FX rates (custodian price / book price) the currency strategy will accept.
KNOWN_FX_RATES = (1.08, 1.27, 0.79, 0.92)
FX_TOLERANCE = 0.01
# Known forward stock-split ratios (custodian qty / book qty) — Lab 4's exercise strategy.
KNOWN_SPLIT_RATIOS = (2, 3, 4)
# Relative tolerance on notional value (qty * price) across a split.
SPLIT_NOTIONAL_TOLERANCE = 0.01
# A position whose notional exposure is at or above this escalates regardless of any strategy.
DOLLAR_RISK_THRESHOLD = 1_000_000.0

# Status values (plain strings so callers can assert `status == "RESOLVED"` per the spec).
MATCHED = "MATCHED"
RESOLVED = "RESOLVED"
ESCALATED = "ESCALATED"

# Risk levels for escalations.
LOW, MEDIUM, HIGH = "LOW", "MEDIUM", "HIGH"

Position = dict  # a position is a plain dict: {"symbol", "qty", "price"?, "settle_date"?}


@dataclass
class ReconResult:
    """The reconciliation verdict for a single symbol."""

    symbol: str
    status: str  # MATCHED | RESOLVED | ESCALATED
    strategy: str | None = None
    risk_level: str | None = None
    attempted_strategies: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass
class TriageResult:
    """The whole run, shaped for the report: matched, resolved, escalated + an audit trail."""

    matched: list[ReconResult] = field(default_factory=list)
    resolved: list[ReconResult] = field(default_factory=list)
    escalated: list[ReconResult] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)

    @property
    def results(self) -> list[ReconResult]:
        return [*self.matched, *self.resolved, *self.escalated]


# ── Loading ────────────────────────────────────────────────────────────────


def load_positions(path: str | Path) -> list[Position]:
    """Read a CSV of ``symbol,qty[,price][,settle_date]`` into position dicts.

    A header row is required (its column names drive parsing). `qty`/`price` are cast to
    numbers; `settle_date` (ISO ``YYYY-MM-DD``) is kept as a string. Blank cells are dropped so
    a position simply lacks that field.
    """
    positions: list[Position] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pos: Position = {}
            for key, raw in row.items():
                key = (key or "").strip()
                value = (raw or "").strip()
                if not key or value == "":
                    continue
                if key in ("qty", "price"):
                    pos[key] = float(value)
                else:
                    pos[key] = value
            if pos.get("symbol"):
                positions.append(pos)
    return positions


# ── Dollar-risk ──────────────────────────────────────────────────────────────


def dollar_risk(*sides: Position | None) -> float:
    """Notional exposure of a position: the largest ``|qty| * price`` across the sides given."""
    worst = 0.0
    for side in sides:
        if not side:
            continue
        qty = abs(float(side.get("qty", 0) or 0))
        price = float(side.get("price", 0) or 0)
        worst = max(worst, qty * price)
    return worst


# ── Normalization strategies: does this one explain the difference? ────────────


def _fields_equal(book: Position, custodian: Position, *keys: str) -> bool:
    return all(book.get(k) == custodian.get(k) for k in keys)


def rounding_tolerance(book: Position, custodian: Position) -> bool:
    """Explains a difference that is only a small price rounding delta (qty/date agree)."""
    if not _fields_equal(book, custodian, "qty", "settle_date"):
        return False
    bp, cp = book.get("price"), custodian.get("price")
    if bp is None or cp is None or bp == cp:
        return False
    return abs(bp - cp) <= PRICE_ROUNDING_TOLERANCE


def settlement_date_offset(book: Position, custodian: Position) -> bool:
    """Explains a difference that is only the usual T+1 settlement-date offset."""
    if not _fields_equal(book, custodian, "qty", "price"):
        return False
    bd, cd = book.get("settle_date"), custodian.get("settle_date")
    if not bd or not cd or bd == cd:
        return False
    try:
        delta = abs((date.fromisoformat(bd) - date.fromisoformat(cd)).days)
    except ValueError:
        return False
    return delta <= SETTLEMENT_OFFSET_DAYS


def currency_conversion(book: Position, custodian: Position) -> bool:
    """Explains a price difference that matches a known FX conversion (qty/date agree)."""
    if not _fields_equal(book, custodian, "qty", "settle_date"):
        return False
    bp, cp = book.get("price"), custodian.get("price")
    if not bp or not cp or bp == cp:
        return False
    ratio = cp / bp
    return any(abs(ratio - rate) <= FX_TOLERANCE for rate in KNOWN_FX_RATES)


def stock_split_adjustment(book: Position, custodian: Position) -> bool:
    """LAB 4 EXERCISE — not yet implemented; see README.md Part 2.

    Should explain a qty/price difference caused by a known forward stock split (custodian
    qty = book qty * ratio, custodian price = book price / ratio) where notional value
    (qty * price) is unchanged within `SPLIT_NOTIONAL_TOLERANCE`, for a known `ratio` in
    `KNOWN_SPLIT_RATIOS`, with settle_date agreeing on both sides.
    """
    return False  # TODO: implement, then add this strategy to DEFAULT_STRATEGIES below


@dataclass(frozen=True)
class Strategy:
    name: str
    explains: "object"  # Callable[[Position, Position], bool]


# Ordered: strategies are tried in this sequence and the first one that explains the
# difference wins. LAB 4 EXERCISE: once stock_split_adjustment is implemented, add it here.
DEFAULT_STRATEGIES: tuple[Strategy, ...] = (
    Strategy("rounding_tolerance", rounding_tolerance),
    Strategy("settlement_date_offset", settlement_date_offset),
    Strategy("currency_conversion", currency_conversion),
)


# ── The core: reconcile every position, resolve-or-escalate ────────────────────


def _positions_equal(book: Position, custodian: Position) -> bool:
    keys = (set(book) | set(custodian)) - {"symbol"}
    return all(book.get(k) == custodian.get(k) for k in keys)


def reconcile_positions(
    book: list[Position],
    custodian: list[Position],
    *,
    strategies: tuple[Strategy, ...] = DEFAULT_STRATEGIES,
    dollar_threshold: float = DOLLAR_RISK_THRESHOLD,
) -> list[ReconResult]:
    """Reconcile book vs custodian, returning one verdict per symbol.

    Per position, this works through the known strategies (Read → Decide → Act → Observe):
      - identical on both sides                         -> MATCHED
      - a strategy explains the difference, risk small  -> RESOLVED (strategy recorded)
      - notional exposure >= dollar_threshold           -> ESCALATED (HIGH), even if a strategy
        would have explained it — a big number is never auto-resolved on a pattern match
      - no strategy explains it, or a side is missing   -> ESCALATED (strategies tried recorded)

    Every input symbol appears in exactly one verdict — nothing is silently dropped.
    """
    book_by_symbol = {p["symbol"]: p for p in book}
    cust_by_symbol = {p["symbol"]: p for p in custodian}
    results: list[ReconResult] = []

    for symbol in sorted(book_by_symbol.keys() | cust_by_symbol.keys()):
        b = book_by_symbol.get(symbol)
        c = cust_by_symbol.get(symbol)
        risk = dollar_risk(b, c)
        risk_level = HIGH if risk >= dollar_threshold else MEDIUM

        # Missing on one side — a genuine break, escalate with no strategy attempted.
        if b is None or c is None:
            where = "custodian file" if b is None else "book"
            results.append(ReconResult(
                symbol=symbol, status=ESCALATED, risk_level=risk_level,
                attempted_strategies=[],
                detail=f"{symbol} missing from the {where} — position exists on one side only",
            ))
            continue

        # Identical on every shared field — nothing to do.
        if _positions_equal(b, c):
            results.append(ReconResult(symbol=symbol, status=MATCHED))
            continue

        # Decide → Act → Observe: try each strategy until one explains the difference.
        attempted: list[str] = []
        explained_by: str | None = None
        for strategy in strategies:
            attempted.append(strategy.name)
            if strategy.explains(b, c):
                explained_by = strategy.name
                break

        # Dollar-risk override: large exposure escalates regardless of an explanation.
        if risk >= dollar_threshold:
            results.append(ReconResult(
                symbol=symbol, status=ESCALATED, risk_level=HIGH,
                attempted_strategies=attempted,
                detail=(f"{symbol} notional ${risk:,.0f} exceeds the "
                        f"${dollar_threshold:,.0f} auto-resolve threshold — human review required"),
            ))
        elif explained_by is not None:
            results.append(ReconResult(
                symbol=symbol, status=RESOLVED, strategy=explained_by,
                attempted_strategies=attempted,
                detail=f"{symbol} difference explained by {explained_by}",
            ))
        else:
            results.append(ReconResult(
                symbol=symbol, status=ESCALATED, risk_level=risk_level,
                attempted_strategies=attempted,
                detail=f"{symbol} difference not explained by any known strategy",
            ))

    return results


# ── The report every consumer (CLI, tests) speaks to ────────────────────────────


def _file_result(result: TriageResult, r: ReconResult) -> None:
    if r.status == MATCHED:
        result.matched.append(r)
    elif r.status == RESOLVED:
        result.resolved.append(r)
        result.actions.append(f"{r.symbol}: RESOLVED via {r.strategy}")
    else:
        result.escalated.append(r)
        result.actions.append(
            f"{r.symbol}: ESCALATED ({r.risk_level}) — "
            f"tried [{', '.join(r.attempted_strategies) or 'none'}]"
        )


def triage(
    book: list[Position],
    custodian: list[Position],
    *,
    strategies: tuple[Strategy, ...] = DEFAULT_STRATEGIES,
    dollar_threshold: float = DOLLAR_RISK_THRESHOLD,
) -> TriageResult:
    """Run `reconcile_positions` and group the verdicts into a report with an audit trail."""
    results = reconcile_positions(
        book, custodian, strategies=strategies, dollar_threshold=dollar_threshold)
    triage_result = TriageResult()
    for r in results:
        _file_result(triage_result, r)
    return triage_result
