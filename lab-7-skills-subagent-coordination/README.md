# Day 2 · Lab 7 — Add Structured Logging

> **Standalone package.** This folder is a self-contained copy of Lab 7 from a larger Claude
> Code training course — it needs no access to the rest of the course repo. Setup:
> ```bash
> cd lab7-standalone
> python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
> pip install -r requirements.txt
> ```
> All commands below assume you're running them from this folder.

> **Recap.** Day 1 and the Day 2 morning (earlier labs in this course, not included in this
> package) built and mapped this app's fee, reconciliation, and drift logic (Labs 1-4) and
> introduced multi-agent orchestration and a project-scoped review subagent (Labs 4-5). None of
> the fee/reconciliation/drift logic is auditable yet — a fee gets calculated, a reconciliation
> exception gets resolved or escalated, a drift alert fires, and nothing records that it
> happened. This lab fixes that with one cross-cutting change — a shared structured-logging
> abstraction, threaded through three existing modules at once — and composes two things you've
> already seen separately: a **Skill** does the implementing, and a **subagent** does the
> independent review, rather than the same conversation checking its own diff.

---

## The ticket: WM-109 — No structured audit trail across fee, reconciliation, and drift logic

> *"When compliance asks 'why did this fee/escalation/alert happen,' there's nothing to query.
> Add a shared structured-logging abstraction and thread it through `fees.py`, `reconcile.py`,
> and `drift.py` so every fee calculation, every reconciliation exception, and every fired
> drift alert is logged as a structured (JSON) event — not printed, not silently dropped."*

**The fix:** add `agentic_framing/logging_utils.py` — a small `StructuredLogger` — then wire
one log call into each of three modules from earlier labs, at the exact point each one produces
something audit-worthy. This is deliberately a **broad, multi-file change**: three separate
files edited in one coherent pass, implemented by a Skill and then reviewed by a subagent.

### User story

**Given** fee calculations, reconciliation exceptions, and drift alerts that all happen with no
structured record, **When** any of those three things occurs, **Then** a structured (JSON) log
event must be emitted with the fields a compliance reviewer would need — and routine, no-op
outcomes (an exact match, drift that stays within threshold) must NOT add noise to the trail.

### Definition of done

1. `annual_advisory_fee` (`labs/lab1/fees.py`) logs a `fee_calculated` event (`aum`, `fee`) on
   every call.
2. `reconcile_positions` (`labs/lab4/reconcile.py`) logs `position_resolved` (`symbol`,
   `strategy`) for every explained mismatch, and `position_escalated` (`symbol`, `risk_level`,
   `reason`) for every escalation — but nothing for an exact `MATCHED` position.
3. `check_drift_alert` (`labs/lab3/drift.py`) logs `drift_alert_fired` (`portfolio_id`,
   `drift_percent`) whenever it returns an alert — but nothing when it returns `None`.
4. The `logging-reviewer` subagent has reviewed all three changes and returned **APPROVED**.
5. `test_logging.py` passes in full, and the full suite (`pytest`) has no regressions.

> **Verifiable target (Agentic Mindset — Verification ingredient):**
> `test_logging.py` — seeded failing (the three modules don't call the logger yet). That
> failing state *is* the spec for this lab.

---

## What's already built vs. what you'll do

| Already built | Your turn |
|---|---|
| `agentic_framing/logging_utils.py` — `get_logger()`, `StructuredLogger`, and a `capture_log_events()` test helper. | Thread it through the three target modules — nothing here needs editing. |
| `labs/lab1/fees.py`, `labs/lab3/drift.py`, `labs/lab4/reconcile.py` — working domain logic carried forward from earlier labs | Add one `get_logger("...")` + the log calls named in Definition of done, above |
| `.claude/skills/structured-logging-rollout/` — a **multi-file project Skill**: `SKILL.md` (workflow), `reference.md` (field-naming conventions + worked example, loaded on demand), `scripts/verify_structured_logs.py` (a deterministic checker run via Bash) | Use it — read `reference.md` once before writing your first log call |
| `.claude/agents/logging-reviewer.md` — a pre-built, read-only review subagent the Skill delegates to | Nothing to build — just don't skip the delegation step |
| `test_logging.py` — the verifiable target, currently failing | Make it pass without changing what any of the three functions returns |

---

## Part 1: Analyze — read the logger and the three targets

Read `agentic_framing/logging_utils.py` first — it's short. The interface you'll use everywhere:

```python
from agentic_framing.logging_utils import get_logger

logger = get_logger("fees")          # -> logs under "agentic_framing.fees"
logger.info("fee_calculated", aum=aum, fee=fee)
```

Then run the seeded-failing test to see exactly what's missing:

```bash
python3 -m pytest test_logging.py -v
```

You should see failures for all three domains — `fees`, `reconcile`, and `drift` — because none
of them call the logger yet.

---

## Part 2: Use the Skill to implement

This is a **multi-file project Skill**, not a single-file fix — `.claude/skills/
structured-logging-rollout/` is a *directory*: `SKILL.md` plus a `reference.md` that only loads
when you're about to write a log call (progressive disclosure keeps context cheap), plus a
`scripts/verify_structured_logs.py` checker the Skill runs via `Bash` — its logic never has to
be read into the conversation, only its pass/fail output does.

Ask for it explicitly — Skill selection isn't guaranteed to happen implicitly:

> *"Use skill `structured-logging-rollout`. Outcome: thread `agentic_framing.logging_utils`
> through `labs/lab1/fees.py`, `labs/lab4/reconcile.py`, and `labs/lab3/drift.py` per WM-109.
> Scope: only those three files (plus the necessary import/module-level logger in each) —
> don't change what any function returns or how it decides. Verification: delegate to the
> `logging-reviewer` subagent, then run
> `python3 .claude/skills/structured-logging-rollout/scripts/verify_structured_logs.py`, then
> `pytest test_logging.py -v`, then full `pytest`. Guardrails: don't touch fee-tier,
> reconciliation-strategy, or hysteresis logic — only add logging. Run Phase A only first."*

Review the plan, approve it, then let it proceed through Phase B (implement).

> **This is where the safety net matters.** Three files, edited in one pass, is exactly the
> kind of broad change **checkpoints/rewind** exists for — if a diff looks wrong in one file,
> you don't have to re-run the whole thing to fix it. Review each file's diff before accepting.

---

## Part 3: Independent review — delegate to `logging-reviewer`

The Skill's Phase C is a delegation, not a checklist you tick off yourself: once all three files
are edited, the Skill hands the diff to the `logging-reviewer` subagent — a pre-built, read-only
reviewer (`tools: Read, Grep, Glob`, no `Edit`/`Bash`) that starts fresh, with no stake in the
reasoning that produced the change.

### Why a subagent here, and why *this* is the shape that earns one

You've already seen a Skill run inline in the main session (Labs 1-2, and Part 2 above) and a
subagent run in its own isolated context for review (Lab 4's `strategy-reviewer`). This lab
combines both moves deliberately, and the combination is not arbitrary:

- **The implementation is fully specified in advance.** `reference.md` already pins down every
  event name and field before a single log call is written — there's no judgment call Phase B
  needs help with, so it stays a Skill, running inline.
- **The review is exactly the kind of work a subagent is for.** `logging-reviewer` reads all
  three edited modules — a cross-cutting, multi-file check — in its own context, and reports
  back a short verdict. That reading never has to happen in your main conversation's context at
  all; the subagent absorbs it and hands back a summary instead. That's the same
  context-isolation property `strategy-reviewer` had in Lab 4, just applied to three files
  instead of one.
- **It's still read-only by design.** `logging-reviewer` cannot patch `fees.py`, `reconcile.py`,
  or `drift.py` even if it "wanted to" — if it flags something, you (or the Skill, back in
  Phase B) fix it, then ask for review again.

Once all three files are edited, prompt explicitly if the Skill hasn't already:

> *"Have the logging-reviewer subagent review the logging changes in `labs/lab1/fees.py`,
> `labs/lab4/reconcile.py`, and `labs/lab3/drift.py`."*

Read its report. If it comes back **CHANGES NEEDED**, fix the flagged file(s) yourself, then
re-run the tests and ask for review again. Once it's **APPROVED**, move on to Part 4.

---

## Part 4: Verify

```bash
python3 .claude/skills/structured-logging-rollout/scripts/verify_structured_logs.py
python3 -m pytest test_logging.py -v
python3 -m pytest -v
```

All three should be clean: the verification script reports `PASS` for `fees`, `reconcile`, and
`drift`; `test_logging.py` passes in full; the full suite has no regressions.

---

## Part 5: Deliver

Hand back:

1. The three files changed, and the one log call (or two, for `reconcile.py`) added to each.
2. The `logging-reviewer` verdict (APPROVED, plus anything it flagged and how you fixed it).
3. Verification script output + test results (`test_logging.py`, full `pytest`).
4. Any decision point you deliberately chose **not** to log (e.g. an exact `MATCHED` position,
   a drift check that stays within threshold) and why — routine outcomes aren't audit events.

---

## Guardrails

1. Don't change what `annual_advisory_fee`, `reconcile_positions`, or `check_drift_alert`
   return, or how they decide — only add logging.
2. Don't touch the fee-tier bug fix, the reconciliation strategies, or the hysteresis logic
   (`stock_split_adjustment` is still stubbed and drift's hysteresis TODO is still open in this
   package, on purpose) — those belong to other labs, not this one.
3. Don't log a routine/no-op outcome (an exact match, drift within threshold) — that's noise,
   not an audit trail.
4. Never log raw PII — not relevant to these three modules today, but the guardrail the Skill
   and the `logging-reviewer` subagent both carry forward to the next module either one is used
   on.
5. `logging-reviewer` is read-only by design — if it flags something, fix the module yourself;
   don't loosen its checklist to make it stop complaining.

---

## Why this is a Skill *and* a subagent, not just a prompt

The same three-line ask — "thread structured logging through these files" — comes up again
every time this app grows a new module. Packaging the *implementation* as a Skill means the
conventions (event naming, what NOT to log, how to verify) travel with the workflow instead of
living only in this lab's instructions. Packaging the *review* as a separate subagent means that
check is never done by the same conversation that just wrote the code, and never costs the main
session context to perform — `logging-reviewer` reads three files' worth of diff in its own
isolated window and hands back a few lines. Because both are **project-scoped**
(`.claude/skills/`, `.claude/agents/`, committed), the next engineer who clones this repo gets
both — no re-authoring required, and no ambiguity about which one does which job.
