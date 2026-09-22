# The role pod, part two: a full feature through five roles

Lab 4 built a pod for **one module** and ran one ticket through it: `test-author`,
`implementer`, `contract-reviewer`, all project-scoped, all checked into that repo. This lab
runs a full feature's lifecycle through the pod instead: investigate, migrate, extend,
document. That surfaces two things Lab 4's single-ticket shape never had to answer: *who
owns a role across repos*, and *what happens on a ticket a role doesn't fit*.

`check_pod.py` came with you from Lab 4. It's the same script; only the default pod differs:
including the **tool-enforced vs contract-only** labels it prints. `impact-mapper` and
`release-scribe`, below, are both tool-enforced. `implementer`, `test-author`, and
`contract-reviewer`, carried forward from Lab 4, keep whatever label they had there. Copying a
role doesn't change its contract.

```bash
python3 check_pod.py                 # impact-mapper, release-scribe, implementer, test-author, contract-reviewer
python3 check_pod.py --scope both    # searches ~/.claude/agents/ too (the default here)
```

### Where each role actually does something, this lab

| Role | WM-114 (migrate) | WM-118 (extend) |
|---|---|---|
| `impact-mapper` | maps the blast radius before anyone edits | **not used**: nothing to map, no signature changes |
| `release-scribe` | writes `impact_note.md` | not used |
| `implementer` | migrates all six files | builds `statement_delta` against `test-author`'s tests |
| `test-author` | not used (no test goes stale) | **writes the acceptance tests from scratch**, its only such scene all day |
| `contract-reviewer` | reviews the migration (+ the over-migration criterion) | reviews the implementation |

No row has every cell filled, on purpose. A pod that reaches for every role on every ticket
regardless of fit hasn't learned anything from Lab 4's "not every ticket needs all four."

---

## Project scope vs. personal scope

This is a **distribution** decision, not a capability one. Both kinds of subagent get the same
isolated context, the same enforced tool list, the same everything at runtime. What differs is
who else has it and where the cost lands:

|  | `.claude/agents/` (project) | `~/.claude/agents/` (personal) |
|---|---|---|
| **Who gets it** | anyone who clones the repo | only you, in every repo on your machine |
| **Reviewed by** | your team, in a PR | nobody |
| **Cost** | loaded in sessions on this repo | loaded in **every** session you ever start |
| **Right for** | a role encoding *this codebase's* rules | a habit you want everywhere |

`contract-reviewer` from Lab 4 is project-scoped and should stay that way. Its checklist
encodes what "done" means for that repo's tickets. `impact-mapper` is the opposite: tracing a
function's callers has nothing to do with this toy portfolio package, and you'll want it in
every codebase you touch for the rest of your career.

That's the test. Not "is it useful?", everything useful, but **"would this role make sense in
a repo I haven't seen yet?"** If yes, personal. If it only makes sense here, project.

> **The cost of personal scope is real.** Every personal subagent's `description` is loaded into
> every session on your machine from now on. Three good ones sharpen every project you open.
> Fifteen mediocre ones are a tax you pay forever and a menu Claude has to disambiguate every
> time you ask for anything.

---

## The roles for this lab: two new, three carried forward

### `impact-mapper`: **personal scope** (`~/.claude/agents/`) · tool-enforced

| | |
|---|---|
| **Job** | Given a target function, find every caller, **direct and transitive**, and report them as two separate lists, naming the file each lives in. Plus what the change provably does *not* reach. |
| **Tools** (enforced) | Needs `Read`, `Grep`, `Glob`. Must **not** have `Edit`, `Write`, `MultiEdit`, or `Bash`. |
| **Why that budget** | It runs *before* anyone touches code, to decide whether the change is safe to attempt. A mapper that can edit has already skipped the decision it exists to inform. |
| **Hands off** | Two lists (direct, transitive) with file references, and an explicit "not reached, because…" section. |
| **Judgment** | The direct list is the part `grep` gets right. **The transitive list and the not-reached list are the entire value of the role.** If it reports only direct callers, it has told you nothing you couldn't have gotten in one keystroke. |

### `implementer`, `test-author`, and `contract-reviewer`: carried forward from Lab 4

 **copied**, as files, from
`../lab-4-subagent-pod-intro/.claude/agents/`. See README.md Part 2 for the exact commands.

`implementer` does two jobs here: migrates all six files against `test_backdated_statements.py`
in Part 4, then builds `statement_delta` against whatever `test-author` writes in Part 5. Its
Lab 4 contract, never edit a test, never guess a value, stay inside the named files, travels
with it unchanged across both.

`test-author` sits out Part 4 entirely (no test goes stale, because the migration doesn't touch
`DEFAULT_STRATEGIES`-shaped state) and does its **first** job for the first time all day in
Part 5: originating tests from a ticket, not repairing one a change made stale. Same contract as
Lab 4, never touch source, never weaken a test to make it pass, pointed at different work.

`contract-reviewer` reviews both: the migration (with one addition to its checklist, see
**over-migration**, below) and the extension.

**This is the friction personal scope buys you out of, made concrete.** Both are project-scoped,
so neither exists in this repo until you physically put a copy here. Compare that against
`impact-mapper`, next: the moment you author it, it's usable in *every* project on your
machine, this one included, no copy required.

### `release-scribe`: project scope · tool-enforced

| | |
|---|---|
| **Job** | Turn the finished migration into the artifact other teams read: what moved, what didn't, what a caller has to do differently (here: nothing, and saying so explicitly is the point). |
| **Tools** (enforced) | Needs `Read`, `Write`. Must **not** have `Edit` or `MultiEdit`. |
| **Why that budget** | It creates new documents. Denying `Edit` keeps a documentation pass from quietly becoming a code pass: the failure mode where a scribe "fixes a typo" in a docstring and changes behavior. |
| **Hands off** | `impact_note.md`, passing `python3 check_impact_note.py impact_note.md`. |
| **Judgment** | A note that lists files is a diff. A note that tells the advisor team *whether their integration breaks* is a release note. Write the second one. |

---

## Over-migration: the failure mode with no error message

Every migration has two ways to be wrong, and teams only ever guard against the first:

1. **A caller you missed.** Loud. Something breaks, a test fails, you fix it.
2. **A caller you changed that didn't need changing.** Silent. Every test passes. The diff looks
   thorough. You have permanently added a parameter that no caller can ever meaningfully vary,
   and the next engineer has to work out whether it means something.

`target_weights` in `allocation.py` is this lab's instance of #2. It returns a static profile;
it has no pricing in it at all, directly or transitively. Threading `as_of_date` through it
would pass every behavioral test in the suite.

So `contract-reviewer` needs a criterion for it: **"every signature that changed, needed to
change."** A reviewer that only checks for missed callers will approve an over-migration every
time. `test_backdated_statements.py` pins this one case down, but the *habit* is the deliverable.
The next migration won't come with a test that guards the negative.

---

## Serializing a six-file migration

The one-editor rule from Lab 4 gets harder here, because six files genuinely need editing and
the temptation to parallelize is strong. The call graph gives you the order for free:

```
pricing.py  →  allocation.py  →  rebalance.py / fees.py / drift.py  →  statements.py
```

Migrate **in dependency order**, bottom-up, verifying as you go. Each layer's tests can pass
before the next layer is touched, so a failure tells you which layer broke it. Fan out `Read`
across all six at once. That's free and it's what `impact-mapper` is for. Edit one at a time.

> `rebalance.py`, `fees.py`, and `drift.py` are siblings. None depends on another. They are the
> one place in this migration where concurrent edits would be safe. Decide deliberately whether
> the coordination overhead is worth it for three small files, and be able to defend the answer.

---

## Stretch: a role that argues with the map

Once the pod is green, the sharpest addition is a role whose job is to **distrust
`impact-mapper`**: given the map, try to find a caller it missed, or a "not reached" claim that
is actually reached. Add its contract to `ROLE_CONTRACTS` in `check_pod.py`, author it
read-only, and run it against a map you already believe.

If it never finds anything on a six-file package, that is a legitimate result. Say so, and
note what size of codebase would change your answer. A verifier that can't fail on a toy
problem hasn't been proven useless; it just hasn't been tested yet.
