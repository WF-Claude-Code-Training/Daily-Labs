"""Tests for WM-101 tiered advisory-fee calculations."""

import pytest

from fees import annual_advisory_fee


def test_fee_at_first_breakpoint_is_exact():
    assert annual_advisory_fee(1_000_000) == 10_000.00


def test_fee_just_above_first_breakpoint_uses_second_tier_rate():
    assert annual_advisory_fee(1_000_001) == 10_000.01


def test_fee_at_second_breakpoint_is_progressive_sum():
    assert annual_advisory_fee(5_000_000) == 42_000.00


def test_fee_above_second_breakpoint_uses_top_tier_rate():
    assert annual_advisory_fee(5_250_000) == 43_500.00


def test_negative_aum_rejected():
    with pytest.raises(ValueError):
        annual_advisory_fee(-1)
