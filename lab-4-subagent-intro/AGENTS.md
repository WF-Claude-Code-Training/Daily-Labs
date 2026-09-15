# Claude Code session guide — Lab 4 (standalone)

You (Claude Code) are pairing with a Wells Fargo Wealth Management engineer working through
a single, self-contained lab extracted from a larger Claude Code training course (Day 1,
Lab 4 of an 8-lab progression). This folder runs entirely on its own — no access to the rest
of the course repo, and no GitLab access, is required or expected.

## The task

WM-106 — positions don't match the custodian file. See [README.md](README.md) for the full
user story and step-by-step lab flow (implement a strategy, then get it independently reviewed
by a subagent).

## The shared standard: the five-ingredient task frame

Every non-trivial ask should read as an agentic task frame, not a bare prompt:

1. **Outcome** — the end state, not the keystrokes.
2. **Scope** — the concrete target and boundaries (which module/files; what not to touch).
3. **Verification** — how "done" is checked (here: `pytest`, plus the `strategy-reviewer`
   subagent's checklist).
4. **Deliverable** — the reviewable artifact handed back (a diff summary, a report).
5. **Guardrails** — what NOT to do, and when to stop and ask.

## How to work in this folder

- **Domain is Wealth Management** — portfolios, positions, custodian reconciliation, advisor
  escalation. Keep examples in that world.
- **Files:**
  - `reconcile.py` — the module you'll edit. Three normalization strategies already
    work (`rounding_tolerance`, `settlement_date_offset`, `currency_conversion`);
    `stock_split_adjustment` is stubbed to always return `False`.
  - `test_reconcile.py` — the verifiable target. One test fails on purpose
    (`test_stock_split_auto_resolves`); that failing test *is* the spec.
  - `run_reconcile.py` — prints a triage report over the CSV fixtures.
  - `fixtures/` — `book_positions.csv` / `custodian_file.csv`, a deliberate mix of
    matches, explainable mismatches, and genuine breaks.
  - `backlog/WM-106-reconcile-script.md` — the ticket this lab is based on.
  - `.claude/agents/strategy-reviewer.md` — a pre-built, read-only subagent. Delegate to it
    after implementing `stock_split_adjustment`, before wiring it into `DEFAULT_STRATEGIES` (see
    README.md Part 3).
- **Verify with `pytest`, not by eye:**
  ```bash
  python3 -m pytest test_reconcile.py -v   # this lab's tests
  python3 -m pytest -v                       # full suite, no regressions
  ```
- **Guardrails:**
  - `stock_split_adjustment` must not guess a split ratio outside `KNOWN_SPLIT_RATIOS` — verify
    notional value (`qty * price`) is unchanged within `SPLIT_NOTIONAL_TOLERANCE`, don't just
    check `qty`/`price` in isolation.
  - Don't touch the other three strategies or the dollar-risk override in
    `reconcile_positions` while implementing this one.
  - `strategy-reviewer` is read-only by design (`tools: Read, Grep, Glob`, no `Edit`/`Bash`) —
    if it flags something, fix `reconcile.py` yourself; don't loosen the subagent's checklist to
    make it stop complaining.
  - A passing test is necessary but not sufficient — `strategy-reviewer`'s job is to catch a
    shortcut that happens to pass the given tests without honoring the guardrails above.

## Why this lab uses a subagent, not a Skill

A Skill runs inline, in your main session's context — the right choice when the workflow
doesn't need isolation from the conversation that's driving it. A **subagent** runs in its own
context with its own enforced tool list, which is worth the overhead specifically when you want
independence: a reviewer that shares no history with the code it's reviewing, and that
*cannot* edit code no matter what permission mode the main session is in. That's why
`strategy-reviewer` exists as a subagent — reviewing/exploring, not implementing, is the kind of
work a subagent is usually for.
