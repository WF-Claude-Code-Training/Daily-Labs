"""Verifiable target for Lab 2 Option C fee-standardization rollout.

These tests are intentionally expected to fail before learners implement progressive-tier logic
in `fee_rollout.py`. They support a two-pass workflow:
- Pass 1 focus: `-k quarterly`
- Pass 2 focus: `-k monthly`
"""

from __future__ import annotations

import pytest

from fee_rollout import monthly_advisory_fee, quarterly_advisory_fee


def _expected_annual_progressive_fee(aum: int) -> float:
    if aum < 0:
        raise ValueError("AUM cannot be negative")

    if aum <= 1_000_000:
        return round(aum * 0.01, 2)
    if aum <= 5_000_000:
        return round(10_000.00 + (aum - 1_000_000) * 0.008, 2)
    return round(42_000.00 + (aum - 5_000_000) * 0.006, 2)


def _expected_quarterly_fee(aum: int) -> float:
    return round(_expected_annual_progressive_fee(aum) / 4, 2)


def _expected_monthly_fee(aum: int) -> float:
    return round(_expected_annual_progressive_fee(aum) / 12, 2)


@pytest.mark.parametrize(
    "aum,expected",
    [
        (0, 0.00),
        (1_000_000, 2_500.00),
        (1_000_001, 2_500.00),
        (5_000_000, 10_500.00),
        (5_000_001, 10_500.00),
        (5_250_000, 10_875.00),
    ],
)
def test_quarterly_breakpoints_and_tiers(aum: int, expected: float) -> None:
    assert quarterly_advisory_fee(aum) == expected


@pytest.mark.parametrize(
    "aum,expected",
    [
        (0, 0.00),
        (1_000_000, 833.33),
        (1_000_001, 833.33),
        (5_000_000, 3_500.00),
        (5_000_001, 3_500.00),
        (5_250_000, 3_625.00),
    ],
)
def test_monthly_breakpoints_and_tiers(aum: int, expected: float) -> None:
    assert monthly_advisory_fee(aum) == expected


@pytest.mark.parametrize("aum", [250_000, 999_999, 1_750_000, 4_250_000, 7_500_000])
def test_quarterly_matches_progressive_formula(aum: int) -> None:
    assert quarterly_advisory_fee(aum) == _expected_quarterly_fee(aum)


@pytest.mark.parametrize("aum", [250_000, 999_999, 1_750_000, 4_250_000, 7_500_000])
def test_monthly_matches_progressive_formula(aum: int) -> None:
    assert monthly_advisory_fee(aum) == _expected_monthly_fee(aum)


def test_quarterly_monotonic_non_decreasing() -> None:
    aums = [0, 1, 100_000, 999_999, 1_000_000, 1_000_001, 2_500_000, 5_000_000, 8_000_000]
    fees = [quarterly_advisory_fee(aum) for aum in aums]
    assert fees == sorted(fees)


def test_monthly_monotonic_non_decreasing() -> None:
    aums = [0, 1, 100_000, 999_999, 1_000_000, 1_000_001, 2_500_000, 5_000_000, 8_000_000]
    fees = [monthly_advisory_fee(aum) for aum in aums]
    assert fees == sorted(fees)


@pytest.mark.parametrize("aum", [-1, -100, -1_000_000])
def test_quarterly_negative_aum_rejected(aum: int) -> None:
    with pytest.raises(ValueError):
        quarterly_advisory_fee(aum)


@pytest.mark.parametrize("aum", [-1, -100, -1_000_000])
def test_monthly_negative_aum_rejected(aum: int) -> None:
    with pytest.raises(ValueError):
        monthly_advisory_fee(aum)
