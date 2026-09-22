# Day 2 · Lab 4: Meet the Pod, Then Add to It

> **Standalone package.** This folder is a self-contained copy of Lab 4 from a larger Claude
> Code training course. Open this folder directly as your VS Code / editor workspace root, then:
> ```bash
> pip install -r requirements.txt
> ```
> All commands below assume you're running them from this folder.

> **Environment notes.** If `python3` isn't on PATH (common on Windows), substitute `py -3` or
> `python`. If `pip install` fails behind corporate proxy, confirm the proxy environment
> variables or internal package index with your TA before the session. Don't spend lab time
> debugging network config. If it fails with `error: externally-managed-environment` (PEP 668,
> common on Homebrew/Linux system Python), rerun with `pip install --user -r requirements.txt`
> or `pip install --break-system-packages -r requirements.txt`.

> **Recap, and what changes today.** Day 1 was about framing one bounded task well: Plan mode, a
> verifiable target, test-driven delivery, you in the loop for every step. That's the floor you
> build on. Today the shape changes: you stop being the person who does every step and become the
> person who **staffs the work and owns the contract**.
>
> The pattern is the same one Labs 1 and 2 used for Skills. There, you were handed a working
> `SKILL.md`, you read it, you used it, and *then* you authored one. Here you're handed three
> working **subagent roles**, you read them, you watch them complete a bug fix together, and then
> you author a fourth.

---

## Part 0: Warm-up, confirm your environment (target: 5 minutes)

```bash
python3 -m pytest -q
```

You should see **18 failing, 14 passing**. That's correct. Most of those failures are work you
haven't done yet. Sort them once so the numbers mean something:

| Suite | State | What it is |
|---|---|---|
| `test_reconcile.py` | 13 pass, **1 fails** | The existing contract. The failure is the demo in Part 2 |
| `test_reconcile_epic.py` | **6 fail** | WM-115, the ticket you run through the pod in Part 4 |
| `test_reconcile_stretch.py` | **11 fail**, 1 passes | WM-116 + WM-117, optional, skip freely |

---

## Part 1: Read the pod (target: 20 minutes)

Three roles ship with this lab, already written, in `.claude/agents/`. Read all three. They are
the worked examples you'll imitate in Part 3, and each one explains its own design decisions
inline.

| Role | Tools | What it does |
|---|---|---|
| **`implementer`** | `Read, Edit, Bash` | Changes source to make a failing test pass, then verifies |
| **`test-author`** | `Read, Write, Edit, Bash` | Turns criteria into failing tests; repairs tests a change made untrue |
| **`contract-reviewer`** | `Read, Grep, Glob` | Reviews the finished diff against acceptance criteria, independently |

Then check them:

```bash
python3 check_pod.py
```

Three `[ok]` lines and one `[FAIL]`: `reference-data-steward` doesn't exist yet. That's Part 3.
Read the rest of the output too; there's more in it than pass/fail.

### The three things worth discussing before you move on

**1. `implementer` takes action. Most subagents don't.**

Every subagent you saw on Day 1 was read-only: a reviewer or an explorer. `implementer` has
`Edit` and `Bash`, and that's deliberate: it closes a loop (change code → run tests → read the
failure → change again) that would otherwise cost the main conversation a round trip per
iteration. Repetitive work with a mechanical success condition is exactly what's worth handing
to an agent that can act.

**2. A `tools:` list gates tool *types*, not file *paths*.**

`check_pod.py` labels `contract-reviewer` **tool-enforced** and `implementer`/`test-author`
**contract-only**, and the distinction is the most important thing in this lab.

`contract-reviewer` genuinely *cannot* edit your code. No `Edit`, no `Write`, no `Bash`, and
`Bash` matters most, because `python3 -c "open(...).write(...)"` is an edit. That restriction
holds no matter what permission mode your main session is in.

`implementer` is told "never edit a test file" and `test-author` is told "never edit source." Both
are **contracts written in prose**, because no `tools:` list can express "Edit, but only these
paths." They work, mostly, because the roles are narrow and well-described. They are not
guarantees.

> Sit with that gap. It's the reason Lab 7 exists: a `PreToolUse` hook is the layer that turns
> "please don't touch the fee tiers" into something that cannot be done.

**3. Subagents share one working tree.**

They don't get private copies of the repo. Two roles holding `Edit` and running at the same time
will overwrite each other, and the loser's work is gone with no error message. `check_pod.py`
prints a `[WARN]` about exactly this, because both `implementer` and `test-author` can edit.

> **Fan out reads and reviews. Serialize edits.**

---

## Part 2: Watch the pod fix a bug (target: 25 minutes)

This is the demo. Prompts are supplied here. The point is to see a real three-role hand-off end
to end before you're asked to design one. Run each step yourself and read what comes back.

**The bug:** `test_stock_split_auto_resolves` fails. `stock_split_adjustment` in `reconcile.py`
is stubbed to always return `False`, so reconciliation escalates a 2-for-1 stock split it should
be able to explain. Read the test and the stub's docstring first.

### Step 1: `implementer` writes the fix

> *"Have the implementer subagent make `test_stock_split_auto_resolves` pass. The stub is
> `stock_split_adjustment` in `reconcile.py`; its docstring has the rule. Follow the pattern of
> the three working strategies. Acceptance criteria: the test passes, no other test regresses,
> and no split ratio outside `KNOWN_SPLIT_RATIOS` is ever accepted. Then add the strategy to
> `DEFAULT_STRATEGIES`."*

Read its report, especially the "what I deliberately did not change" section. Then:

```bash
python3 -m pytest -q
```

**The target test passes, and a different test is now failing.** Don't fix it yet. Look at what
broke: `test_default_strategies_are_the_three_known_normalizations` asserts there are three
strategies. There are now four. **The test was right yesterday and is wrong today**, and nothing
about the implementation is at fault.

Notice what `implementer` did when it hit this: it reported the failure rather than editing the
test. That's its contract, and it's the whole reason the next step is a different role.

### Step 2: `test-author` repairs the stale test

> *"Have the test-author subagent repair `test_default_strategies_are_the_three_known_normalizations`
> in `test_reconcile.py`. A fourth strategy was added, so the test's name and its assertion are
> both now untrue. Keep the coverage it was protecting. Don't delete it or make it vague."*

```bash
python3 -m pytest -q
```

Green except the two suites you haven't started.

> **Why this is two roles and not one.** An implementer with a red test has two ways to make it
> green: change the code, or change the test. The first is the job. The second is how a test
> suite quietly stops meaning anything. Splitting them means every test change is a deliberate
> act by something whose only concern is whether the suite tells the truth.

### Step 3: `contract-reviewer` reviews it

> *"Have the contract-reviewer subagent review the `stock_split_adjustment` implementation and
> the `DEFAULT_STRATEGIES` change against these criteria: the strategy never accepts a ratio
> outside `KNOWN_SPLIT_RATIOS`; it verifies notional value (`qty * price`) is unchanged within
> `SPLIT_NOTIONAL_TOLERANCE` rather than checking qty or price alone; it follows the existing
> strategy pattern; nothing outside the new function and its `DEFAULT_STRATEGIES` entry changed."*

Read the verdict. If it comes back **CHANGES NEEDED**, route the fix back to `implementer`. The
reviewer cannot patch anything, by design. Then re-run and re-review.

If it comes back **APPROVED** on the first pass, ask it the question that matters: *what did you
check that `pytest` didn't?* A reviewer that only confirms what the test runner already told you
is costing tokens for nothing.

---

## Part 3: Author the fourth role (target: 20 minutes)

Now you write one. The contract is in [`ROLES.md`](ROLES.md); the file is yours.

**`reference-data-steward`**: read-only. It answers one question about a diff: *could the team
who owns this data change it without an engineer and a release?* That question is the acceptance
criterion for the ticket you're about to do, which is why this is the role worth having.

Use the three you just read as templates. `contract-reviewer` is the closest shape: read-only,
checklist-driven, returns a verdict.

```bash
python3 check_pod.py
```

Iterate to exit 0. It will push back on things that are easy to get wrong: a missing `tools:`
line (which grants **every** tool and makes the restriction imaginary), a reviewer that quietly
holds `Bash`, a `description` too vague for Claude to ever match against a task.

### Then test delegation both ways

- **Explicit**: name the role. Guaranteed.
- **Proactive**: describe a task *without* naming a role and see which one Claude picks.

If your new role never gets picked proactively, the `description` is the bug, not Claude's
judgment. A description that says what the role *is* ("reviews config") loses to one that says
*when to reach for it* ("use before closing any ticket that moves a hardcoded value into a file
another team maintains"). `check_pod.py` enforces a length floor for exactly this reason: length
is a crude proxy for specificity, and it's the only part a script can check.

---

## Part 4: Run a real ticket through the pod (target: 20 minutes)

No prompts supplied. That's the exercise.

**WM-115**: `backlog/WM-115-split-reference-data.md`. Read it. It's written the way tickets
actually arrive: a symptom, a vague ask, and no statement of what must keep working. Reframing it
is the first thing you do.

`test_reconcile_epic.py` (6 failing tests) is the acceptance contract. Read it before you plan.
It answers a question the ticket doesn't: what reconciliation should do at 2am when the file Ops
maintains is missing or malformed.

What you owe the ticket:

1. **Reframe it**: outcome, scope, verification, deliverable, guardrails.
2. **Route it**: which roles, in what order. Not every ticket needs all four; deciding is part
   of the work.
3. **Review the verdict, not the vibe**: including `reference-data-steward`'s, since "could Ops
   do this without us?" *is* this ticket's acceptance criterion.

Two things that are where teams lose the most time:

- **The seam already exists.** `reconcile_positions` accepts `strategies=` today. This ticket is
  an exercise in *using* a seam, not cutting a new one. Have a role read the signature before
  anyone proposes an architecture.
- **There's a back-compat trap, and the suite tests for it.** A caller who passes no reference
  data must keep today's exact behavior. Widening a default is how you silently change every
  existing caller.

### The payoff: run it (and verify both paths)

**Part of WM-115 verification:** Both commands below are required acceptance tests. The second
command uses the `--reference-data` flag to load Ops-maintained split ratios. This flag is part
of the verification process for agents completing Part 4.

**Code changes required for `--reference-data` support:**

`run_reconcile.py` must be updated to:
1. Import `load_split_ratios` and `build_strategies` from `reconcile`
2. Add an optional `--reference-data` argument to the argument parser
3. When the flag is provided:
   - Call `load_split_ratios(path)` to load ratios from the JSON file
   - Call `build_strategies(split_ratios=...)` to construct the strategy tuple with loaded ratios
   - Pass `strategies=...` to the `triage()` function
4. When the flag is omitted:
   - Call `triage()` with no `strategies` argument (uses default `DEFAULT_STRATEGIES`)
5. Print a message indicating how many ratios were loaded and from where

This ensures both the back-compat path (no flag) and the new Ops-enabled path (with flag) work correctly.

**Without reference data** (back-compat, today's behavior):
```bash
python3 run_reconcile.py fixtures/book_positions.csv fixtures/custodian_file.csv
```
→ ORCL escalates (3 resolved, 4 escalated). Ratio `1.5` is not in the compiled-in table.

**With Ops-loaded reference data** (WM-115, the change):
```bash
python3 run_reconcile.py fixtures/book_positions.csv fixtures/custodian_file.csv --reference-data reference_data/split_ratios.json
```
→ ORCL now resolves via `stock_split_adjustment` (4 resolved, 3 escalated). Ops added the `1.5`
ratio to the JSON file, no code change needed.

**Verification checklist for agents:**
- [ ] Update `run_reconcile.py` to accept `--reference-data` flag
- [ ] Run without `--reference-data` flag and verify ORCL escalates (back-compat path)
- [ ] Run with `--reference-data reference_data/split_ratios.json` and verify ORCL resolves
- [ ] Compare outputs: ORCL should move from ESCALATED → RESOLVED when reference data is loaded
- [ ] Confirm both runs complete without errors

**The moment of truth:** Compare the two outputs. ORCL moves from ESCALATED to RESOLVED. That's
WM-115 working. Ops can change reference data without an engineer and without a release.

That escalation in the first run was **correct** on Day 1 and it still is. A 3-for-2 ratio (`1.5`)
wasn't in the table, nothing reads free text, and auto-resolving on a press-release note would
have been a guess.

What WM-115 changes is *who can clear it, and how fast*: the ratio is now data Ops owns.

You didn't make the system guess better. You shortened the path from "a human knows the answer"
to "the system knows it too" from a release to a data change. Say that out loud when you present.
It's the whole ticket.

---

## Part 5: Deliver

1. What each of the three shipped roles is for, and why `contract-reviewer`'s restriction is
   enforced where `implementer`'s is not.
2. The Part 2 hand-off: what `implementer` did when its fix broke a passing test, and why that
   was correct.
3. Your `reference-data-steward` definition, and `check_pod.py` exiting 0.
4. One proactive delegation that worked, and one that didn't until you rewrote the `description`.
5. WM-115 reframed, shipped, and reviewed, with `contract-reviewer`'s verdict.
6. `python3 -m pytest test_reconcile.py test_reconcile_epic.py -q` green.
7. The ORCL before/after, and one sentence on why the original escalation was still correct.

---

## Guardrails

1. **Don't edit `reference_data/*.json`.** Ops and Risk own those files. Your code consumes
   whatever is in them, including a missing or malformed file, which WM-115's contract covers
   and does *not* answer with "raise."
2. **Don't break `test_reconcile.py`.** It's green after Part 2 and must stay that way.
3. **Don't widen a default to make a test pass.** A new capability that changes behavior for
   callers who didn't ask for it is a regression wearing a feature's clothes.
4. **Never guess a ratio, rate, or band that isn't in a reference table.** The escalate-rather-
   than-guess rule from Day 1 isn't relaxed by having a config file. It's why the file exists.
5. **`contract-reviewer` and `reference-data-steward` are read-only by design.** If one flags
   something, fix the code. Don't loosen its checklist, and don't grant it `Bash` so it can
   "just fix it."
6. **One editor at a time.** See Part 1.

---

## Stretch goals

Ordered by how much they'll teach you, not by difficulty. **None are required**: if you're
short on time, stop after Part 5 with a clean conscience.

1. **Make a reviewer disagree with a green suite.** Get `contract-reviewer` to flag something
   real while `pytest` is fully passing. Hint: hardcode a value the ticket said Ops should own,
   and see whether your checklist catches it. A reviewer that only ever agrees with the test
   runner is overhead.
2. **Break the contract-only boundary on purpose.** Ask `implementer` to edit a test to make it
   pass. Note whether it refuses, and note that nothing *stopped* it. Write down what control
   would have. Then keep that answer for Lab 7.
3. **WM-116 and WM-117**: `test_reconcile_stretch.py`, 11 failing tests. WM-117 is the more
   interesting of the two because it needs a **new file**; notice which of your roles is even
   able to create one, and what that implies about your hand-off.
4. **Author a fifth role: `escalation-auditor`.** Read-only, verifies the WM-106 invariant
   across every change: every input symbol lands in exactly one verdict, nothing silently
   dropped. Add its contract to `ROLE_CONTRACTS` in `check_pod.py`, then prove it catches
   something the other four missed. A role that never disagrees with the pod is overhead.
5. **Cause a real conflict.** Run two editing roles concurrently on `reconcile.py` and watch the
   working tree lose an edit. Do it deliberately, with a clean `git status` first so you can
   recover, then design the hand-off that prevents it.

---

## Why this matters

- **A role is a control; a prompt is a request, but only sometimes.** `contract-reviewer` cannot
  edit your code; that's a property of the system. `implementer` is *asked* not to edit tests;
  that's a property of how well the role is written. Knowing which of your guardrails is which
  is the difference between a framework and a wish.
- **The hand-off is the work.** Part 2's interesting moment isn't either agent's output: it's
  the seam between them, where a broken test became someone else's job. Most of today's failures
  will be hand-off failures, not coding failures.
- **Independence is what you're buying, not speed.** A reviewer in its own context, with no
  memory of writing the code and no ability to change it, catches a class of problem no
  conversation reviewing its own diff ever will.
- **Configuration is a governance decision, not a refactor.** WM-115 moves a value from code into
  a file another team owns. That changes who can act, how fast, and who's accountable when it's
  wrong, which is why `reference-data-steward` exists as a role and not a checklist item.
- **Escalating what you can't verify is still correct.** The feature wasn't "guess better." It
  was "let the people who know tell us." Those are different systems with different risk
  profiles, and the second one is the one you can defend in an audit.
