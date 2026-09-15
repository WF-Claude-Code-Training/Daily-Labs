# Day 2 · Lab 5 — Map Before You Touch: Build Your Own Exploration Subagent

> **Standalone package.** This folder is a self-contained copy of Lab 5 from a larger Claude
> Code training course — it needs no access to the rest of the course repo and has no external
> dependencies to install (stdlib-only, Python 3.10+). All commands below assume you're running
> them from this folder.

> **Recap.** In Lab 4 (an earlier lab in this course, not included in this package) you used a
> subagent someone else had already built for you: `strategy-reviewer`, a **project-scoped**
> subagent shipped in that repo's `.claude/agents/`, read-only, one specific job. This lab flips
> both of those: you **author** the subagent yourself, and you scope it to **you** — a personal
> subagent at `~/.claude/agents/`, available in every project on your machine, not just this
> one. Its job also changes: not reviewing a diff, but **mapping a change's blast radius before
> anyone touches code.**

---

## The ticket: WM-114 — Historical pricing for backdated statements

> *"Advisors sometimes need to reissue a client statement as of a prior date. Today
> `get_price` only returns today's price — it needs to accept an `as_of_date` instead."*

A signature change to one small function in `pricing.py`. Before anyone touches it, the real
question is: **what else in this codebase breaks?** A `grep` for `get_price(` finds the direct
callers. It won't tell you which *other* functions depend on it indirectly, several files away,
with no mention of pricing anywhere in their own bodies — and those are exactly the ones a
change like this quietly breaks.

### Definition of done

1. A personal subagent exists at `~/.claude/agents/` whose job is tracing a target function's
   callers — direct and transitive — across this codebase.
2. Claude delegated to it at least once **without being told its name** (proactive delegation),
   and at least once **by explicit invocation** — both observed, not assumed.
3. `impact_note.md` names every direct and transitive caller of `get_price`, and states which
   function in this package is genuinely *not* affected, and why.
4. `python3 check_impact_note.py impact_note.md` passes.

> **Verifiable target (Agentic Mindset — Verification ingredient):** `check_impact_note.py` —
> a deterministic, offline check that your note actually names every required call site, not a
> read-it-yourself judgment call.

---

## What's already built vs. what you'll do

| Already built | Your turn |
|---|---|
| `pricing.py`, `allocation.py`, `rebalance.py`, `fees.py`, `drift.py`, `statements.py` — a small, real call graph | Trace what `get_price` actually reaches |
| `check_impact_note.py` — the verifiable target for your note | Nothing to change here |
| *(nothing — Lab 4 gave you a subagent; this lab doesn't)* | Author your own personal subagent to do the tracing |

---

## Part 1: Orient — a five-minute tour, not a deep dive yet

Six files, in call-graph order: `pricing.py` → `allocation.py` → `rebalance.py` / `fees.py` /
`drift.py` → `statements.py`. Skim them — this is the "map before you touch" habit itself: a
quick pass for shape and direction before you commit to tracing anything in detail. Notice that
`statements.py` (`build_statement`) never mentions pricing anywhere in its own body. Keep that
in mind; it matters in Part 4.

---

## Part 2: Build your own subagent — personal scope, this time

Ask Claude Code to write it, the same way you'd ask for any bounded piece of work:

> *"Create a personal subagent at `~/.claude/agents/` named `change-impact-mapper`. Given a
> target function, it should find every direct caller and every transitive caller (a function
> that depends on it through another function, not by calling it directly) across the current
> project, and report them as two separate lists — direct and transitive — naming the file each
> one lives in. Make it read-only: `Read`, `Grep`, `Glob` only. Use Sonnet."*

**Why personal, not project scope.** `strategy-reviewer` in Lab 4 encoded a rule specific to
*that* codebase's reconciliation strategies — it belongs checked into that repo. Tracing a
function's callers isn't specific to this toy portfolio package at all; it's a habit you'll want
in every codebase you touch. That's exactly the distinction between the two scopes: project
subagents travel with a repo and its team, personal subagents travel with *you*.

> **One restart, once.** If `~/.claude/agents/` didn't already exist on your machine before this
> session started, Claude Code won't notice the new file until you restart it — restart once
> after creating your first personal subagent, then continue.

Open the generated file and check its frontmatter (`name`, `description`, `tools`, `model`)
before moving on — the `description` is what Part 3 depends on.

---

## Part 3: Confirm delegation — proactive, then explicit

**Proactive first — don't name the subagent:**

> *"I'm about to change `get_price`'s signature to add an `as_of_date` parameter. What in this
> codebase would that affect?"*

Watch whether Claude delegates to `change-impact-mapper` on its own. This is the automatic
delegation you'd expect from a well-written `description` — Claude matches your task against
every subagent's description and current context, with no explicit invocation needed. If it
doesn't delegate, that's worth noticing too: revisit the `description` you wrote until a
task like this reliably triggers it.

**Now invoke it explicitly** — name it directly, or `@`-mention it — and compare: same
result, guaranteed rather than inferred.

**Optional — see the context isolation, don't just take it on faith.** Check your context
indicator (or `/usage`) before asking the question above, then again immediately after. Then
try tracing the same thing by asking Claude to read and grep through all six files itself,
inline in the main conversation, and compare the context cost of that against delegating to the
subagent.

---

## Part 4: Produce the change-impact note

Using your subagent (directly, or through Claude Code delegating to it), write `impact_note.md`
naming:

- Every **direct** caller of `get_price`, with its file.
- Every **transitive** caller — a function that never calls `get_price` itself but depends on
  one that does.
- The one function in this package `get_price`'s change does **not** reach, and why — this is
  the one a naive `grep` would also get right, which is the point: the interesting part of
  blast-radius mapping is what a keyword search misses, not what it catches.

Then verify:

```bash
python3 check_impact_note.py impact_note.md
```

All 5 required call sites should be found.

---

## Why this matters

- **Personal vs. project scope is a distribution decision, not a context-efficiency one.**
  Once invoked, your subagent gets the same isolated, fresh context window a project subagent
  would — the difference is who else has it and where its cost is paid. A personal subagent's
  description is loaded into *every* session on your machine from now on; a project subagent's
  cost is contained to that one repo.
- **Proactive delegation is real, and it's driven by what you write.** Claude decides whether to
  delegate based on your task plus the subagent's `description` — a vague description gets
  skipped in favor of just doing the work inline; a specific one gets matched.
- **Isolation is the actual context win.** The subagent's Read/Grep/Glob calls across six files
  never touch your main conversation's context — only its summary does.
- **Transitive impact is the whole lesson.** `build_statement` never says "price" anywhere in
  its own body, and it's still fully exposed to this change. A change-impact note that stops at
  direct callers would have told the advisor team the wrong thing was safe.
