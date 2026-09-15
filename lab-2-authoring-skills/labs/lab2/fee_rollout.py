"""Lab 2 fee rollout exercise.

This module mirrors the Lab 1 fee domain but introduces two analogous methods so learners can
apply one fix pattern repeatedly and decide when a specialized Skill is justified.

Both methods below intentionally start with cliff-rate behavior to create a verifiable failing
baseline in `test_fee_rollout.py`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeeTier:
    """One fee tier.

    `upper_aum` is inclusive. Use None for the top tier.
    `rate_bps` is basis points (100 bps = 1.00%).
    """

    upper_aum: int | None
    rate_bps: int


DEFAULT_FEE_TIERS: tuple[FeeTier, ...] = (
    FeeTier(upper_aum=1_000_000, rate_bps=100),
    FeeTier(upper_aum=5_000_000, rate_bps=80),
    FeeTier(upper_aum=None, rate_bps=60),
)


def annual_progressive_fee(aum: int, tiers: tuple[FeeTier, ...] = DEFAULT_FEE_TIERS) -> float:
    """Progressive fee calculator used by the quarterly rollout method.

    The current implementation is intentionally incorrect (cliff-rate) so learners can implement
    the progressive logic and then decide whether to reuse the fix pattern for `monthly_advisory_fee`.
    """
    if aum < 0:
        raise ValueError("AUM cannot be negative")

    for tier in tiers:
        if tier.upper_aum is None or aum <= tier.upper_aum:
            return round(aum * (tier.rate_bps / 10_000), 2)

    raise ValueError("AUM exceeds all configured fee tiers")


def quarterly_advisory_fee(aum: int, tiers: tuple[FeeTier, ...] = DEFAULT_FEE_TIERS) -> float:
    """Quarterly fee derived from annual fee logic."""
    return round(annual_progressive_fee(aum, tiers) / 4, 2)


def _annual_cliff_rate(aum: int, tiers: tuple[FeeTier, ...] = DEFAULT_FEE_TIERS) -> float:
    """Progressive fee calculator used by the monthly rollout method.

    Independent from `annual_progressive_fee` — intentionally duplicates the same cliff-rate bug
    so a fix to the quarterly method does not also fix this one.
    """
    if aum < 0:
        raise ValueError("AUM cannot be negative")

    for tier in tiers:
        if tier.upper_aum is None or aum <= tier.upper_aum:
            return round(aum * (tier.rate_bps / 10_000), 2)

    raise ValueError("AUM exceeds all configured fee tiers")


def monthly_advisory_fee(aum: int, tiers: tuple[FeeTier, ...] = DEFAULT_FEE_TIERS) -> float:
    """Monthly fee derived from annual fee logic."""
    return round(_annual_cliff_rate(aum, tiers) / 12, 2)
