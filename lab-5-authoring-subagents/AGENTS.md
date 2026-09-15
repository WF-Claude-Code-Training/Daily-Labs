# Claude Code session guide — Lab 5 (standalone)

You (Claude Code) are pairing with a Wells Fargo Wealth Management engineer working through
a single, self-contained lab extracted from a larger Claude Code training course (Day 2,
Lab 5 of an 8-lab progression). This folder runs entirely on its own — no access to the rest
of the course repo, and no GitLab access, is required or expected.

## The task

WM-114 — a proposed signature change to `get_price` in `pricing.py`. Before it happens, map
every function that change reaches. See [README.md](README.md) for the full flow: build a
personal subagent, confirm it gets delegated to both proactively and explicitly, then use it to
produce a change-impact note.

## The shared standard: the five-ingredient task frame

Every non-trivial ask should read as an agentic task frame, not a bare prompt:

1. **Outcome** — the end state, not the keystrokes.
2. **Scope** — the concrete target and boundaries (which module/files; what not to touch).
3. **Verification** — how "done" is checked (here: `check_impact_note.py`).
4. **Deliverable** — the reviewable artifact handed back (`impact_note.md`).
5. **Guardrails** — what NOT to do, and when to stop and ask.

## How to work in this folder

- **Domain is Wealth Management** — portfolio allocation, rebalancing, advisory fees, drift
  alerts, client statements. Keep examples in that world.
- **Files:**
  - `pricing.py` — `get_price`, the function WM-114 proposes changing.
  - `allocation.py`, `rebalance.py`, `fees.py`, `drift.py`, `statements.py` — the rest of the
    call graph, in increasing distance from `pricing.py`. `statements.py` is the top: it never
    mentions pricing directly, but nothing in it is safe from this change.
  - `check_impact_note.py` — the verifiable target. Deterministic, stdlib-only, no API key.
  - `backlog/WM-114-historical-pricing.md` — the ticket this lab is based on.
- **This lab is read-only.** Don't modify `pricing.py`, `allocation.py`, `rebalance.py`,
  `fees.py`, `drift.py`, or `statements.py` — the deliverable is a note about them, not a change
  to them.
- **Verify with the checker, not by eye:**
  ```bash
  python3 check_impact_note.py impact_note.md
  ```
- **Guardrails:**
  - Don't stop at a `grep` for `get_price(` — that only finds direct callers
    (`current_weights`, `compute_trades`, `advisory_fee`). `check_drift` and `build_statement`
    depend on it transitively, through those direct callers, and are just as real a break.
  - The subagent you build in this lab is **personal-scoped** (`~/.claude/agents/`), not
    project-scoped. If `~/.claude/agents/` didn't exist before this session started, it won't be
    detected until Claude Code restarts — restart once after creating it, the first time.
  - Keep the subagent read-only (`Read`, `Grep`, `Glob`) — it's an exploration tool, not an
    implementer. There's no code to change in this lab.
  - Test that Claude delegates to it **proactively** (without naming it) before relying on
    explicit invocation — a subagent with a vague `description` gets silently skipped in favor
    of Claude just doing the work inline, which defeats the point of building one.
