# Day 2 · Lab 8 — Put It All Together: Recommend Skills & Subagents for a Real Codebase

> **Standalone package.** This folder is a self-contained copy of Lab 8 from a larger Claude
> Code training course. Unlike Labs 4 and 5, it doesn't ship its own target codebase — it ships
> a small **subagent toolkit** you point at a codebase of your choosing. No dependencies to
> install; `git` and `jq` (used by the read-only hook below) are the only requirements.

> **Recap.** Lab 4 gave you a project-scoped subagent (a reviewer) and had you use it. Lab 5 had
> you author your own, personal-scoped, for exploration. This lab combines both moves: you're
> handed **two** subagents — a mapper and a scout — you run them together, and the synthesis
> (the actual "put it all together" work) is yours to do. The deliverable is a short
> recommendation, not a passing test.

---

## Choose your target

**Option A — your team's own codebase (preferred).** It's likely you already work on shared
code with the people in this room. Recommending real Skills/Subagents for a codebase your team
will actually keep using is worth far more than doing it against a stranger's code.

> **Data governance callout.** Only point these subagents at a codebase that's already inside
> Wells Fargo's approved Claude Code access path — the same rule from Day 1's Data Governance
> briefing applies here, it isn't relaxed for this lab. If your team's repo isn't accessible that
> way in this environment, use Option B.

**Option B — fallback: analyze the course itself.** Point the toolkit at `claude-labs-ttt` (the
repo this folder lives in) or at `lab4-standalone`/`lab5-standalone` for a smaller warm-up. Zero
setup, and you can sanity-check the subagents' findings against labs you've already done.

---

## Part 1: Install the toolkit at your target

Copy this folder's `.claude/agents/` and `scripts/` into the root of the codebase you're
analyzing (or open this folder in Claude Code and use `--add-dir <path-to-target>` to bring the
target codebase into the session instead — either works).

```bash
cp -r .claude/agents scripts /path/to/your/target-codebase/
```

> **One restart, once.** If the target codebase didn't already have a `.claude/agents/`
> directory before you start a Claude Code session there, Claude Code won't notice the new
> subagents until you restart it — restart once after copying, then continue.

Confirm both subagents loaded (`name`, `description`, `tools` — check `pattern-scout`'s `hooks:`
entry specifically) before moving on.

---

## Part 2: Orient, briefly

A five-minute skim of the target's top-level structure — same "map before you touch" habit from
Lab 5. You're not doing the mapping yourself; you're forming a rough expectation to check the
subagents' reports against in Part 4.

---

## Part 3: Fan out both subagents in parallel

Neither depends on the other's output, so run them together rather than one after the other:

> *"Use codebase-mapper and pattern-scout in parallel to analyze [target]. codebase-mapper:
> architecture, entry points, data flow, complexity hotspots. pattern-scout: repetition signals
> for Skill candidates and risk signals for Subagent candidates."*

Read both reports before doing anything else. Notice what stayed out of your main conversation's
context: two independent investigations' worth of file reads and `git log` output, none of it
sitting in your context window — only the two summaries did.

---

## Part 4: Synthesize — this is the part that isn't delegated

Cross-reference the two reports yourself. The strongest candidates are usually where they
overlap: a hotspot `codebase-mapper` flagged that `pattern-scout` *also* flagged for repetition
or risk is a far stronger case than either signal alone. For each candidate you keep, apply the
same test from Lab 4/5 explicitly:

- **Skill candidate?** Is this a bounded, repeated workflow — not a one-off fix?
- **Subagent candidate?** Does isolation, an enforced tool restriction, or a different model
  actually earn its overhead here — not just "this code is complex"?

Drop anything that doesn't survive that test, even if a subagent flagged it.

---

## Part 5: Fill out the recommendation

Copy `templates/recommendation-one-pager.md` and complete it:

```bash
cp templates/recommendation-one-pager.md my-recommendation.md
```

Five sections: the codebase in one sentence, top hotspots, Skill candidates, Subagent
candidates, and one thing you'd add to that codebase's `AGENTS.md` today. Keep every row backed
by a citation from Part 3 — a row with no file/function reference doesn't survive Part 6.

---

## Part 6: Present (~3 minutes) — this is the verification

There's no test file for this lab — the deliverable is a recommendation about real code, and the
honest check on that is other people who might know the codebase, not a script. Present your
one-pager to the room. Expect challenges, especially if you analyzed a codebase others in the
room also touch: "that's not actually repeated, that was a one-off" is exactly the kind of
verify-don't-trust check this lab is supposed to produce.

### Definition of done

1. Both subagents ran, and `pattern-scout`'s hook visibly blocked at least one thing during the
   session (even a command you tried deliberately, to confirm it's enforced).
2. Every candidate in your one-pager is backed by a citation, not a vibe.
3. Every Skill/Subagent candidate is justified against the Lab 4/5 criteria, not just flagged.
4. The one-pager was presented and survived at least one challenge from the room.

---

## Why this matters

- **Two subagents in parallel, synthesized by a human, is the actual capstone skill** — not
  running subagents, which you already knew how to do after Lab 4/5, but cross-referencing their
  independent findings into a judgment call neither of them made for you.
- **This is Skill/Subagent authoring in service of understanding a system, not agent-building as
  an end in itself.** The deliverable is a recommendation and an `AGENTS.md` starting point —
  artifacts a team keeps — not a fleet of agents.
- **Read-only enforcement scales to real risk.** `pattern-scout`'s hook matters more here than in
  any earlier lab, because this is the first lab where the target might be a codebase you don't
  fully control the blast radius of yet.
- **A presentation is a legitimate verifiable target.** Not every deliverable in this course can
  be a passing test — when the work is judgment about real, varied code, a defensible
  presentation that survives peer challenge is the honest substitute.
