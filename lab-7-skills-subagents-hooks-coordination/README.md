# Day 2 · Lab 7 — Add Structured Logging

> **Standalone package.** This folder is a self-contained copy of Lab 7 from a larger Claude
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

1. `annual_advisory_fee` (`fees.py`) logs a `fee_calculated` event (`aum`, `fee`) on
   every call.
2. `reconcile_positions` (`reconcile.py`) logs `position_resolved` (`symbol`,
   `strategy`) for every explained mismatch, and `position_escalated` (`symbol`, `risk_level`,
   `reason`) for every escalation — but nothing for an exact `MATCHED` position.
3. `check_drift_alert` (`drift.py`) logs `drift_alert_fired` (`portfolio_id`,
   `drift_percent`) whenever it returns an alert — but nothing when it returns `None`.
4. The `logging-reviewer` subagent has reviewed all three changes and returned **APPROVED**.
5. A `PreToolUse` hook (`.claude/hooks/protected_regions.py`) is wired in `.claude/settings.json`
   and blocks any edit that would remove or alter the fee-tier table, the reconciliation-strategy
   definitions, or the drift hysteresis condition — confirmed by
   `pytest test_protected_regions_hook.py -v`.
6. `test_logging.py` passes in full, and the full suite (`pytest`) has no regressions.

> **Verifiable target (Agentic Mindset — Verification ingredient):**
> `test_logging.py` — seeded failing (the three modules don't call the logger yet). That
> failing state *is* the spec for this lab.

---

## What's already built vs. what you'll do

| Already built | Your turn |
|---|---|
| `agentic_framing/logging_utils.py` — `get_logger()`, `StructuredLogger`, and a `capture_log_events()` test helper. | Thread it through the three target modules — nothing here needs editing. |
| `fees.py`, `drift.py`, `reconcile.py` — working domain logic carried forward from earlier labs | Add one `get_logger("...")` + the log calls named in Definition of done, above |
| `.claude/skills/structured-logging-rollout/` — a **multi-file project Skill**: `SKILL.md` (workflow), `reference.md` (field-naming conventions + worked example, loaded on demand), `scripts/verify_structured_logs.py` (a deterministic checker run via Bash) | Use it — read `reference.md` once before writing your first log call |
| `.claude/agents/logging-reviewer.md` — a pre-built, read-only review subagent the Skill delegates to | Nothing to build — just don't skip the delegation step |
| `.claude/hooks/protected_regions.py` + `protected_regions.json`, wired in `.claude/settings.json` — a `PreToolUse` hook that enforces the fee-tier/strategy/hysteresis guardrails as denials, not prose | Nothing to build — confirm it blocks an out-of-scope edit, then continue with the in-scope logging change |
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

Skill selection isn't guaranteed to happen implicitly. Before you type anything to Claude,
write your own task frame covering all five ingredients:

- **Outcome** — use the skill to thread the shared logger through `fees.py`, `reconcile.py`, and `drift.py` per
  WM-109, so each domain's audit-worthy moment gets a structured event.
- **Scope** — only those three files (plus the import/module-level logger each one needs) —
  nothing else changes.
- **Verification** — the `logging-reviewer` subagent has to approve the diff, the Skill's own
  checker script has to pass, the seeded logging test has to go green, and the full suite has
  to still be clean — name that order, don't leave it implicit.
- **Deliverable** — the three diffs, the reviewer's verdict, and which routine outcomes you
  deliberately chose not to log.
- **Guardrails** — the fee-tier table, the reconciliation strategies, and the drift hysteresis
  condition are off-limits — logging only, no behavior changes.

Ask for the Skill by name (`structured-logging-rollout`), and tell it to run Phase A only —
don't let it run straight through to implementation before you've reviewed the plan.

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

> *"Have the logging-reviewer subagent review the logging changes in `fees.py`,
> `reconcile.py`, and `drift.py`."*

Read its report. If it comes back **CHANGES NEEDED**, fix the flagged file(s) yourself, then
re-run the tests and ask for review again. Once it's **APPROVED**, move on to Part 4.

---

## Part 4: See the guardrail enforced by a hook, not just written down

This lab's guardrails have always said "don't touch fee-tier, reconciliation-strategy, or
hysteresis logic while threading logging through." A `PreToolUse` hook now enforces exactly
that — it's already wired in `.claude/settings.json` and reads its rules from
`.claude/hooks/protected_regions.json`. It intercepts every `Write`/`Edit`/`MultiEdit`, checks
whether the change would remove or alter one of three protected snippets (the fee-tier table in
`fees.py`, the `DEFAULT_STRATEGIES` tuple in `reconcile.py`, or the hysteresis condition in
`drift.py`), and **blocks it outright** if so — Claude sees the denial reason and has to work
around it, the same way `logging-reviewer` can't be talked out of a finding.

Try it once, deliberately, before moving on: ask Claude to also "fix the hysteresis TODO while
you're in `drift.py`" as an explicit off-scope request, and confirm the hook denies the edit with
a clear reason. Then continue with only the in-scope `drift_alert_fired` log call. This is the
same guardrail from Part 2's task frame — the hook is what makes it a control instead of a
request.

---

## Part 5: Verify

```bash
python3 .claude/skills/structured-logging-rollout/scripts/verify_structured_logs.py
python3 -m pytest test_protected_regions_hook.py -v
python3 -m pytest test_logging.py -v
python3 -m pytest -v
```

All four should be clean: the verification script reports `PASS` for `fees`, `reconcile`, and
`drift`; the hook test suite passes in full; `test_logging.py` passes in full; the full suite has
no regressions.

---

## Part 6: Deliver

Hand back:

1. The three files changed, and the one log call (or two, for `reconcile.py`) added to each.
2. The `logging-reviewer` verdict (APPROVED, plus anything it flagged and how you fixed it).
3. Confirmation that the `protected_regions.py` hook denied your deliberate off-scope test edit,
   with the reason it returned.
4. Verification script output + test results (`test_protected_regions_hook.py`, `test_logging.py`,
   full `pytest`).
5. Any decision point you deliberately chose **not** to log (e.g. an exact `MATCHED` position,
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
6. The `protected_regions.py` hook is the enforcement layer for guardrail 2 above — if it
   denies an edit, that's it working correctly; don't disable the hook or edit
   `protected_regions.json` to loosen it just to get past a legitimate denial.

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
