# Claude Code session guide — Lab 1 (standalone)

You (Claude Code) are pairing with a Wells Fargo Wealth Management engineer working through
a single, self-contained lab extracted from a larger Claude Code training course (Day 1,
Lab 1 of an 8-lab progression). This folder runs entirely on its own — no access to the rest
of the course repo, and no GitLab access, is required or expected.

## The task

This lab focuses on framing quality and a bounded bug-fix workflow. See [README.md](README.md)
for the full user story and the exact steps for improving the task frame and shipping a real
WM-101 fix.

## The shared standard: the five-ingredient task frame

Every non-trivial ask should read as an agentic task frame, not a bare prompt:

1. **Outcome** — the end state, not the keystrokes.
2. **Scope** — the concrete target and boundaries (which module/files; what not to touch).
3. **Verification** — how "done" is checked (here: `pytest`).
4. **Deliverable** — the reviewable artifact handed back (a diff summary, a report).
5. **Guardrails** — what NOT to do, and when to stop and ask.

## How to work in this folder

- **Domain is Wealth Management** — advisory fees, AUM tiers, breakpoint calculation.
  Keep examples in that world.
- **Files:**
  - `fees.py` — the module you'll edit.
  - `test_fees.py` — the verifiable target.
  - `.claude/skills/scoped-bugfix-flow/SKILL.md` — the reusable generic bug-fix flow.
  - `backlog/WM-101-fee-tier-bug.md` — the ticket this lab is based on.
- **Verify with `pytest`, not by eye:**
  ```bash
  python3 -m pytest test_fees.py -v   # this lab's tests
  python3 -m pytest -v                          # full suite, no regressions
  ```
- **Guardrails:**
  - Do not edit tests to fake a pass.
  - Keep the fix bounded to the fee logic in `fees.py`.
  - Preserve public behavior except for the actual breakpoint bug fix.
  - Negative AUM must still raise `ValueError`.

## No idea is ground truth

The tests are the verifiable target. A good task frame, a disciplined implementation, and
clear evidence are how you ship a trustworthy fix.
