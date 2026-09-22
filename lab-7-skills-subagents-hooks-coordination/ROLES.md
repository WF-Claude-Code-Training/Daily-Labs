# The framework, assembled: three layers of control

Labs 4 and 5 built roles. This lab is where the roles become a **framework**, because it's the
first time you hold all three kinds of control at once and have to decide which one a given
guardrail belongs in.

```bash
python3 check_pod.py     # risk-officer — the only role required for this lab's main flow
```

---

## The three layers

|  | Artifact | What it is | How it fails |
|---|---|---|---|
| **Workflow** | Skill (`.claude/skills/`) | A procedure, written down once, that travels with the repo | Silently, if nobody invokes it. A Skill nobody asks for is a document. |
| **Judgment** | Subagent (`.claude/agents/`) | An independent opinion, in its own context, with its own tool budget | Arguably. A reviewer can be wrong, or shallow, or talked around. |
| **Enforcement** | Hook (`.claude/settings.json`) | A deterministic denial before a tool call runs | Loudly, or not at all. It cannot be reasoned with, which is the point. |

Everything you've built so far has been layers one and two. This lab adds three, and the
important part is not *how* to write a hook. It's learning which guardrails deserve one.

**You already met the gap this closes.** In Lab 4, `check_pod.py` labelled `implementer` and
`test-author` **contract-only**: they were *asked* to stay on their side of the test/source line,
because a `tools:` list gates tool types and not file paths. There was no way to write "Edit, but
only `test_*.py`." A `PreToolUse` hook is that missing expression: it runs before the tool call,
sees the file path and the proposed content, and can refuse. Layer three is not a new idea in
this lab; it's the answer to a question Lab 4 deliberately left open.

**The test:** could a well-intentioned, competent engineer violate this guardrail by accident,
in a way review might miss, with consequences you can't take back? If yes, it's a hook. If it's
a matter of judgment, taste, or a tradeoff someone should weigh, a hook is the wrong tool and
will just get disabled the first time it's inconvenient.

### Two shapes of hook

Once you've decided something deserves a hook, there's a second question, and it determines how
much work you're in for:

| | Additive check | Subtractive check |
|---|---|---|
| Asks | does this change **add** something forbidden? | does this change **remove** something required? |
| Needs | only the text being introduced | the **simulated result** vs. what's on disk |
| Example | `no_print.py` (shipped, read it) | `protected_regions.py` (yours to write) |

The additive one is nearly free: look at `new_string`, match a pattern, decide. The subtractive
one has to work out what the file *will look like* after the call: apply the edit, walk a
`MultiEdit` list, take a `Write` wholesale, and then check the thing you're protecting is still
in it. Reading the tool input alone cannot answer it.

Most guardrails worth having are subtractive, which is why that's the one you build.

### Applied to WM-109

- *"Use `snake_case` past-tense event names"* → **Skill.** A convention. Write it down, follow it.
- *"Don't log a routine no-op path"* → **Subagent.** Needs judgment about what's routine.
- *"Don't alter the fee-tier table while adding logging"* → **Hook.** One careless `Edit` in the
  wrong place mispriced every household's fee. No amount of reviewer diligence makes that
  recoverable, and the guardrail has no legitimate exception during a logging rollout.

That last one is the hook you're going to write. And one more, already written, as your
worked example:

- *"Log events; don't `print()` them"* → **Hook.** WM-109 says it in the ticket, the Skill
  repeats it, and a `print()` during a logging rollout is never the right answer. Deterministic,
  no legitimate exception, trivially checkable. `no_print.py`: read it before you write yours.

---

## `risk-officer`: the role you author

| | |
|---|---|
| **Job** | Ask whether the audit trail is *adequate for an audit*, not whether it follows conventions. |
| **Tools** (enforced) | Needs `Read`, `Grep`. Must **not** have `Edit`, `Write`, `MultiEdit`, or `Bash`. |
| **Why that budget** | A governance reviewer that can quietly fix what it flags destroys the record that the finding existed. In a regulated shop the *finding* is an artifact, not just the fix. |
| **Hands off** | Findings, each tied to a question a compliance reviewer would actually ask, then **ADEQUATE** or **GAPS FOUND**. |
| **Judgment** | Its checklist is about *sufficiency*, not correctness: given only this trail, can you reconstruct why a fee was charged, why a position was escalated, and who would have seen it? If not, name what's missing. |

### Its checklist should be genuinely different from `logging-reviewer`'s

`logging-reviewer` already ships in `.claude/agents/`. Read it first. Its five points are all
**conformance** questions: does the event name match the convention, did a routine path stay
silent, did anything else in the diff change.

`risk-officer` asks different questions, and if you find yourself writing "checks event names"
you've built a second `logging-reviewer` and wasted the slot. Questions that belong to it:

- Could a compliance analyst reconstruct the *decision* from this trail, or only the outcome?
  (`position_escalated` with a `risk_level` tells you what happened. Does anything say *why*?)
- Is there any path where something audit-worthy happens and **nothing** is written?
- Is anything logged that shouldn't be retained at all, and would we know before it's in a
  seven-year archive?
- If this trail is all we have in twelve months, which question can we still not answer?

---

## When your two reviewers disagree

This is the part that's new, and it's the whole reason the lab has two of them.

`logging-reviewer` optimizes for convention. `risk-officer` optimizes for audit sufficiency.
They *will* collide, and the collision is legitimate on both sides: the clearest case being a
field that would make the trail genuinely more reconstructable but isn't in `reference.md`'s
table.

You do not resolve this by picking the reviewer you like better, and you certainly don't resolve
it by loosening one checklist until it agrees. You resolve it by **deciding, and recording the
decision**: either the convention gets extended (update `reference.md`, then both reviewers
agree for the right reason) or the gap is accepted (write down why, so the next person doesn't
rediscover it as a surprise).

> Two reviewers that never disagree are one reviewer you're paying for twice. If yours agree on
> everything, one of their checklists isn't doing any work. Go make them collide on purpose and
> then adjudicate it.

---

## No `contract-reviewer` in this lab, on purpose

Labs 4 and 5 both used `contract-reviewer` as the second review pass. This lab doesn't, and the
reason is worth stating rather than leaving as an omission: this lab's review story is *two
differently-motivated reviewers disagreeing*: `logging-reviewer` (conformance) against
`risk-officer` (audit sufficiency), which you built above. A third, generic reviewer checking
acceptance criteria wouldn't add a perspective; it would just be a fourth pass over the same
diff. Not every lab needs every role. Deciding a role *doesn't* earn its place here is the same
skill as deciding one does.

`implementer` isn't part of this lab's pod either. Nothing here needs it. It shows up once, in
the optional stretch goals, where attaching a hook to a specific subagent is the point rather
than the implementation work itself.

---

## Stretch: the hook you shouldn't write

Once your `protected_regions.py` hook passes its tests, the sharper exercise is picking a
guardrail and arguing yourself *out* of hooking it. Candidates from this lab:

- *"Never log raw PII."* Obviously important. Now try to write the deterministic check. What
  exactly matches? How many false positives before someone turns it off? Is a hook that fires on
  every string field a control, or a nuisance that trains people to ignore denials? Contrast it
  with `no_print.py`, which is the same *shape*, scan added text for a pattern, but where the
  pattern has essentially no false positives. That difference is the whole argument.
- *"Don't widen the scope beyond the three named modules."* Trivially hookable by path. Now ask
  what happens the first time a legitimate fourth module needs logging.

Write down which layer each belongs in and why. A framework is defined as much by what it
declines to enforce as by what it blocks. And "we considered a hook here and chose not to" is a
much stronger position in a design review than never having thought about it.
