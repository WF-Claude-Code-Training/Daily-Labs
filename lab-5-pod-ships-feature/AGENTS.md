# Claude Code session guide: Lab 5 (standalone)

You (Claude Code) are working with a Wells Fargo Wealth Management engineer on **Day 2, Lab 5**
of an 8-lab Claude Code training course. This folder's code and tests need nothing from the rest
of the course repo, but its role pod does: Part 2 has the engineer copy `implementer`,
`test-author`, and `contract-reviewer` in from `../lab-4-subagent-pod-intro/.claude/agents/`, so this
folder is expected to sit as a sibling of `lab-4-subagent-pod-intro/` in the same checkout. If that
sibling folder genuinely isn't present, the engineer re-authors all three from Lab 4's
`ROLES.md` instead. Either way, don't skip straight to Part 4 without them.

**This lab runs a full feature lifecycle through the pod, not one ticket on one file.** WM-114
is a migration: one function's signature changes (`get_price` gains `as_of_date`) and the
ripple crosses six files, two of which never mention pricing in their own bodies. The engineer
maps the blast radius with a subagent they author, then ships the change through
`implementer`: the engineer briefs it, not the other way around. WM-118 is different in kind:
genuinely new code (`statement_delta`), with **no pre-written test file**, the only ticket all
day where `test-author` originates tests from a brief instead of repairing a stale one. Lab 5
used to end at a markdown note describing a migration; it now ends at a shipped migration *and*
a shipped feature built on top of it.

## The two tickets

- **WM-114**: historical pricing for backdated statements. `backlog/WM-114-historical-pricing.md`,
  acceptance contract `test_backdated_statements.py` (19 tests, 11 seeded failing). **Read the
  suite before proposing a design**. It answers two questions the ticket leaves open
  (no-mark-for-that-date, date-before-history-begins) and pins down one requirement the ticket
  never states (a backdated statement must say so on its face).
- **WM-118**: statement comparison. `backlog/WM-118-statement-comparison.md`. **No test file
  exists.** `check_statement_delta.py` is a deterministic floor, not the spec. Don't treat it
  as one, and don't let it substitute for `test-author` actually writing tests from the ticket.

See [README.md](README.md) for the full four-part flow: investigate, migrate, extend, document.

## The shared standard: the five-ingredient task frame

1. **Outcome**: the end state, not the keystrokes.
2. **Scope**: the concrete target and boundaries.
3. **Verification**: how "done" is checked (`pytest`, `check_statement_delta.py`,
   `check_pod.py`, `check_impact_note.py`).
4. **Deliverable**: the reviewable artifact handed back.
5. **Guardrails**: what NOT to do, and when to stop and ask.

## Delegation posture for this lab

- **Map before you touch.** If asked what a change affects, prefer delegating to the engineer's
  `impact-mapper` role over grepping inline. That delegation is the thing being taught. If the
  role doesn't exist yet, say so rather than silently absorbing its job.
- **Part 4's migration and Part 5's build both belong to `implementer`, not to you.** If asked
  to make the six-file change or build `statement_delta` directly, prefer routing to
  `implementer` (once copied in) and say so if it isn't there yet.
- **For WM-118, don't originate the tests yourself, and don't let `implementer` do it either.**
  That job belongs to `test-author`, and it's the only ticket all day where that role's *first*
  contract responsibility (turn criteria into failing tests) actually applies. If asked to write
  `test_statement_delta.py` directly, redirect to `test-author` and say why.
- **`impact-mapper` has no job on WM-118.** Don't invoke it there for the sake of symmetry.
  Nothing in that ticket changes an existing signature, so there's no blast radius to map. If
  asked to "map WM-118 too," say plainly that it doesn't apply and why.
- **Direct callers are the easy half.** Any report that stops at a `grep` for `get_price(` is
  wrong, not incomplete. The transitive callers and the not-reached claim are the deliverable.
- **Migrate in dependency order**, bottom-up: `pricing.py` → `allocation.py` →
  `rebalance.py`/`fees.py`/`drift.py` → `statements.py`. Verify each layer before the next.
- **One editor at a time.** Subagents share this working tree. `rebalance.py`, `fees.py`, and
  `drift.py` are siblings and would be safe to edit concurrently. Name that tradeoff rather
  than assuming it's worth the coordination.
- **Watch for over-migration.** `target_weights` in `allocation.py` must NOT gain `as_of_date`;
  it returns a static profile with no pricing dependency, direct or transitive. Threading the
  parameter through it would pass every behavioral test. Flag it if it appears in a plan.

## How to work in this folder

- **Domain is Wealth Management**: portfolios, positions, allocation drift, advisory fees,
  client statements, end-of-day marks. Keep examples in that world.
- **Files:**
  - `pricing.py`: `get_price`; the function WM-114 changes. The smallest, most innocuous file
    here, which is the point.
  - `allocation.py`: `current_weights` (direct caller), `target_weights` (**not affected**).
  - `rebalance.py`: `compute_trades`; reaches pricing **twice**, directly and via
    `current_weights`. Both paths need the date or the dollar amounts come out wrong while the
    symbols and directions come out right.
  - `fees.py`: `advisory_fee` (direct caller).
  - `drift.py`: `check_drift`; transitive, via `current_weights`.
  - `statements.py`: `build_statement`; transitive via all three, and never mentions pricing.
  - `reference_data/price_history.json`: owned by the pricing team. **Read-only from this
    repo's perspective.** Its newest mark per symbol must agree with `pricing.py`'s `_PRICES`;
    one test asserts exactly that.
  - `test_backdated_statements.py`: WM-114's acceptance contract. 8 of 19 pass before any
    work starts; those are the back-compat guards and must stay green.
  - `statement_delta.py`: WM-118's stub, `NotImplementedError`. **No test file for this one
    exists anywhere in the repo**, that absence is deliberate, not an oversight to fill in
    yourself.
  - `check_statement_delta.py`: a floor-level checker with four fixed scenarios, computed
    against the real (already-migrated) fee/trades/drift functions. Explicitly not the full
    spec. Its own docstring says what it skips (a same-symbol trade whose dollar amount
    changed). Don't let it stand in for `test-author`'s tests.
  - `check_impact_note.py`: deterministic checker for `impact_note.md`.
  - `ROLES.md`: role contracts (scope, tools, hand-offs), including a table of which role does
    what on which ticket. `check_pod.py`: their validator; required pod is five roles now.
- **Verify with scripts, not by eye:**
  ```bash
  python3 -m pytest -v                            # the migration (WM-114)
  python3 check_statement_delta.py                 # the floor for the new feature (WM-118)
  python3 check_pod.py                            # the role definitions (searches both scopes)
  python3 check_impact_note.py impact_note.md      # the note
  ```

## Guardrails

- `as_of_date` must default to `None` on every signature, never to a computed "today". The
  default path has to be bit-identical to today's behavior for every existing caller.
- Keyword name is `as_of_date` everywhere. Not `date`, not `asof`, not `as_of`. One test
  enforces this across all six entry points, because the alternative is a silent bug when
  someone passes the wrong keyword and gets today's price with no error.
- Don't interpolate or estimate a price. No mark at or before the requested date is a `KeyError`,
  not an opportunity to guess. A statement is a client-facing document.
- Use the most recent mark at or before the requested date. Never reach forward to a later mark;
  that puts a price on a statement that didn't exist on the day it claims to describe.
- Don't edit `reference_data/price_history.json` to make a test pass.
- `impact-mapper` is read-only by design. `contract-reviewer`'s restriction is enforced the
  same way. If either flags something, fix the code. Don't widen their tool lists.
- `implementer`'s "never edit a test, never guess a value" boundary is contract-only (a `tools:`
  list can't express "Edit, but not test files"), carried unchanged from Lab 4. Don't ask it to
  cross that line to get unstuck, and don't paper over the fact that nothing but the contract
  stops it.
- For WM-118: `test-author` writes the tests before `implementer` writes any code. If the
  engineer skips straight to implementation because there's no seeded test file to read, name
  the skip rather than quietly following along.

## Why this lab has a personal-scoped subagent

`contract-reviewer` encodes what "done" means for a specific repo's tickets. It belongs checked
into that repo, reviewed by that team. Tracing a function's callers has nothing to do with this
toy portfolio package; it's a habit worth having in every codebase. That distinction is the
entire scope decision: project subagents travel with a repo and its team, personal subagents
travel with the engineer.

Both get the same isolated context and the same enforced tool list at runtime. The only
difference is distribution, and that a personal subagent's `description` is loaded into every
session on that machine from then on, which is a cost worth spending deliberately rather than by
accident.
