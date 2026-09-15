# Claude Code session guide — Lab 3 (standalone)

You (Claude Code) are pairing with a Wells Fargo Wealth Management engineer working through
a single, self-contained lab extracted from a larger Claude Code training course (Day 1,
Lab 3 of an 8-lab progression). This folder runs entirely on its own — no access to the rest
of the course repo, and no GitLab access, is required or expected.

## The task

WM-110 — drift alert false positives. See [README.md](README.md) for the full user story
and step-by-step lab flow (Plan mode, then test-driven delivery).

## The shared standard: the five-ingredient task frame

Every non-trivial ask should read as an agentic task frame, not a bare prompt:

1. **Outcome** — the end state, not the keystrokes.
2. **Scope** — the concrete target and boundaries (which module/files; what not to touch).
3. **Verification** — how "done" is checked (here: `pytest`).
4. **Deliverable** — the reviewable artifact handed back (a diff summary, a report).
5. **Guardrails** — what NOT to do, and when to stop and ask.

## How to work in this folder

- **Domain is Wealth Management** — portfolios, drift from target allocation, advisor
  alerting. Keep examples in that world.
- **Files:**
  - `labs/lab3/drift.py` — the module you'll edit (starter code, no hysteresis yet).
  - `labs/lab3/test_drift.py` — the verifiable target. One test fails on purpose; that
    failing test *is* the spec.
  - `backlog/WM-110-drift-alert.md` — the ticket this lab is based on.
- **Use Plan mode** before editing `drift.py`. Propose a plan, get it reviewed/approved, then
  implement — see README.md Parts 2-3.
- **Verify with `pytest`, not by eye:**
  ```bash
  python3 -m pytest labs/lab3/test_drift.py -v   # this lab's tests
  python3 -m pytest -v                            # full suite, no regressions
  ```
- **Guardrails:**
  - Don't edit `test_drift.py`'s existing 4 tests to make a fix "pass" — fix `drift.py`
    instead.
  - Preserve existing behavior (`min_duration_minutes=0` still alerts immediately).
  - In Part 6, you write new tests yourself — don't touch the tests that lock in Part 1-5's
    behavior.
  - An implementation that always alerts (or never alerts) is not a fix — both
    `test_no_alert_for_brief_spike` and `test_alert_after_sustained_breach` must pass together.

## No custom Skill required

Earlier labs in the full course use a reusable `.claude/skills/scoped-bugfix-flow` Skill.
This lab relies only on Claude Code's built-in **Plan mode** — no custom Skill is needed, so
the `.claude/` folder here is intentionally empty/reserved.
