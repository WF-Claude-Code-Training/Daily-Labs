# Appendix (optional) - Workflows: the delegation you just did by hand, as a script

> **Skip-safe.** This appendix is optional and nothing in Lab 7's Definition of Done depends on
> it. The Workflow tool is a newer capability and may not be enabled in your environment. If
> it isn't, read Parts A and D, the ideas transfer, and move on without penalty. **Confirm with
> your TA before spending lab time on setup.**

---

## Part A: What a workflow is, and what it isn't

Everything you've done in Labs 4-7 you drove yourself: you decided which role got which ticket,
you read each report, you decided what came next. That's correct for work where the next step
depends on what the last step found.

A **workflow** is for the other case: when you already know the shape of the work and the only
question is coverage. It's a JavaScript script that spawns subagents deterministically:
`pipeline()`, `parallel()`, phases, JSON-schema-validated returns. Control flow lives in code,
not in a model's judgment.

**What it is:** a way to fan out across many items or dimensions, verify each result
independently, and take on scope one context window couldn't hold. Reviews, audits, migrations
across hundreds of call sites, research sweeps.

**What it isn't:** a way to make your pair-programming loop faster. If you arrive expecting
speed on a single bounded task, you'll be disappointed. And you'll have spent a lot of tokens
finding out. The return is *coverage and confidence*, not latency.

The honest summary: **a workflow is worth it when you'd otherwise have to choose between being
thorough and being finished.**

---

## Part B: Run the one that ships with this lab

`.claude/workflows/audit-review.js` reviews your WM-109 diff across four dimensions at once,
then tries to *refute* every finding before it reaches you.

**Prerequisite:** finish Part 2's logging work first. A workflow reviewing an empty diff finds
nothing and teaches nothing.

Workflows require explicit opt-in. Claude will not start one on its own, by design. Ask for it
in as many words:

> *"Run the audit-review workflow against the WM-109 logging changes."*

Read the script before you run it. It's ~140 lines and the comments explain each decision. Four
things in it are worth understanding, because they're the transferable part:

1. **Four dimensions, not four copies of one reviewer.** `coverage`, `noise`, `scope`, and
   `reconstructability` each get a prompt that's blind to the others. One reviewer asked to
   check four things in sequence runs out of attention on the fourth; four reviewers asked one
   thing each don't.
2. **`pipeline()`, not `parallel()`.** There's no barrier between reviewing and verifying, so
   `coverage`'s findings start getting verified while `reconstructability` is still reading.
   A barrier would idle every fast reviewer until the slowest finished.
3. **Adversarial verification.** Each finding goes to two independent skeptics told to *refute*
   it, and to default to "refuted" when uncertain. A reviewer reading quickly produces
   plausible-sounding findings; this is what stops them reaching you dressed as confirmed ones.
4. **It reports what it dropped.** The return value includes `refuted` and `refuted_count`, not
   just survivors. A review that silently discards findings reads as "nothing else was wrong."

---

## Part C: Compare it against what you built by hand

You now have two reviews of the same diff. Put them side by side:

| | `logging-reviewer` + `risk-officer` | `audit-review` workflow |
|---|---|---|
| Findings raised | | |
| Findings that survived scrutiny | | |
| Found by one and not the other | | |
| Roughly what it cost | | |
| How long you waited | | |

Then answer the question that actually matters: **which findings did the workflow surface that
your two reviewers didn't, and were they worth the cost?**

Be willing to conclude no. On a three-file diff, two well-written reviewer subagents may well
match a four-dimension fan-out for a fraction of the tokens, and knowing that is more useful
than assuming more agents is better. The number that changes the answer is scale: at three
files, hand-driven review wins on cost. At three hundred, it isn't a competition, because you
were never going to read three hundred files.

---

## Part D: When you'd reach for one at work

Shapes from your own codebases where this pays off:

- **Migration**: a signature change across 400 call sites. Discover the sites, transform each
  (in an isolated git worktree so they can't collide), verify each independently. Exactly Lab 5's
  exercise, at a scale where doing it by hand isn't an option. This is the single most
  defensible use of the tool.
- **Audit**: "which of our 60 services log PII?" One agent per service, structured findings,
  adversarial verification, one synthesis.
- **Judge panel**: three independent designs for a hard change, scored by independent judges,
  then synthesize from the winner while grafting the best of the runners-up. Beats
  one-design-iterated when the solution space is wide.

And the caveats, which you should be the one to raise when someone asks you about this:

- **Token cost is real.** Dozens of agents per run. A cohort all running one simultaneously is a
  capacity conversation, not a footnote.
- **Explicit opt-in, always.** Nothing spawns a workflow on your behalf. That's a feature.
- **Scripts are plain JavaScript**, not TypeScript, no type annotations. `Date.now()` and
  `Math.random()` are unavailable inside them (they'd break resume); pass timestamps in as args.
- **A workflow is not a substitute for a contract.** Four reviewers with vague prompts produce
  four vague reports, in parallel, for four times the price. Everything you learned in Labs 4-6
  about writing a contract is the input to this, not an alternative to it.

---

## Stretch

1. **Add a fifth dimension**: retention (`is anything here going to sit in a seven-year archive
   that shouldn't?`). One entry in `DIMENSIONS`, and the fan-out and verification come free. Note
   how little the script changed: that's the actual argument for encoding delegation as code.
2. **Make verification stricter and watch the finding count drop.** Change two skeptics to three
   and require a majority rather than unanimity to refute. Which findings come back? Were they
   real?
3. **Point it at Lab 5.** Its four dimensions become `missed callers`, `over-migration`,
   `keyword consistency`, `back-compat`. Nothing about the script's structure is specific to
   logging. Write the `DIMENSIONS` array and reuse everything else.
