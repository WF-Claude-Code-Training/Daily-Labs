# WM-202 — Fee logic rollout across billing cadences

## User story

As a WM platform lead, I want fee calculations standardized across billing cadences so that
quarterly and monthly fees follow the same progressive-tier business rules.

## Problem

Both `quarterly_advisory_fee()` and `monthly_advisory_fee()` are currently implemented as
cliff-rate pricing rather than progressive-tier pricing. This creates inconsistent fees for
clients across similar AUM levels and billing cadences.

## Acceptance criteria

- Quarterly advisory fees use progressive marginal tiers.
- Monthly advisory fees use the same progressive marginal tiers.
- Breakpoints at $1,000,000 and $5,000,000 behave correctly.
- Fees remain monotonic as AUM increases.
- Negative AUM values are rejected.
- Existing public method signatures remain unchanged.

## Notes

This is a rollout exercise: fix the quarterly method first with a generic reusable skill, then
reuse the same discipline for the monthly method with a fee-specific skill.
