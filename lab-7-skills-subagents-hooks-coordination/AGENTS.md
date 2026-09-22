# Claude Code session guide: Lab 7 (standalone)

You (Claude Code) are working with a Wells Fargo Wealth Management engineer on **Day 2, Lab 7**
of an 8-lab Claude Code training course. This folder runs on its own: no access to the rest of
the course repo, and no GitLab access, is required or expected.

**This lab is about the enforcement layer.** Labs 4 and 5 got work done through roles. Here the
engineer holds all three kinds of control at once: a Skill carrying the procedure, two subagents
supplying independent judgment, and `PreToolUse` hooks enforcing guardrails deterministically,
and has to decide which control a given guardrail belongs in.

Same arc as Lab 4: **one hook ships working, then they write the second.**

- `.claude/hooks/no_print.py`: complete, wired in `settings.json`, 9 passing tests in
  `test_no_print_hook.py`. It blocks adding a `print()` to a guarded module. This is the worked
  example; point at it freely.
- `.claude/hooks/protected_regions.py`: **theirs to write.** Do not write it for them unasked
  and do not paste a solution. The design decisions inside it (fail-open vs fail-closed, text
  matching vs AST) are the exercise, and `no_print.py` deliberately models *one* answer to each
  so they have something to agree or disagree with.

The two hooks are opposite shapes on purpose: `no_print.py` asks "does this change **add**
something forbidden?" (needs only the new text), theirs asks "does this change **remove**
something required?" (needs the simulated post-edit file compared against disk). If asked for
help, explain that difference rather than handing over code. It's the crux of the exercise.

## The epic

WM-109 (logging), WM-120 (audit query), WM-121 (protected-region hook). Tickets in `backlog/`,
lab flow in [README.md](README.md). 42 tests, 30 seeded failing across four suites: the fourth,
`test_no_print_hook.py`, ships passing as the worked-example hook (see Part 2).

## The shared standard: the five-ingredient task frame

1. **Outcome**: the end state, not the keystrokes.
2. **Scope**: the concrete target and boundaries.
3. **Verification**: how "done" is checked (four test suites, `check_pod.py`, the Skill's
   checker, and two reviewer verdicts).
4. **Deliverable**: the reviewable artifact handed back.
5. **Guardrails**: what NOT to do, and when to stop and ask.

## The three layers, and how to pick one

| Layer | Artifact | Use when | Example here |
|---|---|---|---|
| Workflow | Skill | It's a repeatable procedure | event naming conventions |
| Judgment | Subagent | It needs an opinion | "is this path routine?" |
| Enforcement | Hook | A well-meaning mistake would be unrecoverable | the fee-tier table |

If asked to enforce something that's really a matter of judgment, say so. An over-broad hook
gets disabled the first time it's inconvenient, and then nothing is enforced.

## Delegation posture for this lab

- **Order matters: the hooks come before the logging work.** A guardrail added after the risky
  change is a post-mortem. If the engineer starts with Part 3, mention it once.
- **Let them watch a hook deny them.** Part 2b asks for a `print()` in `fees.py` on purpose, and
  Part 2c asks to "fix the hysteresis TODO." Both should be denied. Don't route around a denial,
  don't suggest disabling the hook, and don't pre-emptively refuse the request yourself. Attempt
  it, let the hook fire, and read the reason back. The round trip is the lesson.
- **Two reviewers, different jobs.** `logging-reviewer` (pre-built) checks conformance.
  `risk-officer` (the engineer authors it) checks audit sufficiency. If you're asked to write
  `risk-officer` and its checklist comes out looking like `logging-reviewer`'s, that's a failed
  role. Flag it rather than shipping a duplicate.
- **When the reviewers disagree, don't resolve it for them.** Surface both positions clearly.
  The adjudication is the engineer's deliverable, and "loosen a checklist until it agrees" is
  never the answer.
- **Never let the implementing context review its own diff.**
- **One editor at a time.** Three files, shared working tree.

## How to work in this folder

- **Domain is Wealth Management**: advisory fees, custodian reconciliation, allocation drift,
  and compliance audit trails. Keep examples in that world.
- **Files:**
  - `fees.py` / `reconcile.py` / `drift.py`: the three targets. Add a module-level logger and
    the log calls `test_logging.py` names. Nothing else changes.
  - `agentic_framing/logging_utils.py`: `get_logger()`, `StructuredLogger`,
    `capture_log_events()`. Infrastructure; don't edit it.
  - `audit_query.py`: **does not exist yet**; WM-120 creates it. `test_audit_query.py` imports
    from it and drives its CLI via subprocess.
  - `fixtures/audit_trail.jsonl`: a captured night's output: 12 valid events, 3 lines that are
    not (blank, rotation marker, truncated write). Don't "clean" it; surviving it is the point.
  - `.claude/hooks/no_print.py`: the **worked example**: complete, wired, tested. Blocks adding
    a `print()` to `fees.py`/`reconcile.py`/`drift.py`. Its policy list lives in code on purpose
    (it changes when the ticket changes); contrast with the registry below.
  - `test_no_print_hook.py`: 9 tests, **passing on a fresh checkout**. Also the template for how
    a hook gets tested: subprocess, JSON on stdin, assert exit codes, copies in `tmp_path`.
  - `.claude/hooks/protected_regions.json`: the registry of protected snippets, with reasons.
    **Read-only.** This is policy owned by someone else, which is why it's a file and not a
    constant. If the hook denies something legitimate, fix the hook.
  - `.claude/hooks/protected_regions.py`: **does not exist yet**; WM-121 creates it. Wire it as
    a second `PreToolUse` hook in `.claude/settings.json`, alongside `no_print.py`.
  - `test_protected_regions_hook.py`: the hook's full contract. It runs the hook as a
    subprocess with PreToolUse JSON on stdin and asserts on exit codes: `2` = blocked (reason on
    **stderr**, which is what gets fed back to the model), `0` = allowed.
  - `.claude/skills/structured-logging-rollout/`: multi-file Skill: `SKILL.md`, `reference.md`
    (read once before the first log call), `scripts/verify_structured_logs.py` (run via Bash;
    don't read its source into context).
  - `.claude/agents/logging-reviewer.md`: the pre-built conformance reviewer.
  - `.claude/workflows/audit-review.js`: the optional appendix. Requires explicit opt-in and may
    not be available in this environment; never start it unprompted.
  - `ROLES.md`: the three-layer model and `risk-officer`'s contract, plus why this lab doesn't
    use `contract-reviewer`. `check_pod.py`: validator; `risk-officer` is the only role it
    requires by default (`implementer` matters only for the optional stretch goal that attaches
    a hook to it: don't route required work to a role this lab hasn't asked for).
- **Verify with scripts, not by eye:**
  ```bash
  python3 -m pytest test_no_print_hook.py -v          # the worked example — already green
  python3 -m pytest test_protected_regions_hook.py -v  # the hook they write
  python3 -m pytest test_logging.py -v
  python3 -m pytest test_audit_query.py -v
  python3 -m pytest -v
  python3 check_pod.py
  python3 .claude/skills/structured-logging-rollout/scripts/verify_structured_logs.py fees.py reconcile.py drift.py
  ```

## Guardrails

- Don't change what `annual_advisory_fee`, `reconcile_positions`, or `check_drift_alert` return,
  or how they decide. Logging only.
- Don't touch the fee-tier table, the reconciliation strategies, or the drift hysteresis
  condition. `stock_split_adjustment` stays stubbed and the hysteresis TODO stays open. They
  belong to other labs, and the hook exists to stop exactly this.
- Don't edit `.claude/hooks/protected_regions.json`, and don't unwire or weaken **either** hook
  to get past a denial, including `no_print.py`. A denial is the system working. If a denial
  blocks something genuinely legitimate, say so and stop; don't route around it.
- Don't log a routine/no-op outcome (an exact `MATCHED`, a drift check within threshold).
- Never log raw PII. Not applicable to today's fields; it travels with the Skill to the next
  module.
- In `audit_query.py`: a malformed log line is skipped, never fatal, and never silently. The
  count of unparsed lines must be reachable and surfaced, or nobody can tell a quiet night from
  a half-parsed file.
- Both reviewer subagents are read-only by design. Fix the module; don't widen their tools.

## Why this lab is a Skill *and* subagents *and* a hook

The same three-line ask, "thread structured logging through these files", recurs every time
this app grows a module. Packaging the **implementation** as a Skill means the conventions travel
with the workflow instead of living in one lab's instructions. Packaging the **review** as
subagents means it's never done by the conversation that wrote the code, and never costs the
main session the context to perform. Packaging the **guardrail** as a hook means it holds when
someone is tired, the diff is three files wide, and the reviewer is looking at something else,
which, per WM-121's postmortem, is exactly when it failed last time.

It also closes a gap this course left open on purpose. In Lab 4, `implementer`'s "never edit a
test file" was **contract-only**: a `tools:` list gates tool types, not file paths. A hook is
the expression that was missing, and Lab 7's stretch goal 5 has the engineer attach one to a
single subagent to prove it.

All three are project-scoped and committed, so the next engineer to clone this repo gets the
whole framework, not a description of one.
