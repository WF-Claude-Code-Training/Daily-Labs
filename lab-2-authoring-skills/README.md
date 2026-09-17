# Day 1 · Lab 2 — Fee Logic Rollout with Two-Pass Skills

> **Standalone package.** This folder is a self-contained copy of Lab 2 from a larger Claude
> Code training course — it needs no access to the rest of the course repo. Setup:
> ```bash
> cd lab2-standalone
> python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
> pip install -r requirements.txt
> ```
> All commands below assume you're running them from this folder.

> **Environment notes.** If `python3` isn't on PATH (common on Windows), substitute `py -3` or
> `python` in every command below. If `pip install` fails behind the Wells Fargo corporate
> proxy, confirm the current proxy environment variables or internal package index with your TA
> before the session — don't spend lab time debugging network config.

> **Recap.** In Lab 1, you used a generic bounded Skill to fix one fee bug. This lab proves
> when a generic flow is enough and when a domain-specific Skill is worth creating.

---

## Principle for this lab

Do not agentify work that should just be automated.

Use agentic workflow to standardize repeated code changes. Once a flow is deterministic and
stable, it should become automation.

---

## Scope for Lab 2

This lab is fee-domain only and stays inside this folder.

- Primary code target: `fee_rollout.py`
- Primary verification target: `test_fee_rollout.py`
- Starter generic Skill: `.claude/skills/scoped-bugfix-flow/SKILL.md`

## Scenario

**WM-202:** Fee logic rollout across billing cadences.

You are rolling out consistent fee business logic across two methods:

1. `quarterly_advisory_fee(...)`
2. `monthly_advisory_fee(...)`

Both methods are intentionally implemented with cliff-rate logic and must be corrected to
progressive-tier logic.

Tests are pre-seeded and intentionally failing at the start.

---

## User story

**As a** WM platform lead, **I want** fee calculations standardized across billing cadences,
**so that** quarterly and monthly fees follow the same progressive-tier business rules.

### Definition of done

1. Pass 1: you use `scoped-bugfix-flow` to fix the quarterly target.
2. Pass 2: you author and invoke your own fee-specific Skill and fix the monthly target.
3. `pytest test_fee_rollout.py -v` passes.
4. Full `pytest` passes.
5. You provide a pass-by-pass deliverable with evidence.

---

## Two-pass workflow (45-60 minutes)

### Pass 0 - Baseline (5 min)

Run tests before edits:

```bash
python3 -m pytest test_fee_rollout.py -v
```

You should see failures. That failing state is the verifiable target.

### Pass 1 - Generic flow on first target (15-20 min)

Use the existing generic Skill to fix **quarterly** behavior only.

Run focused tests:

```bash
python3 -m pytest test_fee_rollout.py -k quarterly -v
```

Prompt template:

> "Use skill `scoped-bugfix-flow`. Outcome: fix progressive-tier behavior for
> `quarterly_advisory_fee` in `fee_rollout.py`. Scope: edit only that file.
> Verification: run `pytest test_fee_rollout.py -k quarterly -v`.
> Guardrails: do not edit tests. Deliverable: scope confirmation + diff summary + evidence."

### Pass 2 - Specialized flow on second analogous target (20-25 min)

Now create your own Skill at `.claude/skills/<your-name>-fee-standardization-flow/SKILL.md` and
use it to fix **monthly** behavior.

Your Skill must add domain rules beyond generic flow:

- progressive marginal tiers only (no cliff-rate pricing)
- exact breakpoint correctness
- monotonic non-decreasing fee for increasing AUM
- preserve public method signatures
- run targeted tests and full suite

Run focused tests:

```bash
python3 -m pytest test_fee_rollout.py -k monthly -v
```

Prompt template:

> "Use skill `<your-fee-standardization-skill>`. Outcome: apply the same progressive-tier
> business rules to `monthly_advisory_fee` in `fee_rollout.py`.
> Verification: run `pytest test_fee_rollout.py -k monthly -v`, then
> `pytest test_fee_rollout.py -v`, then full `pytest`.
> Guardrails: do not edit tests, do not expand scope."

### Final verification (5-10 min)

```bash
python3 -m pytest test_fee_rollout.py -v
```

---

## Deliverable format

Submit these items in order:

1. Skill artifacts:
  - generic Skill used in Pass 1
  - your specialized Skill from Pass 2
2. Scope confirmation:
  - files changed
  - out-of-scope files left untouched
3. Diff summary:
  - what changed for quarterly
  - what changed for monthly
4. Test evidence:
  - baseline failing state
  - Pass 1 focused results (`-k quarterly`)
  - Pass 2 focused results (`-k monthly`)
  - final `test_fee_rollout.py` result
  - final full `pytest` result
5. Comparison:
  - what the specialized fee Skill added beyond `scoped-bugfix-flow`
  - what parts are stable enough to automate next

---

## Optional context exercise (not primary)

If time allows, run the backlog audit command to inspect framing quality:

```bash
python -m agentic_framing audit backlog/
```

Treat it as triage signal only, not a second implementation project.
