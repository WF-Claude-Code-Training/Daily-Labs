# Day 1 · Lab 4 — Implement, Then Get an Independent Review

> **Standalone package.** This folder is a self-contained copy of Lab 4 from a larger Claude
> Code training course. Open this folder
> directly as your VS Code / editor workspace root, then set up:
> ```bash
> pip install -r requirements.txt
> ```
> All commands below assume you're running them from this folder.

> **Environment notes.** If `python3` isn't on PATH (common on Windows), substitute `py -3` or
> `python` in every command below. If `pip install` fails behind corporate
> proxy, confirm the current proxy environment variables or internal package index with your TA
> before the session — don't spend lab time debugging network config. If `pip install` fails
> with `error: externally-managed-environment` (PEP 668, common on Homebrew/Linux system
> Python), rerun with `pip install --user -r requirements.txt` or
> `pip install --break-system-packages -r requirements.txt`.

> **Recap.** In Lab 3 (an earlier lab in this course, not included in this package) you used
> **Plan mode** and **test-driven delivery** to add hysteresis to a drift alert — a bounded,
> one-shot fix reviewed before it ran. This lab keeps that same discipline for the fix itself,
> then adds one new move: before you call the fix done, hand it to a **subagent** — a
> pre-built, read-only reviewer that starts fresh and can't edit your code — for an independent
> pass you can't get by asking the same conversation to check its own work.

---

## The ticket: WM-106 — Positions don't match the custodian file

> *"Write a script that compares our book of positions against the custodian file and prints
> the mismatches."*

Taken literally, that dumps every discrepancy on an advisor every night — and most of them are
**explainable noise**: a price off by a rounding cent, a settlement date off by the usual one
day, a price quoted in another currency. Buried in that noise are the few **genuine breaks** an
advisor actually needs to see — a real quantity gap, or a position missing on one side.

The ticket also has a vague outcome, no constraints, and "prints the mismatches" is *output*,
not *verification*. **The fix:** reframe it — reconcile book vs custodian, resolve what a known
normalization rule explains and escalate everything else, read-only against both source files,
verified by `test_reconcile.py` — so the result never silently drops a mismatch and
never guesses.

### User story

**Given** a nightly reconciliation run where book and custodian positions disagree for a mix of
explainable reasons (rounding, settlement-date offset, currency) and a few genuine breaks,
**When** the reconciliation logic evaluates each mismatch,
**Then** it must resolve every mismatch a known strategy explains, escalate everything else
(never silently drop a mismatch, never guess), and escalate any position above the dollar-risk
threshold regardless of whether a strategy would have explained it.

### Definition of done

1. Exact matches, each normalization case (rounding, settlement-date offset, currency), a
   genuinely unresolved case, and a high-dollar case that escalates despite a matching pattern
   all resolve to the correct verdict.
2. Every input position ends as exactly one of `MATCHED` / `RESOLVED` / `ESCALATED` — none
   dropped.
3. `test_reconcile.py` passes in full, and the full suite (`pytest`) has no regressions.
4. The new strategy has been reviewed by the `strategy-reviewer` subagent and any findings
   addressed.

> **Verifiable target (Agentic Mindset — Verification ingredient):** `test_reconcile.py`
> — match / resolve / escalate / dollar-risk cases are the acceptance criteria the strategies are
> built against, not the printed output.

---

## Part 1: Read the existing reconciliation logic

For each position, `reconcile_positions()` works through four steps:

| Step | What happens |
|---|---|
| **Read** | Line up the book and custodian sides of the position |
| **Decide** | Pick the next known strategy to try (`rounding_tolerance`, `settlement_date_offset`, `currency_conversion`) |
| **Act** | Apply it — does it *explain* the difference? |
| **Observe** | If yes → `RESOLVED`; if no → try the next; if none → `ESCALATED` with the strategies it tried |

Every position ends as exactly one verdict — `MATCHED`, `RESOLVED`, or `ESCALATED` — so nothing
is ever silently dropped.

### The dollar-risk override

A large **notional exposure** (`qty × price`) escalates for human review *even if* a strategy
would have explained it. Risk beats pattern-matching: you don't auto-resolve a $2.5M position on
a rounding cent. This is the governance beat of the lab.

### Naive "print mismatches" vs. this implementation

| Naive "print mismatches" | This implementation |
|---|---|
| Prints every discrepancy at once | Resolves explainable noise, surfaces only genuine breaks |
| No notion of "explainable vs real" | Records the strategy that explained each, and the ones it tried |
| No risk awareness | High-dollar positions escalate regardless of pattern |
| Advisor triages by hand | Advisor sees a short escalation list + an audit trail |

Read `reconcile.py`'s strategies and the `MATCHED/RESOLVED/ESCALATED` model, then run the tests
— they *are* the acceptance criteria:

```bash
python3 -m pytest test_reconcile.py -v
```

You should see 13 passing and **1 failing**: `test_stock_split_auto_resolves`. Read it — it's
your verifiable target for Part 2.

---

## What's already built vs. what you'll build

| Already built | Your turn |
|---|---|
| `reconcile.py` — 3 working strategies (`rounding_tolerance`, `settlement_date_offset`, `currency_conversion`), the `triage` report, the dollar-risk override | Implement the 4th strategy, `stock_split_adjustment` — currently a stub that always returns `False` |
| `test_reconcile.py` — all green **except** `test_stock_split_auto_resolves` | Make that one test pass without breaking the rest |
| `fixtures/book_positions.csv`, `custodian_file.csv` — a deliberate mix | Nothing to change here — the exercise test uses inline positions |
| `.claude/agents/strategy-reviewer.md` — a pre-built, read-only review subagent | Delegate your finished strategy to it before wiring it in (Part 3) |

---

## Part 2: Build — implement the missing strategy

This is the hands-on core of the lab: a real, scoped gap in working code, with a failing test
as the verifiable target — the same discipline as Lab 3, just applied to a different module.

Open `reconcile.py` and find `stock_split_adjustment` — it's stubbed to always return
`False`, with a docstring describing what it should do: explain a qty/price difference caused by
a known forward stock split, where the custodian's quantity is the book's quantity times a known
ratio (`KNOWN_SPLIT_RATIOS`), the price is divided by that same ratio, and the notional value
(`qty * price`) is unchanged within `SPLIT_NOTIONAL_TOLERANCE`.

Give Claude Code the frame directly:

> *"Implement `stock_split_adjustment` in `reconcile.py` so
> `test_stock_split_auto_resolves` in `test_reconcile.py` passes. Follow the pattern
> of the existing strategies (`rounding_tolerance`, `currency_conversion`) — read qty/price/
> settle_date from both sides, don't guess at a ratio that isn't in `KNOWN_SPLIT_RATIOS`. Add
> the strategy to `DEFAULT_STRATEGIES` once it works. Don't touch the other strategies or the
> dollar-risk override. Run `pytest test_reconcile.py -v` to verify."*

Then run the full suite:

```bash
python3 -m pytest test_reconcile.py -v
```

All 14 tests should pass, including `test_default_strategies_are_the_three_known_normalizations`
— since you just added a 4th strategy, that test's name and assertion are now stale. Update it
(rename it, and update the expected list) so the suite still says what's true.

---

## Part 3: Get it independently reviewed — your first subagent

Your strategy passes its tests. Before you wire it into `DEFAULT_STRATEGIES` for good and call
this done, get it reviewed — by something other than the conversation that just wrote it.

### Why a subagent, not just asking Claude Code to check its own diff

A **Skill** runs inline, in your main session, sharing its
context and history — the cheap, default choice for a reusable workflow. A **subagent**
(`.claude/agents/*.md`) runs in its own context — its own history, its own enforced tool list,
its own model — separate from your main session, and **disposable**: once it reports back, that
context is gone. That isolation is the entire point here:

- **Independence.** The reviewer never saw the reasoning that produced the code — it can't be
  talked into rubber-stamping its own blind spots the way a conversation reviewing its own work
  can be.
- **A disposable context.** Reading `reconcile.py` in full, working through the five-point
  checklist below — all of that happens in a context window that's thrown away once the
  subagent reports back. Only the verdict lands in your conversation, not the reasoning it took
  to get there, so your main session's context budget stays exactly as it was before you asked.
- **Enforced restriction, not a suggestion.** `strategy-reviewer`'s tools are locked to
  `Read, Grep, Glob` — no `Edit`, no `Bash`. It is *not able* to patch the code itself, no matter
  what permission mode your main session is running in.
- **Tests check behavior; the reviewer checks the guardrails.** A test can pass while the
  implementation still took a shortcut — e.g. quietly matching on a ratio outside
  `KNOWN_SPLIT_RATIOS` for the one fixture it happened to be tested against. That's exactly what
  `strategy-reviewer`'s checklist looks for.

Read `.claude/agents/strategy-reviewer.md` — note its `tools:` line and its five-point
checklist — then delegate to it:

> *"Have the strategy-reviewer subagent review `stock_split_adjustment` and the
> `DEFAULT_STRATEGIES` change in `reconcile.py`."*

Read its report. If it comes back **CHANGES NEEDED**, fix `reconcile.py` yourself — the
subagent can't, by design — then re-run the tests and ask for review again. Once it's
**APPROVED**, you're done with the code.

---

## Part 4: Run it and read the result

```bash
python3 run_reconcile.py fixtures/book_positions.csv fixtures/custodian_file.csv
```

You'll see the auto-resolutions (KO rounding, MSFT settlement offset, SAP currency) and the
escalations — GOOG (unexplained quantity gap), NVDA (missing on one side), **TSLA, which
escalates HIGH even though rounding explains its price** because its notional exceeds the
threshold, and **ORCL**, whose custodian row carries a free-text note:

> *3-for-2 forward stock split per press release; ratio not yet loaded to reference table*

Nothing in `DEFAULT_STRATEGIES` reads free text, and a 3-for-2 ratio (`1.5`) isn't in
`KNOWN_SPLIT_RATIOS` — so ORCL escalates, and *should* escalate. That note is exactly the kind
of judgment call that belongs to a human analyst, not something to auto-resolve on a guess.
Escalating what you can't verify is correct behavior, not a gap to close.

---

## Part 5: Verify & deliver

```bash
python3 -m pytest -v
```

Then read the triage report yourself — confirm no mismatch was silently dropped (every input
symbol appears once), the high-dollar case genuinely escalated, and the source files are
untouched. Your deliverables:
1. ✅ Ticket reframed before code — outcome, constraints, and verification named up front
2. ✅ Failing test (`test_stock_split_auto_resolves`) understood before implementing
3. ✅ `stock_split_adjustment` implemented and wired into `DEFAULT_STRATEGIES`
4. ✅ Reviewed independently by the `strategy-reviewer` subagent, findings addressed
5. ✅ Ran the triage report and read the resolved-vs-escalated split
6. ✅ All tests passing, including the updated strategy-enumeration test

---

## Why this matters

- **A strategy is a bounded extension point** — Part 2 showed you can grow what's explainable
  without touching the report, the escalation model, or the dollar-risk override.
- **Not every reusable workflow needs a subagent.** Reach for one when isolation, an enforced
  tool restriction, or a different model than your main session actually buys you something —
  not by default. A Skill is the cheaper first choice; a subagent earns its overhead.
- **Subagents are usually reviewers and explorers, not implementers.** `strategy-reviewer`
  doesn't know anything about wealth management that Claude Code didn't already know — its
  value is starting fresh and being unable to edit code, which is exactly the shape most
  subagents take (code review, codebase exploration) rather than domain-specific business logic.
- **Read-only tools are an enforced control, not a guideline.** `strategy-reviewer` cannot patch
  `reconcile.py` even if it "wanted to" — that's a property of its `tools:` list, not of good
  behavior.
- **Escalation is still a feature.** ORCL's free-text corporate-action note is a real case no
  fixed rule can safely resolve — escalating it to a human is the correct outcome, not an
  unfinished one.
