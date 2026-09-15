"""Tiered advisory-fee calculations for the Lab 1 WM-101 exercise.

This module intentionally stays small and deterministic so participants can focus on
framing and implementation workflow, not domain complexity.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeeTier:
    """One advisory-fee tier.

    `upper_aum` is inclusive. Use `None` for the top tier with no ceiling.
    `rate_bps` is basis points (100 bps = 1.00%).
    """

    upper_aum: int | None
    rate_bps: int


DEFAULT_FEE_TIERS: tuple[FeeTier, ...] = (
    FeeTier(upper_aum=1_000_000, rate_bps=100),
    FeeTier(upper_aum=5_000_000, rate_bps=80),
    FeeTier(upper_aum=None, rate_bps=60),
)


def annual_advisory_fee(aum: int, tiers: tuple[FeeTier, ...] = DEFAULT_FEE_TIERS) -> float:
    """Calculate annual advisory fee using progressive tier pricing.

    Example with default tiers:
    - First $1,000,000 at 1.00%
    - Next $4,000,000 at 0.80%
    - Remainder at 0.60%
    """
    if aum < 0:
        raise ValueError("AUM cannot be negative")

    total_fee = 0.0
    previous_upper = 0

    for tier in tiers:
        if tier.upper_aum is None:
            applicable_amount = max(aum - previous_upper, 0)
            total_fee += applicable_amount * (tier.rate_bps / 10_000)
            return round(total_fee, 2)

        if aum <= tier.upper_aum:
            applicable_amount = aum - previous_upper
            total_fee += applicable_amount * (tier.rate_bps / 10_000)
            return round(total_fee, 2)

        applicable_amount = tier.upper_aum - previous_upper
        total_fee += applicable_amount * (tier.rate_bps / 10_000)
        previous_upper = tier.upper_aum

    raise ValueError("AUM exceeds all configured fee tiers")
