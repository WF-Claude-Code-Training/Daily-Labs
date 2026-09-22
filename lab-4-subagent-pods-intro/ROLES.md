# The role pod: how the three shipped roles work, and the one you'll write

You're about to stop asking Claude Code to do things and start **staffing a team**. This is the
org chart: what each role is for, what it can and can't do, and what it hands off.

Three of these roles ship with the lab, already written, in `.claude/agents/`. Read them: each
explains its own design decisions inline, and they're the templates for the fourth, which is
yours to write.

`check_pod.py` is the machine-readable half of this document:

```bash
python3 check_pod.py     # 3 [ok] + 1 [FAIL] on a fresh checkout
```

---

## Why roles instead of one conversation

A single conversation doing everything has three problems that better prompting doesn't fix:

1. **It reviews its own work.** It has a stake in the reasoning that produced the code, and will
   defend a shortcut it invented forty messages ago.
2. **It carries everything.** Reading six files to trace a dependency leaves six files in your
   context for the rest of the session, whether you need them or not.
3. **It has every tool, always.** "Please don't edit the fee tiers" is a request. A reviewer
   without `Edit` is a control.

A pod addresses all three by construction. The cost is that you now have to design the
hand-offs, which is the actual skill this lab teaches.

---

## The two kinds of boundary

This is the most important distinction in the lab, and `check_pod.py` labels every role with it.

### Tool-enforced

`contract-reviewer` has `tools: Read, Grep, Glob`. It genuinely **cannot** edit your code:
there's no `Edit`, no `Write`, and critically no `Bash`, because `python3 -c "open(...).write(...)"`
is an edit. That holds regardless of what permission mode your main session is running in, and
regardless of what the role is asked to do.

### Contract-only

`implementer` has `Edit`. It's told "never edit a test file." `test-author` has `Edit` too, and
it's told "never edit source."

**Neither of those is enforceable with a `tools:` list**, because a tools list gates tool
*types*, not file *paths*. There is no way to write "Edit, but only `test_*.py`."

These contracts work, mostly: the roles are narrow, the instructions are specific, and a
well-described role follows them. But "mostly" is doing real work in that sentence, and you
should know which of your guardrails depends on it.

> This gap is why Lab 7 exists. A `PreToolUse` hook runs *before* a tool call and can deny it
> based on the file path and the content of the proposed change. That's the layer that turns
> "please don't touch the fee tiers" into something that cannot be done. Keep this gap in mind
> when you get there, it'll make the hook feel less like a party trick.

---

## The three shipped roles

### `implementer` - `Read, Edit, Bash` · contract-only

| | |
|---|---|
| **Job** | Make an existing verifiable target pass. Nothing else. |
| **Why it acts** | It's the exception to "subagents are reviewers and explorers." `Edit` + `Bash` let it close a loop: change code, run tests, read the failure, change again, that would otherwise cost the main conversation a round trip per iteration. Repetitive work with a mechanical success condition is exactly what's worth handing to an agent that can act. |
| **Hands off** | The diff, the test output, and what it deliberately left alone. |
| **Its contract** | Never edit a test file. Never edit another team's reference data. Stay in the named files. Never guess a value that isn't defined somewhere. |
| **Judgment** | Passing the given tests is necessary, not sufficient. If it had to special-case a fixture to go green, that's a finding, not a win. |

### `test-author` - `Read, Write, Edit, Bash` · contract-only

| | |
|---|---|
| **Job** | Turn acceptance criteria into failing tests, and repair tests that a source change has made untrue. |
| **Why the second job matters** | An implementer with a red test has two ways to make it green: change the code, or change the test. The first is the job. The second is how a suite quietly stops meaning anything. Separating them means a test change is always a deliberate act by something whose only concern is whether the suite tells the truth. |
| **Hands off** | Tests that fail for the right reason, and one line each on what they pin down. |
| **Its contract** | Never edit source to make a test pass. Never weaken a test, no deleted assertions, loosened tolerances, or added skips, to make it agree with broken code. |
| **Judgment** | A test that restates the implementation is not a test. Pin the *contract*: what a caller observes. |

### `contract-reviewer` - `Read, Grep, Glob` · **tool-enforced**

| | |
|---|---|
| **Job** | Review a finished change against the ticket's acceptance criteria and guardrails, independently. |
| **Why read-only** | A reviewer that can patch what it finds leaves no record that the finding existed. In a regulated shop the *finding* is an artifact, not just the fix. |
| **Hands off** | One line per criterion (pass/fail + why), then **APPROVED** or **CHANGES NEEDED**. No softening a failing item to reach APPROVED. |
| **Judgment** | It should be able to say "the tests pass and this is still wrong." If it can't, its checklist is too shallow. |

---

## The role you'll write

### `reference-data-steward` - read-only, **tool-enforced**

| | |
|---|---|
| **Job** | Answer one question about a diff: *could the team who owns this data change it without an engineer and a release?* |
| **Tools** (enforced) | Needs `Read` and `Grep`. Must **not** have `Edit`, `Write`, `MultiEdit`, `Bash`, or `Task`. |
| **Why that budget** | It judges whether a value belongs in code or in configuration, a judgment it would corrupt by being able to move the value itself. |
| **Hands off** | A list of values that are hardcoded but shouldn't be, each with the team that should own it, then a verdict. |
| **Judgment** | Not every constant belongs in a file. `SPLIT_NOTIONAL_TOLERANCE` is an engineering tolerance; `KNOWN_SPLIT_RATIOS` is business reference data that changes when a company announces a split. Telling those apart is the entire role: a steward that flags every constant is noise. |

**Why this role and not another:** "could Ops do this without us?" *is* WM-115's acceptance
criterion. The role you author in Part 3 does real work on the ticket you do in Part 4. Use
`contract-reviewer` as your template, it's the closest shape.

---

## The hazard nobody warns you about

**Subagents share one working tree.** They do not get private copies of the repo. Two roles
holding `Edit` and running at the same time will overwrite each other, and the loser's work is
gone with no error message.

`check_pod.py` prints a `[WARN]` when more than one required role can `Edit`, which it will,
because both `implementer` and `test-author` can. That warning isn't a failure. Sometimes you
genuinely need two editors across a session. It's a reminder that *you*, not the model, are
responsible for never having both live at once.

> **Fan out reads and reviews. Serialize edits.**

---

## Stretch: a fifth role

Once the pod is green, the interesting question is which role is still *missing*.
`escalation-auditor` is the strongest candidate: read-only, and its only job is the WM-106
invariant: every input symbol lands in exactly one verdict, nothing silently dropped. Every
ticket in this epic could break that, and no other role is specifically looking.

Add its contract to `ROLE_CONTRACTS` in `check_pod.py`, author it, and prove it catches something
the other four missed. **A role that never disagrees with the pod is overhead**, and finding
that out is a legitimate result worth reporting.
