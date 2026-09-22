# Day 2 · Lab 5: Investigate, Migrate, Extend, Document: Ship a Feature Through the Pod

> **Nearly standalone.** This folder's code and tests need nothing from the rest of the course
> repo. Its role pod is a different story: Part 2 has you copy three files in from
> `../lab-4-subagent-pod-intro/.claude/agents/`, so this folder needs to sit where it normally
> does, as a sibling of `lab-4-subagent-pod-intro/` inside the same checkout. If you only have this
> folder in isolation, see the note in Part 2 for the fallback. Setup:
> ```bash
> pip install -r requirements.txt
> ```
> All commands below assume you're running them from this folder.

> **Environment note.** If `python3` isn't on PATH (common on Windows), substitute `py -3` or
> `python`. If `pip install` fails with `error: externally-managed-environment` (PEP 668), rerun
> with `pip install --user -r requirements.txt` or `--break-system-packages`.

> **Recap, and what's actually different about this lab.** Lab 4 staffed a pod and ran one
> ticket through it, on one file. In this lab, you run a **full feature
> lifecycle** through the pod: **investigate** a change's blast radius before touching anything,
> **migrate** existing code safely across six files, **extend** it with something genuinely
> new, and **document** what moved. This lab is the first time anything new gets
> built, and it's built by a role (`test-author`) that's had exactly one scene all day and has
> never once done its first job until now.

---

## The two tickets, one arc

**WM-114**: advisors need to reissue a client statement as of a prior date. One parameter, on
the smallest function in the package (`get_price`), but the ripple crosses six files, two of
which never mention pricing in their own bodies. This is the **investigate + migrate** half.

**WM-118**: now that a backdated statement exists, advisors are asking a different question:
*"what changed between this date and that one?"* Nothing here exists yet. This is the
**extend + document** half, and it's the one ticket all day with no test file waiting for you.

Read both in `backlog/` before you start either. They arrive in the order a real feature
actually does: change something safely, then build the thing people actually asked for on top
of it.

### Definition of done

**Investigate + migrate (WM-114):**
1. A personal subagent at `~/.claude/agents/` traces a target function's callers, direct and
   transitive, across a codebase, and Claude has delegated to it **without being told its
   name** at least once.
2. `python3 -m pytest test_backdated_statements.py` is green: 19 tests, including the eight
   that were **already passing before you started** and must stay that way.
3. `impact_note.md` names every direct and transitive caller, states which function this change
   does *not* reach and why, and `python3 check_impact_note.py impact_note.md` passes.
4. A backdated statement renders, states its own as-of date on its face, and does not leak a
   single value from today.

**Extend + document (WM-118):**
5. `test-author` wrote the acceptance tests for `statement_delta` **from the ticket, before any
   implementation existed**, not from a pre-written spec. There isn't one.
6. `python3 check_statement_delta.py` passes, a floor, not the full spec. `test-author`'s own
   tests should cover more than it does; naming what they cover that the checker doesn't is
   part of the deliverable.
7. `contract-reviewer` reviewed WM-118 and can state, in one sentence, why `impact-mapper` had
   nothing to do on this ticket.

**Framework:**
8. `python3 check_pod.py` exits 0: `impact-mapper`, `release-scribe`, `implementer`,
   `test-author`, `contract-reviewer`.

> **Five verifiable targets.** `test_backdated_statements.py` checks the migration.
> `check_statement_delta.py` checks the new feature's floor. `check_impact_note.py` checks the
> note. `check_pod.py` checks your roles. If you're wondering which to trust when they disagree:
> they can't. They cover different things.

---

## What's already built vs. what you'll do

| Already built | Your turn |
|---|---|
| `pricing.py`, `allocation.py`, `rebalance.py`, `fees.py`, `drift.py`, `statements.py`: a small, real call graph | Migrate `as_of_date` through it, in dependency order (WM-114) |
| `reference_data/price_history.json`: end-of-day marks the pricing team maintains | Consume it. Don't edit it, one test asserts it agrees with `pricing.py` |
| `test_backdated_statements.py`: **19 tests, 11 failing.** WM-114's acceptance contract | Read it *before* you plan. It answers questions the ticket doesn't |
| `check_impact_note.py`: the note checker | Nothing to change here |
| `statement_delta.py`: a stub, `NotImplementedError`. **No test file exists for it.** | Have `test-author` write the tests, then implement it (WM-118) |
| `check_statement_delta.py`: a floor-level checker, not a spec | Pass it, then notice what it doesn't cover |
| `ROLES.md` + `check_pod.py`: role contracts, carried from Lab 4 | Author `impact-mapper` (personal) and `release-scribe` (project) |
| *(nothing, project-scoped roles don't follow you here on their own)* | Copy `implementer`, `test-author`, and `contract-reviewer` in from Lab 4's `.claude/agents/`, see Part 2 |

---

## Part 1: Orient, five minutes, not a deep dive

Six files, in call-graph order:

```
pricing.py  →  allocation.py  →  rebalance.py / fees.py / drift.py  →  statements.py
```

Skim them. This is the "map before you touch" habit itself: a quick pass for shape and
direction before committing to trace anything in detail. Form a rough expectation you can check
your mapper's report against in Part 3; that comparison is the only way you'll ever know whether
the role is any good.

Notice on the way past that `statements.py`'s `build_statement` never mentions pricing anywhere
in its own body. Keep it in mind.

---

## Part 2: Staff the pod, two authored, three carried forward (target: 25 minutes)

Read `ROLES.md`. It defines `impact-mapper` (personal scope) and `release-scribe` (project
scope), with contracts and no file contents. Author both.

**Then bring the three project-scoped roles forward from Lab 4**: `implementer` migrates
WM-114 and later builds WM-118; `test-author` originates WM-118's tests; `contract-reviewer`
reviews both. This folder has no `.claude/agents/` yet, so create it before copying into it:

```bash
mkdir -p .claude/agents
cp ../lab-4-subagent-pod-intro/.claude/agents/implementer.md .claude/agents/
cp ../lab-4-subagent-pod-intro/.claude/agents/test-author.md .claude/agents/
cp ../lab-4-subagent-pod-intro/.claude/agents/contract-reviewer.md .claude/agents/
```

> **If this folder is genuinely isolated** (no `lab-4-subagent-pod-intro/` sibling, e.g. you were
> handed this lab on its own), re-author all three from their contracts in Lab 4's `ROLES.md`
> instead. Either way, notice what you just did: a project-scoped role has to be physically
> copied or rewritten to exist in a new repo. `impact-mapper`, which you're about to author at
> *personal* scope, needs none of this. It's already on your machine and already visible to
> Claude Code here, in every project, the moment you restart. That's the friction personal scope
> is buying you out of, made concrete instead of asserted.

```bash
python3 check_pod.py
```

Iterate to exit 0, five roles this time, not three.

> **One restart, once.** If `~/.claude/agents/` didn't exist on your machine before this session
> started, Claude Code won't notice your new personal subagent until you restart. Restart once
> after creating it, then continue. Later edits are picked up without restarting.

**Then prove delegation works both ways.** Describe the task *without naming the role*:

> *"I'm about to change `get_price`'s signature to add an `as_of_date` parameter. What in this
> codebase would that affect?"*

Watch whether Claude reaches for `impact-mapper` on its own. If it just greps inline instead,
the `description` you wrote is the bug, not Claude's judgment. Rewrite it to say *when to reach
for this role* and try again. Then invoke it explicitly by name and compare: same result,
guaranteed rather than inferred.

**Optional, and worth the two minutes:** check your context indicator (or `/usage`) before and
after delegating. Then ask Claude to trace the same thing inline, reading and grepping all six
files in the main conversation, and compare what each cost you. The isolation is the product.

---

## Part 3: Investigate, map before you touch (target: 15 minutes)

Run `impact-mapper` and read its report against the expectation you formed in Part 1. You want
three things out of it, and only one of them is easy:

- **Direct callers.** The `grep` answer. Fine, but you didn't need a subagent for it.
- **Transitive callers**: functions that never call `get_price` themselves but depend on one
  that does. This is the part a keyword search cannot give you and the reason the role exists.
- **What this change does not reach**, and why.

If the report stops at direct callers, it is wrong, not incomplete. Fix the role and re-run
before you plan anything, because a migration planned off a direct-callers-only map will tell
the advisor team the wrong thing is safe.

Have `release-scribe` turn the map into `impact_note.md`:

```bash
python3 check_impact_note.py impact_note.md
```

All 5 required call sites should be found. Note that the checker is satisfied by *naming* the
call sites, it cannot tell you whether the note is any good. Read it yourself and ask whether
an advisor-team engineer would know, after reading it, whether their integration breaks.

---

## Part 4: Migrate, change existing code safely (target: 35 minutes)

No prompts supplied. You have the map, the contract in `test_backdated_statements.py`, and a
pod, including `implementer`, carried forward from Lab 4, who does the actual editing here.
Route the migration to it rather than writing the diff yourself; that's the point of having
staffed it. Three things to decide before you brief it:

1. **Order.** The call graph gives it to you: migrate bottom-up, `pricing.py` first, verifying
   each layer before touching the next. A failure then tells you *which* layer broke it.
2. **Semantics the ticket doesn't specify.** What does a statement as of a date with no
   end-of-day mark use? What about a date before the history begins? The contract answers both.
   Find those tests and read them before you write code, not after one fails.
3. **What must not change.** Every existing caller, calling exactly as it does today, must get
   exactly today's answer. Eight of the nineteen tests exist only to hold that line. This is why
   `as_of_date` defaults to `None` rather than to today's date: a default that *computes* today
   looks identical until the day the history and the price table disagree.

> **`compute_trades` reaches pricing twice**: directly, to size dollar amounts, and indirectly
> through `current_weights`. Forward the date to only one and the trades come out on the right
> symbols, in the right direction, for the wrong amount. Exactly one test catches it. Find out
> which one, and appreciate that a human reviewer reading that diff almost certainly would not.

`implementer`'s Lab 4 contract already says "stay inside the files your brief names" and
"never guess a value", both apply directly here across six files instead of one. Brief it with
the order and the two semantics questions above; it still owns deciding how to satisfy each test.

Then get it reviewed by `contract-reviewer`. Its Lab 4 checklist is not sufficient here. Add
the criterion `ROLES.md` describes under **over-migration**, and understand why a reviewer
without it will approve a thorough-looking diff that permanently adds a meaningless parameter.

---

## Part 5: Extend, ship something that didn't exist this morning (target: 20 minutes)

Everything so far has been about changing code that already existed, safely. WM-118 is
different: `statement_delta.py` is a stub that raises `NotImplementedError`, and **there is no
test file for it.** Read `backlog/WM-118-statement-comparison.md` and the stub's docstring,
that's the entire spec.

This is deliberate, and it's the one place all day this happens. Every other required ticket in
this course ships with its acceptance tests pre-written, so `implementer` always had something
concrete to satisfy. `test-author`'s actual first job, *turn acceptance criteria into failing
tests*, has had nowhere to happen until now. Its only scene so far (Lab 4, Part 2) was its
*second* job: repairing a test a change made stale. Different job, and this ticket is where you
finally watch the first one.

**Route it in order:**

1. **Reframe the ticket yourself first**: the ticket's own footer asks two open questions
   (which fields matter to an advisor; what "changed" means for a trade whose dollar amount
   moved but symbol and action didn't). Decide both before delegating anything. A vague brief
   handed to `test-author` produces vague tests.
2. **`test-author` writes the tests**, from your reframed brief, not from `check_statement_delta.py`,
   which it should not read as the spec. Read what it produces. Does it test the boundary (same
   date twice, an empty portfolio) or only the comfortable middle?
3. **`implementer` builds `statement_delta`** against `test-author`'s tests.
4. **Verify against the floor, separately:**
   ```bash
   python3 check_statement_delta.py
   ```
   This checks four fixed scenarios with known-correct answers, computed against the real,
   already-migrated fee/trades/drift functions, not worked out by hand. It deliberately does
   **not** check everything the ticket raises (a trade whose amount changed but symbol/action
   didn't is a case it skips on purpose, see its own docstring). If `test-author`'s tests don't
   cover more ground than this floor does, that's a finding, not a pass.
5. **`contract-reviewer` reviews the implementation** against your reframed criteria.

**Notice what's missing from that list: `impact-mapper`.** There's nothing to map: WM-118 adds
a new function that calls existing ones; it doesn't change anything's signature, so there's no
blast radius to trace into. Deciding a role doesn't apply to a ticket is the same skill as
deciding one does. Say why, out loud, when you present.

---

## Part 6: Verify & deliver

```bash
python3 -m pytest -v
python3 check_statement_delta.py
python3 check_pod.py
python3 check_impact_note.py impact_note.md
```

Then render a statement both ways and read them side by side: current, and as of `2026-03-31`.
Confirm the backdated one states its own as-of date and carries no value from today. Run
`statement_delta` across the same two dates for a household with a drift alert and confirm it
reports the alert clearing.

Hand back:

1. Your two authored role definitions, the scope you chose for each, and one sentence on why.
2. `impact-mapper`'s report: direct, transitive, and not-reached.
3. One proactive delegation that worked, and one that didn't until you rewrote the `description`.
4. The migration diff (WM-114), in the order you applied it, and `contract-reviewer`'s verdict
   including the over-migration criterion you added.
5. WM-118's brief, `test-author`'s tests, and one thing they cover that
   `check_statement_delta.py` doesn't.
6. One sentence on why `impact-mapper` wasn't used for WM-118.
7. `impact_note.md`, and all four checks passing.

---

## Guardrails

1. **Don't edit `reference_data/price_history.json`.** The pricing team owns it. One test asserts
   it agrees with `pricing.py`'s current-price table. If that test fails, the bug is in your
   code, not in their data.
2. **Don't break an existing caller.** No positional-argument changes, no required parameters,
   no defaults that compute today's date.
3. **Don't over-migrate.** If a signature didn't need to change, changing it is a finding.
4. **Don't write `statement_delta`'s tests yourself, and don't let `implementer` write them
   either.** That's the entire point of Part 5. If you catch yourself doing it because it's
   faster, that's the lab's actual lesson slipping past you.
5. **`check_statement_delta.py` is a floor, not a target to stop at.** Passing it with no other
   tests is not the same as being done. Say explicitly what `test-author`'s tests add on top.
6. **One editor at a time.** Six files, shared working tree. Fan out reads; serialize edits.
7. **`impact-mapper` and `contract-reviewer` are read-only by design.** If either flags
   something, fix the code. Don't grant them `Edit` to get unstuck.
8. **Don't interpolate a price.** If there's no mark at or before the requested date, that's an
   error, not an opportunity to estimate. A statement is a client-facing document.

---

## Stretch goals

1. **Break the migration on purpose, one call site at a time.** Remove `as_of_date` from a
   single forwarding call and note which tests fail. Do it for each of the six files. You'll
   find at least one place where *nothing* fails. Write the test that should have caught it.
   That gap is the most valuable thing in this lab's migration half.
2. **Build the fuller version of WM-118: a statement-diff report.** `statement_delta` returns a
   dict; advisors want something they can hand a client. Add a `render_statement_diff()` that
   turns the dict into the same kind of plain-text report `build_statement` produces, including
   the case the required floor explicitly skips: a trade present at both dates whose dollar
   amount changed. Decide whether that's a "change" worth surfacing, and have `test-author`
   write a test that pins your decision down before `implementer` builds it.
3. **Author a role that argues with the map.** `ROLES.md` describes it: given `impact-mapper`'s
   report, try to refute it. Run it against a map you already believe.
4. **Migrate the reverse direction.** `check_drift` currently returns symbol names. Suppose the
   advisor UI now needs the drift *percentage* per symbol. Map that change's blast radius with
   your own role, and notice it's a different shape from WM-114: a return-type change breaks
   callers loudly, where a signature addition breaks them silently. Which is safer to ship on a
   Friday, and why?
5. **Take `impact-mapper` somewhere real.** Point it at a repo you actually work on, inside the
   approved access path from Day 1's Data Governance briefing, and trace a function you already
   understand. Personal-scope roles are only worth their permanent context cost if they hold up
   outside the lab that taught them.
6. **Make the note earn its place.** Rewrite `impact_note.md` for an audience that isn't you: an
   advisor-platform engineer who has never opened this repo and needs to know in one read
   whether their integration breaks. Then ask whether `check_impact_note.py` would have caught
   the difference. It wouldn't. That's worth knowing about your verifiable targets.

---

## Why this matters

- **A feature has a lifecycle, not just a diff.** Investigate, change safely, extend, document:
  Lab 4 exercised the middle two on one file; this lab runs all four on a real feature end to
  end. That's the actual escalation from Lab 4, not "you get to author roles too."
- **A pre-written test suite is a hidden assumption, and WM-118 removes it.** Every other ticket
  in this course hands you the spec as a seeded-failing test file. That's right for verifying a
  lab deterministically, and it means `test-author`'s first job never gets to happen anywhere
  else. Noticing that gap, and building the one ticket that closes it, matters more than the
  feature itself.
- **A checker is a floor, and saying so out loud is part of the deliverable.**
  `check_statement_delta.py` passing is necessary and not sufficient, same lesson as a green
  `pytest` run in Lab 4, applied to a hand-written verifier instead of a full suite.
- **Deciding a role doesn't apply is the same skill as deciding one does.** WM-118 has no
  `impact-mapper` moment because there's no blast radius to map. A pod that reaches for every
  role on every ticket regardless of fit hasn't learned the lesson Lab 4 already named once.
- **Transitive impact is still the whole lesson for the migration half.** `build_statement`
  never says "price" anywhere in its own body and is fully exposed. `check_drift` doesn't either.
  A map that stops at direct callers would have told the advisor team the wrong thing was safe.
- **Over-migration has no error message.** A change that threads a parameter everywhere passes
  every test and looks thorough in review. The only thing that catches it is a reviewer with an
  explicit criterion for it, which is why you added one.
- **Personal vs. project scope is a distribution decision, not a capability one.** Both get the
  same isolated context and enforced tools. What differs is who else has the role, who reviews
  it, and that a personal one's description is loaded into every session you start from now on.
