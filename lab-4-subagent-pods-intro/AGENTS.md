# Claude Code session guide: Lab 4 (standalone)

You (Claude Code) are working with a Wells Fargo Wealth Management engineer on **Day 2, Lab 4**
of an 8-lab Claude Code training course. This folder runs entirely on its own: no access to the
rest of the course repo, and no GitLab access, is required or expected.

**Day 2 works differently from Day 1.** Day 1 was one bounded task at a time with the engineer
in the loop for every step. Today they work through a **pod of subagent roles**. Your job shifts
accordingly: route work to the roles rather than doing it all inline, and help them design the
hand-offs between roles.

The lab follows the same arc Labs 1-2 used for Skills: read a working example, use it, then
author one:

- **Parts 1-2:** three roles ship pre-built in `.claude/agents/`. The engineer reads them, then
  drives a real bug fix through `implementer` -> `test-author` -> `contract-reviewer`. Prompts
  are supplied in the README for this part; it's a guided demo on purpose.
- **Part 3:** they author a fourth role, `reference-data-steward`, using the three as templates.
- **Part 4:** they run WM-115 through the pod with **no prompts supplied**.

## The tickets

- **WM-106** (Part 2 demo): `stock_split_adjustment` is stubbed; one test fails.
- **WM-115** (Part 4, required): Ops can't add a split ratio without a release.
- **WM-116, WM-117** (stretch, optional): tiered risk policy, machine-readable export.

Tickets are in `backlog/`; lab flow in [README.md](README.md). WM-115/116/117 are deliberately
underspecified and the engineer reframes them before any code is written. **Do not reframe a
ticket for them unless asked**. That reframing is the exercise, and a ticket you silently
interpret is a contract they never wrote.

## The shared standard: the five-ingredient task frame

Every non-trivial ask should read as an agentic task frame, not a bare prompt:

1. **Outcome**: the end state, not the keystrokes.
2. **Scope**: the concrete target and boundaries (which module/files; what not to touch).
3. **Verification**: how "done" is checked (`pytest`, `check_pod.py`, a reviewer's verdict).
4. **Deliverable**: the reviewable artifact handed back (a diff summary, a report).
5. **Guardrails**: what NOT to do, and when to stop and ask.

## Delegation posture for this lab

- **Prefer the pod over inline work.** `test-author`, `implementer`, and `contract-reviewer`
  already exist in `.claude/agents/`. Route work to them rather than absorbing it. If a needed
  role doesn't exist yet (e.g. `reference-data-steward` before Part 3), say so rather than
  silently doing its job.
- **Don't write `reference-data-steward` unprompted.** Authoring it is Part 3's exercise. When
  asked to help, point at the three shipped roles as templates and at its contract in
  `ROLES.md`; don't hand over a finished file unless explicitly asked for one.
- **In Part 2, let the seam show.** `implementer`'s fix makes `test_stock_split_auto_resolves`
  pass and makes `test_default_strategies_are_the_three_known_normalizations` stale. That second
  failure is the lesson: repairing it is `test-author`'s job, because an implementer that edits
  tests can make anything pass. Do not pre-emptively fix both, and do not let `implementer` edit
  the test.
- **Never let the implementing context review its own diff.** `contract-reviewer` does that.
  If the engineer skips it, remind them once.
- **One editor at a time.** Subagents share this working tree. Never run two editing roles
  concurrently on the same file; fan out reads and reviews instead. If asked to parallelize
  edits, name the conflict risk before proceeding.
- **A read-only role's `tools:` list is a control, not a suggestion.** If `contract-reviewer` or
  `reference-data-steward` needs something changed, it reports. It does not get granted `Edit`
  or `Bash` to get unstuck.
- **Be honest about which boundaries are enforced.** `contract-reviewer` is tool-enforced and
  genuinely cannot edit. `implementer`'s "never edit a test" and `test-author`'s "never edit
  source" are **contracts in prose**. A `tools:` list gates tool types, not file paths. If the
  engineer asks whether a boundary is real, say which kind it is. That gap is deliberate setup
  for Lab 7's `PreToolUse` hook; don't paper over it.

## How to work in this folder

- **Domain is Wealth Management**: portfolios, positions, custodian reconciliation, advisor
  escalation, Ops-maintained reference data, Risk-owned policy. Keep examples in that world.
- **Files:**
  - `reconcile.py`: the module under change. Three strategies work
    (`rounding_tolerance`, `settlement_date_offset`, `currency_conversion`);
    `stock_split_adjustment` is stubbed. `reconcile_positions` already accepts `strategies=` and
    `dollar_threshold=`: that existing seam matters for WM-115/WM-116.
  - `test_reconcile.py`: the original contract. 13 green, 1 failing on purpose. Must stay green.
  - `test_reconcile_epic.py`: WM-115's acceptance contract, 6 seeded failing. **Required.**
    Read it before proposing a design; it answers what to do when Ops's file is missing or
    malformed.
  - `test_reconcile_stretch.py`: WM-116 + WM-117, 11 seeded failing. **Optional stretch.** Don't
    steer the engineer into these unless they ask or the required work is done.
  - `export.py`: **does not exist yet**; WM-117 (stretch) creates it. The stretch tests import
    from it.
  - `run_reconcile.py`: prints the triage report. WM-117 adds `--format`; the ORCL demo in
    README Part 3 wants `--reference-data`.
  - `reference_data/split_ratios.json`, `risk_policy.json`: owned by Ops and Risk respectively.
    **Read-only from this repo's perspective.** Do not edit them to make a test pass.
  - `ROLES.md`: how the three shipped roles work, plus the contract for the fourth.
    `check_pod.py`: their validator; 3 `[ok]` + 1 `[FAIL]` on a fresh checkout.
  - `.claude/agents/`: `implementer`, `test-author`, `contract-reviewer` (shipped, and the
    templates for Part 3).
- **Verify with scripts, not by eye:**
  ```bash
  python3 -m pytest test_reconcile.py -v          # original contract — no regressions
  python3 -m pytest test_reconcile_epic.py -v     # WM-115 — required
  python3 -m pytest test_reconcile_stretch.py -v  # WM-116/117 — optional
  python3 -m pytest -v                            # everything
  python3 check_pod.py                            # the role definitions themselves
  ```

## Guardrails

- `stock_split_adjustment` must not guess a ratio outside the ratios it was given: verify
  notional (`qty * price`) is unchanged within `SPLIT_NOTIONAL_TOLERANCE`, not just `qty` or
  `price` in isolation.
- Never widen a default so a new test passes. WM-115 (and WM-116, if attempted) are explicitly
  opt-in: a caller that passes no reference data and no risk policy must get today's exact
  behavior, and the suites test for that.
- Don't edit `reference_data/*.json`. A missing or malformed file is a case the contract covers
  (degrade to compiled-in defaults), not a reason to fix the data.
- Don't touch the escalation model or the dollar-risk override's intent: risk beats
  pattern-matching, and every input symbol lands in exactly one verdict.
- A passing test is necessary but not sufficient. The reviewer roles exist to catch a shortcut
  that satisfies the given tests while violating a guardrail.

## Why this lab uses subagents, not a Skill

A Skill runs inline, in the main session's context: the right choice when a reusable workflow
doesn't need isolation from the conversation driving it. A **subagent** runs in its own context
with its own enforced tool list, and that is worth the overhead when you want one of three
things: independence from the reasoning that produced the code, a tool restriction that holds
regardless of the main session's permission mode, or a context you can throw away.

Today's pod is built on all three, with one honest caveat. `contract-reviewer` has no memory of
writing the code and *cannot* change it: that's enforced. `test-author` and `implementer` each
run in a fresh context and are *asked* to stay on their side of the test/source line: that's a
contract. Independence and disposable context you get for free from the subagent boundary; path
restrictions you do not, and Lab 7 is where that gets closed.
