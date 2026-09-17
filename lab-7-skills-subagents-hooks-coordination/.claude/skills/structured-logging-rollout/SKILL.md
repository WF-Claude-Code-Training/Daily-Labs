---
name: structured-logging-rollout
description: >-
  Thread the shared StructuredLogger (agentic_framing/logging_utils.py) through one or more
  existing modules, replacing print()/unstructured strings with structured (JSON) log events
  at the decision points worth auditing. USE WHEN a ticket asks to "add logging", "add an audit
  trail", or "make X auditable" to existing WM modules. See reference.md for field-naming
  conventions and worked examples before implementing. Delegates the post-implementation review
  to the logging-reviewer subagent rather than reviewing its own diff.
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/verify_structured_logs.py:*)
---

# Skill: structured-logging-rollout

A reusable, multi-file workflow for adding structured logging to existing modules without
turning it into a refactor of everything those modules do. Has no built-in knowledge of which
modules or events — that comes from the invoking task frame.

## Intent

Make the behavior described in the frame's Outcome *auditable* — every event worth a human or a
compliance system asking "why did this happen?" gets one structured log call — without changing
what the code actually decides or returns.

## Before implementing: read reference.md

`reference.md` (in this skill's directory) has the field-naming conventions, the event-per-module
table, and worked before/after examples. Read it once per session before writing the first log
call — don't guess at field names from scratch each time.

## Scope

Derive scope entirely from the invoking task frame:
- **Primary code target(s)**: the module(s) named in the frame's **Scope** (e.g. `fees.py`,
  `reconcile.py`, `drift.py`).
- **Logging infra**: always `agentic_framing.logging_utils.get_logger(...)` — never a new
  logging mechanism, never `print()`.
- **Out of bounds unless explicitly requested**: fixing unrelated bugs in the target modules,
  changing return values or public signatures, adding logging to modules not named in Scope.

## Phase flow

1. **Phase A: Analyze only (no code changes).**
   - Read each target module named in the frame's Scope.
   - For each, identify the *decision points* worth an audit event (a calculation completing,
     an exception resolved/escalated, an alert firing) — not every line, not routine/no-op
     paths (see reference.md's "what NOT to log" note).
   - Propose the event name and fields for each call site, in the naming style from
     reference.md.
   - Stop and wait for confirmation before editing.

2. **Phase B: Implement.**
   - Add `from agentic_framing.logging_utils import get_logger` and a module-level
     `logger = get_logger("<domain>")` to each target module.
   - Call `logger.info(event, **fields)` (or `.warning`/`.error` where the frame's Scope says
     an escalation/failure deserves a higher level) at each identified decision point.
   - Do not touch the function's return value, control flow, or public signature.

3. **Phase C: Independent review (subagent) — don't review your own diff.**
   - Delegate to the `logging-reviewer` subagent (`.claude/agents/logging-reviewer.md`), naming
     every file touched in Phase B. It reads those diffs fresh, checks them against
     `reference.md`'s conventions and this Skill's guardrails, and returns an APPROVED /
     CHANGES NEEDED report — it cannot edit code itself.
   - This step is *why* the rollout is worth being multi-file and cross-cutting in one Skill
     invocation: the same touch-three-files-at-once shape that makes this a Skill (not three
     separate small fixes) is exactly what benefits from one reviewer reading all three diffs
     together, in a context that never has to re-enter the main conversation's history.
   - If it comes back CHANGES NEEDED, fix the target module(s) yourself — the subagent can't —
     then ask for review again. Do not proceed to Phase D until APPROVED.

4. **Phase D: Verify.**
   - Run the verification script (context-lean — invoke it via Bash rather than reading its
     source into context; it does the checking):
     ```bash
     python3 ${CLAUDE_SKILL_DIR}/scripts/verify_structured_logs.py <module1> [<module2> ...]
     ```
   - Run the test command(s) named in the frame's Verification (fall back to
     `pytest test_logging.py -v` if none is named).

5. **Phase E: Deliver.**
   - Files changed, one line per module.
   - The event name + fields added per module (a small table).
   - The `logging-reviewer` verdict (APPROVED, plus anything it flagged and how it was fixed).
   - Verification script output + test results.
   - Any decision point you chose *not* to log, and why (routine/no-op paths).

## Guardrails

- Never log raw PII (SSNs, account numbers, full names) in a field value — this app's fee/
  reconciliation/drift data doesn't carry PII, but if a future target module does, redact or
  omit it; ask before logging anything that looks like client-identifying data.
- Don't widen scope to modules the frame didn't name.
- Don't change what a function returns or how it decides — only add logging.
- If a target module doesn't obviously have a "domain name" for `get_logger(...)`, ask rather
  than guessing (reference.md lists the ones already in use).
- A passing test is necessary but not sufficient — `logging-reviewer`'s checklist catches
  convention drift (an invented field name, a routine path logged anyway) that a green test
  suite alone won't. Don't skip Phase C because Phase D looks like it'll pass anyway.
