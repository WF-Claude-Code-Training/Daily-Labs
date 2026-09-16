# Claude Code session guide — Lab 2 (standalone)

You (Claude Code) are pairing with a Wells Fargo Wealth Management engineer working through
a single, self-contained lab extracted from a larger Claude Code training course (Day 1,
Lab 2 of an 8-lab progression). This folder runs entirely on its own — no access to the rest
of the course repo, and no GitLab access, is required or expected.

## The task

This lab is a two-pass fee logic rollout. See [README.md](README.md) for the full user story,
step-by-step flow, and the difference between a generic reusable Skill and a homegrown
fee-specific Skill.

## The shared standard: the five-ingredient task frame

Every non-trivial ask should read as an agentic task frame, not a bare prompt:

1. **Outcome** — the end state, not the keystrokes.
2. **Scope** — the concrete target and boundaries (which module/files; what not to touch).
3. **Verification** — how "done" is checked (here: `pytest`).
4. **Deliverable** — the reviewable artifact handed back (a diff summary, a report).
5. **Guardrails** — what NOT to do, and when to stop and ask.

## How to work in this folder

- **Domain is Wealth Management** — portfolios, advisory fees, AUM tiers, billing cadence.
  Keep examples in that world.
- **Files:**
  - `fee_rollout.py` — the module you'll edit. Both methods start with cliff-rate
    behavior intentionally, so the failing baseline is real.
  - `test_fee_rollout.py` — the verifiable target.
  - `.claude/skills/scoped-bugfix-flow/SKILL.md` — the reusable generic bug-fix flow to use in
    Pass 1.
  - `backlog/WM-202-fee-rollout.md` — the ticket this lab is based on.
- **Verify with `pytest`, not by eye:**
  ```bash
  python3 -m pytest test_fee_rollout.py -v   # this lab's tests
  python3 -m pytest -v                                 # full suite, no regressions
  ```
- **Guardrails:**
  - Do not edit tests to fake a pass.
  - Preserve public method signatures.
  - Keep the fix bounded to the fee logic in `fee_rollout.py` unless the task says otherwise.
  - In Pass 2, add a custom Skill only for the repeated workflow pattern — don't let the
    lab drift into a broad rewrite.

## No idea is ground truth

The tests are the verifiable target. A good task frame, a disciplined implementation, and
clear evidence are how you prove the fix.
