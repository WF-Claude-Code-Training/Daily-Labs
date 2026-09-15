# Claude Code session guide — Lab 8 (standalone)

You (Claude Code) are pairing with a Wells Fargo Wealth Management engineer working through
a single, self-contained lab extracted from a larger Claude Code training course (Day 2,
Lab 8 of an 8-lab progression). This folder runs entirely on its own — no access to the rest
of the course repo, and no GitLab access, is required or expected.

## The task

Not a bug fix — a **recommendation**. Use two provided subagents to analyze a codebase (the
engineer's own team's, or the course repo as a fallback) and produce a short, citation-backed
recommendation of which Skills and Subagents would be real value-adds there, plus one concrete
addition to that codebase's `AGENTS.md`. See [README.md](README.md) for the full flow.

## The shared standard: the five-ingredient task frame

Every non-trivial ask should read as an agentic task frame, not a bare prompt:

1. **Outcome** — the end state, not the keystrokes.
2. **Scope** — the concrete target and boundaries (which codebase; what not to touch).
3. **Verification** — how "done" is checked (here: a presented, citation-backed one-pager that
   survives peer challenge — not a test file).
4. **Deliverable** — `my-recommendation.md`, from `templates/recommendation-one-pager.md`.
5. **Guardrails** — what NOT to do, and when to stop and ask.

## How to work in this folder

- **This package ships a toolkit, not a target.** `.claude/agents/codebase-mapper.md` and
  `.claude/agents/pattern-scout.md` are meant to be copied into (or added via `--add-dir` to)
  whatever codebase is being analyzed — this folder itself has no app code of its own.
- **Files:**
  - `.claude/agents/codebase-mapper.md` — read-only architecture/hotspot mapper.
  - `.claude/agents/pattern-scout.md` — read-only repetition/risk finder; its `Bash` tool is
    restricted by `scripts/validate-readonly-git.sh` (a `PreToolUse` hook) to read-only `git`
    history commands only — everything else is blocked, not just discouraged.
  - `templates/recommendation-one-pager.md` — the deliverable template.
- **Data governance:** only point these subagents at a codebase already inside Wells Fargo's
  approved Claude Code access path (same rule as Day 1's briefing). If that's not available,
  use the fallback: `claude-labs-ttt` itself, or `lab4-standalone`/`lab5-standalone`.
- **Guardrails:**
  - Run `codebase-mapper` and `pattern-scout` in **parallel** — they're independent, and running
    them sequentially wastes the whole point of delegating.
  - Do the cross-referencing/synthesis yourself, in the main conversation — don't delegate that
    judgment to a third subagent. That step is the actual thing this lab teaches.
  - Every row in the recommendation needs a citation (file/function) from a subagent's report.
    A candidate with no citation gets dropped, not included on the strength of a vibe.
  - `scripts/validate-readonly-git.sh` must stay executable (`chmod +x`) and its path in
    `pattern-scout.md`'s `hooks:` block is relative to the target codebase's root — if the
    subagents are copied elsewhere, copy `scripts/` alongside them, in the same relative
    position, or update the `command:` path.
  - If `.claude/agents/` didn't exist in the target codebase before the session started, restart
    Claude Code once after copying the subagents in — it won't detect a brand-new directory
    mid-session.
