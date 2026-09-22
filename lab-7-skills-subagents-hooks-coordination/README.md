# Day 2 · Lab 7: Build the Enforcement Layer

> **Standalone package.** This folder is a self-contained copy of Lab 7 from a larger Claude
> Code training course. Open this folder directly as your VS Code / editor workspace root, then:
> ```bash
> pip install -r requirements.txt
> ```
> All commands below assume you're running them from this folder. (One stretch goal, see the
> end, has you copy a file in from `../lab-4-subagent-pod-intro/`; nothing required depends on it.)

> **Environment notes.** If `python3` isn't on PATH (common on Windows), substitute `py -3` or
> `python`. If `pip install` fails behind corporate proxy, confirm the proxy environment
> variables or internal package index with your TA before the session. If it fails with
> `error: externally-managed-environment` (PEP 668), rerun with `pip install --user -r
> requirements.txt` or `--break-system-packages`.

> **Recap.** Lab 4 had you staff a pod and ship a four-ticket epic on one module. Lab 5 had you
> map a change's blast radius and migrate a signature across six files. Both were about
> **getting work done through roles**. This lab is about the layer underneath: what happens when
> "don't touch that" has to be true even when someone is having a bad afternoon.
>
> You'll hold all three kinds of control at once: a **Skill** that carries the procedure, two
> **subagents** that supply independent judgment and disagree with each other, and **hooks** that
> enforce guardrails deterministically.
>
> Same arc as Lab 4: one working hook ships with this lab, tested and wired, for you to read and
> run. Then you write the second one yourself.

---

## The epic: WM-109, both halves

> *"When compliance asks 'why did this fee/escalation/alert happen,' there's nothing to query.
> Add a shared structured-logging abstraction and thread it through `fees.py`, `reconcile.py`,
> and `drift.py` so every fee calculation, every reconciliation exception, and every fired drift
> alert is logged as a structured (JSON) event, not printed, not silently dropped."*

Read that again and notice what it doesn't ask for. It says *emit*. It says nothing about the
analyst being able to **ask a question and get an answer**, which is the entire reason anyone
wanted this. A trail nobody can query is a disk-space bill.

So the epic is three things:

| # | Ask | Verifiable target |
|---|---|---|
| **1** | Thread the shared structured logger through the three modules | `test_logging.py` |
| **2** | Make the trail answerable: `audit_query.py` | `test_audit_query.py` |
| **3** | Make the guardrail enforceable: a `PreToolUse` hook | `test_protected_regions_hook.py` |

Ticket text is in `backlog/`. **42 tests. 30 failing when you start**: the 12 that pass include
the 9 belonging to the worked-example hook, which is already finished.

### Definition of done

1. `python3 -m pytest` fully green: logging, audit query, and both hooks.
2. Your hook is wired in `.claude/settings.json` and **you watched a hook deny a real edit** and
   read the reason it gave. (Both hooks can do this; do it at least once with yours.)
3. `python3 check_pod.py` exits 0: `risk-officer`.
4. `logging-reviewer` and `risk-officer` both reviewed the change, **you can name one thing they
   disagreed about**, and you recorded how you adjudicated it.
5. The Skill's own checker passes for all three domains.

> **Four verifiable targets.** Three test suites for the feature, `check_pod.py` for the
> framework. The fifth check, that your two reviewers disagreed about something real, is
> deliberately not automatable, and that's worth noticing.

---

## What's already built vs. what you'll build

| Already built | Your turn |
|---|---|
| `agentic_framing/logging_utils.py`: `get_logger()`, `StructuredLogger`, `capture_log_events()` | Thread it through. Nothing here needs editing |
| `fees.py`, `drift.py`, `reconcile.py`: working domain logic from earlier labs | Add the log calls named in `test_logging.py` |
| `.claude/skills/structured-logging-rollout/`: a multi-file project Skill (`SKILL.md`, `reference.md`, a checker script) | Use it. Read `reference.md` once before your first log call |
| `.claude/agents/logging-reviewer.md`: a pre-built read-only conformance reviewer | Don't skip it, but don't mistake it for sufficient |
| `.claude/hooks/no_print.py` + `test_no_print_hook.py` (**9 passing**): a complete, wired, tested hook | Read it. It's the worked example, and deliberately the *opposite shape* to yours |
| `.claude/hooks/protected_regions.json`: the registry of protected snippets, with reasons | **Read-only.** This is policy. Consume it; don't edit it to get past a denial |
| `test_protected_regions_hook.py`: 6 tests, the hook's full contract | **Write `.claude/hooks/protected_regions.py` and wire it in `settings.json`** |
| `fixtures/audit_trail.jsonl`: a captured night's output, 12 events and 3 junk lines | Build `audit_query.py` against it |
| `test_logging.py`, `test_audit_query.py`: seeded failing | Make them pass |
| `ROLES.md` + `check_pod.py` | Author `risk-officer` |

> `.claude/settings.json` wires **one** hook, the worked example. Adding the second is your
> job. Note that `stock_split_adjustment` is still stubbed here and `drift.py`'s hysteresis TODO
> is still open; both belong to other labs and neither blocks this one.

---

## Part 1: See what's missing (target: 10 minutes)

```bash
python3 -m pytest -q
```

**30 failing, 12 passing.** Sort them once so the numbers mean something:

| Suite | State | What it is |
|---|---|---|
| `test_no_print_hook.py` | **9 pass** | The worked-example hook. Already done, read it in Part 2 |
| `test_protected_regions_hook.py` | **6 fail** | The hook you write |
| `test_logging.py` | **5 fail**, 2 pass | The logging rollout |
| `test_audit_query.py` | **19 fail**, 1 pass | The query tool |

That sorting *is* your plan, and it's faster than writing one.

Then read `agentic_framing/logging_utils.py`. It's short, and the whole interface is:

```python
from agentic_framing.logging_utils import get_logger

logger = get_logger("fees")          # -> logs under "agentic_framing.fees"
logger.info("fee_calculated", aum=aum, fee=fee)
```

---

## Part 2: The enforcement layer, read one, then write one (target: 35 minutes)

Do this **before** the logging work, not after. That ordering is the point of the lab: a
guardrail that arrives after the risky change is a post-mortem, not a control.

Read [`ROLES.md`](ROLES.md)'s three-layer table first: Skill / subagent / hook, and the test for
deciding which layer a guardrail belongs in.

### 2a. Read the worked example (10 minutes)

`.claude/hooks/no_print.py` is a complete, wired, tested hook. It enforces the part of WM-109
everyone skims past: events must be "logged as a structured (JSON) event, **not printed**." A
`print()` added to a domain module during a logging rollout is always wrong, and now it's
impossible in the three modules the ticket names.

```bash
python3 -m pytest test_no_print_hook.py -v      # 9 passing
```

Read both files. Four things in them are the mechanics you'll reuse:

1. **The interface.** PreToolUse event as **JSON on stdin**. **Exit 0** = allow, **exit 2** =
   block with the reason on **stderr**. Claude Code feeds stderr back to the model, so that
   message is a prompt, not a log line. Notice that `no_print.py`'s denial names the
   alternative (`get_logger`) rather than just refusing.
2. **How it's tested.** As a subprocess, against copies in `tmp_path`, asserting on exit codes.
   Never by importing its functions. Test the real interface. `test_protected_regions_hook.py`
   uses the identical shape.
3. **A fail-open decision, made explicitly and then asserted.** Every "can't tell" path in
   `no_print.py` returns 0, the docstring says why, and a test pins it down.
4. **A limitation written down rather than discovered.** The check is a regex, not an AST walk,
   and the docstring says exactly what walks past it and why that's an acceptable trade *for
   this guardrail*.

### 2b. Watch it deny you (5 minutes)

Tests prove the logic. They don't prove Claude Code is actually invoking the hook, that's
wiring, and the only way to check it is to try:

> *"In `fees.py`, add a print statement showing the AUM and calculated fee so I can see it while
> debugging."*

Watch the denial. Read the reason. **That round trip: a request, a deterministic refusal, and a
reason the model has to work around, is the thing you came here to see.** A hook that passes
tests but has never denied you anything is a hook you don't yet trust.

### 2c. Now write yours (20 minutes)

Read `.claude/hooks/protected_regions.json`: three snippets, each with a reason: the fee-tier
table in `fees.py`, the `DEFAULT_STRATEGIES` tuple in `reconcile.py`, the hysteresis condition in
`drift.py`. Each is logic an earlier lab got right and this ticket has no business touching.
WM-121 in `backlog/` is the postmortem explaining why prose wasn't enough.

Your job: `.claude/hooks/protected_regions.py`, wired as a second `PreToolUse` hook in
`.claude/settings.json`. `test_protected_regions_hook.py` is the complete contract.

**Yours is the harder shape, and that's deliberate:**

| | `no_print.py` (given) | `protected_regions.py` (yours) |
|---|---|---|
| Asks | does the change **add** something forbidden? | does the change **remove** something required? |
| Needs | only the text being introduced | the **simulated result** of the change vs. what's on disk |
| Policy lives in | a constant in the code | `protected_regions.json`, owned by someone else |

That middle row is the work. To know whether a protected snippet *survived*, you have to work
out what the file will look like after the call: apply `old_string` → `new_string` for `Edit`,
walk the list for `MultiEdit`, take `content` wholesale for `Write`, then check the snippet is
still there. Reading the tool input alone can't tell you.

Four things the contract pins down that are easy to get wrong:

- **Block** (exit 2, reason on stderr) when a protected snippet would be removed or altered.
- **Allow** a `logger.info(...)` call inserted *immediately adjacent* to a protected region. The
  snippet boundaries in the registry were chosen to make this possible. A hook that blocks the
  intended change is a hook that gets disabled on day one.
- Allow edits to files with no registry entry, and unrelated edits to protected files.
- Handle `Write`, `Edit`, **and** `MultiEdit`.

Two decisions the tests *don't* make for you. Decide deliberately and be ready to defend both:

1. **Fail open or fail closed?** `no_print.py` fails open, and its docstring argues why: it's one
   layer among several, so a miss gets caught downstream. **Yours protects something different**:
   a silently mispriced fee table that review already missed once. Same question, possibly a
   different answer.
2. **Text or AST?** A substring check is ~80 lines and will block a semantically identical
   reformat. An AST comparison is correct and much larger. Pick one, and write down what you gave
   up, the way `no_print.py` does.

```bash
python3 -m pytest test_protected_regions_hook.py -v
```

Then deny yourself again, this time with your own hook:

> *"While you're in `drift.py`, go ahead and fix the hysteresis TODO."*

> **Third-layer thread from Lab 4.** In Lab 4, `check_pod.py` labelled `implementer` and
> `test-author` **contract-only**, asked, not prevented, from crossing the test/source line,
> because a `tools:` list gates tool types and not file paths. What you just built is the
> expression that gap was missing. Hooks can also be scoped to a single subagent rather than the
> whole session (see this lab's Stretch goal 5), which is precisely how you'd close Lab 4's gap
> for real.

## Part 3: Thread the logging through, via the Skill (target: 25 minutes)

`.claude/skills/structured-logging-rollout/` is a **multi-file** Skill: `SKILL.md` (the
workflow), `reference.md` (naming conventions and worked examples, loaded only when you're about
to write a log call), and `scripts/verify_structured_logs.py` (a checker run via Bash, so its
logic never enters your context, only its pass/fail output does).

Skill selection isn't guaranteed to happen implicitly. Write your own five-ingredient frame
before you type anything, ask for the Skill by name, and **tell it to run Phase A only**: you
review the plan before it edits three files in one pass.

> **This is what checkpoints/rewind is for.** Three files in one pass is exactly the shape where
> you want to be able to reject one file's diff without re-running the whole thing. Review each
> diff before accepting it.

---

## Part 4: Two reviewers, and a disagreement (target: 20 minutes)

`logging-reviewer` ships with this lab and checks **conformance**: event names, field
conventions, routine paths staying silent, nothing else in the diff. Read its checklist.

Now author `risk-officer` (contract in `ROLES.md`). It asks a different question: is this trail
*adequate for an audit?* Could an analyst reconstruct the decision in twelve months, or only the
outcome? `position_escalated` with a `risk_level` says what happened. Does anything say why?

Run both.

**They should disagree**, and the collision is legitimate on both sides: the clearest case is a
field that would make the trail genuinely more reconstructable but isn't in `reference.md`'s
table. Conformance says no. Audit sufficiency says yes.

You don't resolve that by picking your favorite reviewer, and absolutely not by loosening a
checklist until it agrees. You resolve it by deciding and **recording the decision**: either
extend the convention (update `reference.md`, and now both reviewers agree for the right reason)
or accept the gap and write down why.

> Two reviewers that never disagree are one reviewer you're paying for twice. If yours agree on
> everything, make them collide on purpose and adjudicate it. That adjudication is the
> deliverable for this part.

---

## Part 5: Make the trail answerable (target: 25 minutes)

`test_audit_query.py` is the contract for `audit_query.py`. The compliance question driving all
20 tests is one sentence: *"show me every HIGH-risk escalation from the 2am run."*

`fixtures/audit_trail.jsonl` is a captured night's output, supplied so this half can be built
and verified **independently of Part 3**: if you're behind on the logging work, you can still
ship this. It contains 12 valid events and three lines that are not: a blank line, a
log-rotation marker, and a truncated write. Real log files contain all three.

Two requirements in that suite are worth reading closely before you start, because they're the
difference between a script and a tool someone trusts:

- **Skipping a malformed line is correct. Skipping it silently is not.** If three lines don't
  parse, that has to be *reachable and visible*, or nobody can distinguish "quiet night" from
  "half the file didn't parse."
- **A query with no filters returns everything.** A tool whose default is "nothing" gets used
  wrong on the first try and trusted less forever after.

Once it works, answer the actual question against your own output rather than the fixture:

```bash
python3 -m pytest test_logging.py -q                    # generate real events
python3 audit_query.py fixtures/audit_trail.jsonl --event position_escalated --risk-level HIGH
python3 audit_query.py fixtures/audit_trail.jsonl --summary
```

---

## Part 6: Verify & deliver

```bash
python3 .claude/skills/structured-logging-rollout/scripts/verify_structured_logs.py fees.py reconcile.py drift.py
python3 -m pytest -v
python3 check_pod.py
```

Hand back:

1. Your hook, and the two design decisions from Part 2c (fail-open vs fail-closed, text vs AST)
   with your reasoning, and where you landed differently from `no_print.py`.
2. The denial *your* hook gave when you asked for an off-scope edit, quoted.
3. The three log calls, and any decision point you deliberately chose **not** to log.
4. Both reviewers' verdicts, **one thing they disagreed about**, and how you adjudicated it.
5. `audit_query.py` answering the HIGH-risk escalation question.
6. All 42 tests green, `check_pod.py` at 0, the Skill's checker clean.

---

## Optional appendix: Workflows

[`WORKFLOW-APPENDIX.md`](WORKFLOW-APPENDIX.md) runs the same review as a four-dimension fan-out
with adversarial verification, and has you compare it against what your two reviewers found by
hand. **Entirely optional**: nothing above depends on it, and the tool may not be enabled in
your environment. Check with your TA before spending lab time on it.

---

## Guardrails

1. **Don't edit `.claude/hooks/protected_regions.json`.** It's policy, owned by whoever sets the
   guardrail. If your hook denies something legitimate, the bug is in your hook.
2. **Don't disable or weaken either hook to get past a denial**, not yours, and not
   `no_print.py`. If you find yourself wanting to, that's the lab working: say what you were
   trying to do and whether the denial was right or wrong. "I needed a quick print to debug" is
   the single most common reason a guardrail like this gets removed in real codebases, which is
   exactly why it's worth sitting with the friction once.
3. **Don't change what the three functions return or how they decide.** Logging only. This is
   guardrail 1's whole reason for existing.
4. **Don't log a routine/no-op outcome**: an exact `MATCHED`, a drift check within threshold.
   That's volume, not an audit trail, and you'll be paying to store it for seven years.
5. **Never log raw PII.** These three modules don't carry any today. The guardrail travels with
   the Skill to the next module, which might.
6. **Both reviewers are read-only by design.** If one flags something, fix the module. Don't
   grant `Edit` or `Bash` to either, and don't soften a checklist to reach APPROVED.
7. **One editor at a time.** Three files, shared working tree.
8. `stock_split_adjustment` stays stubbed and drift's hysteresis TODO stays open. They belong to
   other labs. Trying to fix them is what Part 2's hook exists to stop.

---

## Stretch goals

1. **Break your own hook.** Find an edit that alters protected logic but that your hook allows.
   A whitespace reformat of the fee-tier table? Rewriting it with the same values via `MultiEdit`
   in two steps? Then decide whether to close the gap or document it as accepted, a hook with a
   known, written-down limitation is stronger than one with an assumed-perfect reputation.
   Then do the same to `no_print.py`, which tells you in its own docstring how to beat it.
2. **Argue yourself out of a hook.** `ROLES.md` names two candidates ("never log PII", "don't
   widen scope"). Try to write the deterministic check for one, then explain why you wouldn't
   ship it. A framework is defined as much by what it declines to enforce as by what it blocks.
3. **Make the reviewers disagree on something harder.** Get `risk-officer` to flag a *missing
   field* that `logging-reviewer` would reject as a convention violation, then extend
   `reference.md` so both approve for the right reason. You've now changed a team standard, not
   just a file.
4. **Add the retention question.** Nothing in this lab asks how long the trail is kept or what
   happens when it's queried in year six. Add a `risk-officer` criterion for it and see whether
   your own implementation survives its own reviewer.
5. **Close Lab 4's gap for real: an agent-scoped hook.** Everything so far has been
   session-scoped: wired in `settings.json`, applying to every tool call. A hook can instead be
   attached to **one subagent**, in its frontmatter:

   ```yaml
   hooks:
     PreToolUse:
       - matcher: "Edit|Write|MultiEdit"
         hooks:
           - type: command
             command: "python3 .claude/hooks/tests_are_not_mine.py"
   ```

   This needs `implementer`, which isn't part of this lab's required pod (it does no work here
   otherwise). Bring it in first:

   ```bash
   cp ../lab-4-subagent-pod-intro/.claude/agents/implementer.md .claude/agents/
   ```

   (No sibling `lab-4-subagent-pod-intro/` folder? Re-author it from its contract in Lab 4's
   `ROLES.md`, same file either way.)

   Write the hook and attach it to `implementer`, so the "never edit a test file" rule that was
   **contract-only** in Lab 4 becomes tool-enforced for real. Then ask `implementer` to edit a
   test and watch it fail where in Lab 4 it merely declined. This is the most satisfying twenty
   minutes in the lab if you have them.

6. **Take the framework out of the lab.** Point `check_pod.py` at a repo you actually work on
   (inside Day 1's approved access path) and write the three-layer table for it: which of that
   repo's guardrails are Skills, which are subagents, and which genuinely deserve a hook. Bring
   the answer to Lab 8, it's the strongest possible input to that lab's one-pager.

---

## Why this matters

- **A hook is the only guardrail that isn't a request.** A Skill can be skipped. A reviewer can
  be wrong or talked around. A `PreToolUse` denial happens before the tool runs and doesn't
  negotiate. That's why it's reserved for guardrails where a well-meaning mistake is
  unrecoverable, and why hooking everything is a mistake of its own.
- **Hooks come in two shapes, and one is much harder.** Asking "does this change add something
  forbidden?" needs only the text being introduced. Asking "does this change remove something
  required?" means simulating the result and comparing it against what's on disk. You read the
  first and built the second; most real guardrails are the second kind.
- **Choosing the layer is the design work.** Convention → Skill. Judgment → subagent.
  Unrecoverable → hook. Getting this wrong in either direction has a cost: under-enforce and
  you're relying on diligence; over-enforce and people route around the framework.
- **Two reviewers earn their keep by disagreeing.** Conformance and sufficiency are different
  questions and one reviewer optimizing for both will quietly favor whichever is easier to
  check. The disagreement is the signal; adjudicating it is your job, not theirs.
- **"Emit the events" was never the requirement.** The requirement was that someone could ask a
  question and get an answer. A ticket that stops at the mechanism is a ticket that will be
  reopened, and noticing that before you write code is most of what senior means here.
- **Skipping a malformed line silently is how audits fail.** Not dramatically, just a number
  nobody could reconstruct, in a file everyone assumed was complete.
