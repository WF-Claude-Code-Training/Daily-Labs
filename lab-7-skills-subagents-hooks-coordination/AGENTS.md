# Claude Code session guide — Lab 7 (standalone)

You (Claude Code) are pairing with a Wells Fargo Wealth Management engineer working through
a single, self-contained lab extracted from a larger Claude Code training course (Day 2,
Lab 7 of an 8-lab progression). This folder runs entirely on its own — no access to the rest
of the course repo is required or expected.

## The task

WM-109 — no structured audit trail across fee, reconciliation, and drift logic. See
[README.md](README.md) for the full user story and step-by-step lab flow (use a Skill to
implement, then get the result independently reviewed by a subagent).

## The shared standard: the five-ingredient task frame

Every non-trivial ask should read as an agentic task frame, not a bare prompt:

1. **Outcome** — the end state, not the keystrokes.
2. **Scope** — the concrete target and boundaries (which module/files; what not to touch).
3. **Verification** — how "done" is checked (here: the `logging-reviewer` subagent's verdict,
   the verify script, and `pytest`).
4. **Deliverable** — the reviewable artifact handed back (a diff summary, a report).
5. **Guardrails** — what NOT to do, and when to stop and ask.

## How to work in this folder

- **Domain is Wealth Management** — advisory fees, portfolio reconciliation, drift monitoring.
  Keep examples in that world.
- **Files:**
  - `agentic_framing/logging_utils.py` — the shared `StructuredLogger` / `get_logger()` /
    `capture_log_events()` test helper. Already built — don't edit it.
  - `fees.py`, `drift.py`, `reconcile.py` — the three modules you'll thread logging through.
    Their domain logic (fee tiers, reconciliation strategies, drift hysteresis) is carried
    forward from earlier labs and is out of scope here, whether or not it's fully fixed yet.
  - `test_logging.py` — the verifiable target. All tests fail on purpose until logging is
    threaded through; that failing state *is* the spec.
  - `backlog/WM-109-login-audit-log.md` — the ticket this lab is based on.
  - `.claude/skills/structured-logging-rollout/` — the reusable, multi-file Skill: `SKILL.md`
    (workflow), `reference.md` (field-naming conventions, loaded on demand),
    `scripts/verify_structured_logs.py` (a deterministic Bash-run checker).
  - `.claude/agents/logging-reviewer.md` — a pre-built, read-only subagent. The Skill's Phase C
    delegates to it after implementing, before verification (see README.md Part 3).
  - `.claude/hooks/protected_regions.py` + `protected_regions.json`, wired in `.claude/settings.json`
    — a `PreToolUse` hook that denies any edit removing or altering the fee-tier table,
    `DEFAULT_STRATEGIES`, or the drift hysteresis condition. See README.md Part 4.
- **Verify with `pytest`, not by eye:**
  ```bash
  python3 -m pytest test_logging.py -v   # this lab's tests
  python3 -m pytest -v                     # full suite, no regressions
  ```
- **Guardrails:**
  - Don't change what `annual_advisory_fee`, `reconcile_positions`, or `check_drift_alert`
    return, or how they decide — only add logging.
  - Don't touch fee-tier, reconciliation-strategy, or hysteresis logic while threading logging
    through — those are separate exercises, not this lab's scope.
  - Don't log a routine/no-op outcome (an exact match, drift within threshold) — noise, not an
    audit trail.
  - Never log raw PII.
  - `logging-reviewer` is read-only by design (`tools: Read, Grep, Glob`, no `Edit`/`Bash`) — if
    it flags something, fix the module yourself; don't loosen the subagent's checklist to make
    it stop complaining.
  - The `protected_regions.py` `PreToolUse` hook is the enforcement layer for the fee-tier/
    strategy/hysteresis guardrail above — if it denies an edit, don't disable the hook or edit
    `protected_regions.json` to get past it; fix the edit instead.
  - A passing test is necessary but not sufficient — `logging-reviewer`'s checklist catches
    convention drift (an invented field name, a routine path logged anyway) that a green test
    suite alone won't.

## Why this lab uses a Skill *and* a subagent

A **Skill** runs inline, in the main session's context — the right choice for Phase B here
because the implementation is fully specified in advance (`reference.md` already pins down
every event name and field): there's no judgment call that needs isolation. A **subagent** runs
in its own context with its own enforced tool list — worth the overhead specifically when you
want independence, and that's exactly what the post-implementation review needs: a check that
never shares history with the code it's reviewing, performed by something that literally cannot
edit the files it's reading. The two aren't competing choices for the same step; they're the
right tool for two different steps in the same workflow, composed inside one Skill's phase
flow. `logging-reviewer` reading three modules' worth of diff also never has to happen in the
main session's own context — it happens in the subagent's isolated window, and only a short
verdict comes back, which is the same context-isolation benefit `strategy-reviewer` gave Lab 4,
just triggered *from inside* a Skill instead of by hand.
