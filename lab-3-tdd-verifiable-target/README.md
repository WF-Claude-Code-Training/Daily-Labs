# Day 1 · Lab 3 — Plan Mode & Test-Driven Delivery

> **Standalone package.** This folder is a self-contained copy of Lab 3 from a larger Claude
> Code training course. Open this folder
> directly as your VS Code / editor workspace root, then set up:
> ```bash
> pip install -r requirements.txt
> ```
> All commands below assume you're running them from this folder.

> **Environment notes.** If `python3` isn't on PATH (common on Windows), substitute `py -3` or
> `python` in every command below. If `pip install` fails behind the Wells Fargo corporate
> proxy, confirm the current proxy environment variables or internal package index with your TA
> before the session — don't spend lab time debugging network config.

> **Recap.** In Lab 2 (an earlier lab in this course, not included in this package) you drove
> Claude Code's built-in tools to explore and fix quarterly fees, then authored your own
> team-reusable Skill to apply the same pattern fix to montly fees. This lab introduces **Plan
> mode** and **test-driven delivery**: give Claude a verifiable target (failing tests), force
> planning before execution, and implement only after reviewing the plan. Parts 1-5 hand you
> that failing test already written; [Part 6](#part-6-extend--write-the-test-first-for-real-this-time)
> (a stretch goal) takes the training wheels off and has you write the spec yourself.

---

## User story

**WM-110:** Drift alert false positives.

**Given** a portfolio briefly breaches its drift threshold and self-corrects,
**When** the drift-alert system evaluates that breach,
**Then** it must NOT fire an alert unless the breach lasts at least `min_duration_minutes`.
Today it fires on every breach, even momentary spikes, so advisors are drowning in
false-positive alerts.

**The fix:** add **hysteresis** (a minimum duration the portfolio must stay out of bounds
before alerting). A brief spike doesn't fire; a sustained breach does.

### Definition of done

1. A spike lasting less than `min_duration_minutes` does NOT alert.
2. A breach lasting at least `min_duration_minutes` DOES alert.
3. All 4 tests in `test_drift.py` pass, including the one that starts out failing.
4. The full suite (`pytest`) passes with no regressions.

> **Verifiable target (Agentic Mindset — Verification ingredient):** `test_drift.py`
> One test in it fails on purpose before you start. That failing test *is* the spec; Plan
> mode below exists to propose a change against it, not against vibes.

> **Once Parts 1-5 are green:** a follow-up ticket, WM-110b, is waiting in
> [Part 6](#part-6-extend--write-the-test-first-for-real-this-time) (stretch goal, time
> permitting) — no tests provided this time. You write them.

---


## What's already built vs. what you'll do

| Already built | Your turn |
|---|---|
| `drift.py` — basic drift detection (no hysteresis) | Add hysteresis/min-duration behavior |
| `test_drift.py` — 4 tests, **1 failing** (the verifiable target) | Make it pass using Plan mode |
| The drift scorer keywords from earlier | Use them to frame and verify your work |

---

## Part 1: Analyze — understand the verifiable target

Run the tests to see the current state:

```bash
python3 -m pytest test_drift.py -v
```

You should see:
- ✅ `test_no_alert_when_within_threshold` — passes
- ✅ `test_alert_when_breach_exceeds_threshold` — passes
- ❌ `test_no_alert_for_brief_spike` — **fails** (the hysteresis test)
- ✅ `test_alert_after_sustained_breach` — passes (accidentally, for the wrong reason)

Read the failing tests. They specify exactly what "done" means:
- A spike lasting < `min_duration_minutes` should NOT alert
- A breach lasting ≥ `min_duration_minutes` should alert

This is your **verifiable target**. Don't implement until you understand it.

---

## Part 2: Plan — use Plan mode before editing

Open Claude Code and enable **Plan mode** (the toggle in the panel).

Give Claude the task as a proper frame that ensures that false positives in `drift.py` are fixed using hysteresis such that only alert if the breach lasts at least `min_duration_minutes`

**Plan-review checkpoint — read before you approve.** `check_drift_alert` already accepts a
`min_duration_minutes` parameter (it defaults to `0`, which preserves today's alert-immediately
behavior) — the gap is that the function body never uses it. If the plan Claude proposes
includes a step like *"add a `min_duration_minutes` parameter to the function"*, that step is
wrong: the parameter already exists. Don't approve a plan that proposes re-adding it — ask Claude
to revise once it has actually read the current signature.

A correct plan should instead:
1. Track breach duration using the reading timestamps already available
2. Only fire the alert once that duration reaches `min_duration_minutes`
3. Leave the existing parameter and its default untouched

If the plan looks reasonable, approve it. If not, ask for revisions.

---

## Part 3: Implement — execute the approved plan

Once you approve, Claude executes the plan. Watch it:
1. Edit `drift.py` to add hysteresis logic
2. Preserve the existing behavior for immediate breaches when duration tracking isn't needed

---

## Part 4: Verify — run the tests

```bash
python3 -m pytest test_drift.py -v
```

All 4 tests should pass. If not, the verifiable target tells you exactly what's wrong. Fix it and re-run.

---

## Part 5: Deliver — confirm the full suite

Your deliverables for this lab:
1. ✅ Understood the failing tests (verifiable target)
2. ✅ Used Plan mode to review the approach before editing
3. ✅ Implemented hysteresis in `drift.py`
4. ✅ All tests passing (including the 2 that were failing)

---

## Why Plan mode matters

Plan mode is **human-in-the-loop governance** at the edit level:
- You see what Claude intends to do *before* it does it
- You can reject, modify, or approve the plan
- The plan becomes documentation of intent

This is especially important for:
- Changes to critical systems (like alerting)
- Unfamiliar codebases
- Training new team members (they review plans before approving)

---

## The TDD discipline

The failing tests are the **verifiable target** because:
- They're deterministic — same input, same result, every time
- They're specific — they tell you exactly what "done" means
- They're automatable — CI can run them without human judgment

Writing the test first forces you to define acceptance criteria *before* implementation.
This is the same discipline whether you're coding by hand or driving an agent.

Parts 1-5 handed you that discipline pre-packaged — the failing test was already written,
so the spec-writing was done for you. Part 6 takes that scaffolding away.

---

## Part 6: Extend — write the test first, for real this time

> **Stretch goal.** Parts 1–5 are the required lab. Only start Part 6 once those are green and
> time allows — it is not required for completion.

### The follow-up ticket: WM-110b — Severe breaches shouldn't wait

**Given** a portfolio breaches far past its threshold — a severe move, not a marginal one,
**When** the drift-alert system evaluates that breach,
**Then** it must alert immediately, bypassing the `min_duration_minutes` hysteresis you just
built — advisors want to know about a severe move right away, even if it's only been out of
bounds for a minute.

**The fix:** add a `critical_percent` parameter to `check_drift_alert`. When drift exceeds
`critical_percent`, alert immediately regardless of duration. Breaches between
`threshold_percent` and `critical_percent` keep the hysteresis behavior you built in Part 3
unchanged.

No tests exist for this yet, and `drift.py` has no `critical_percent` parameter. That's the
point — you write the spec this time.

### Step 1 — Red: write the tests yourself

Add new test functions to `test_drift.py`. Don't touch the 4 tests already there —
they lock in Part 1-5's hysteresis behavior and must keep passing. At minimum, write:

- A brief spike **above** `critical_percent` → alerts immediately, even though it hasn't
  lasted `min_duration_minutes`.
- A brief spike above `threshold_percent` but **below** `critical_percent` → does NOT alert
  (unchanged hysteresis — this guards against a lazy fix that just deletes the duration
  check entirely).

Run them:

```bash
python3 -m pytest test_drift.py -v
```

Confirm your new tests fail — and fail for the *right* reason (missing behavior, not a typo
in your own test). If a new test passes before you've written any implementation, the test
isn't checking what you think it's checking.

### Step 2 — Plan

Back in Plan mode, frame it for Claude:

> *"Add a `critical_percent` parameter to `check_drift_alert` in `drift.py`:
> breaches above `critical_percent` alert immediately, bypassing `min_duration_minutes`.
> Breaches between `threshold_percent` and `critical_percent` keep the existing hysteresis
> behavior. My new tests in `test_drift.py` are the acceptance criteria — don't edit them.
> Propose a plan first."*

### Step 3 — Implement

Approve the plan, let Claude execute it.

### Step 4 — Verify

```bash
python3 -m pytest test_drift.py -v
```

Your new tests pass, and the original 4 still pass.

### Step 5 — Deliver

```bash
python3 -m pytest -v
```

Full suite, no regressions.

### Why this part exists

A failing test you didn't write is still someone else's spec. Writing the test first means:

- **You** decide what "done" means before any code exists to bias that decision.
- A vague requirement ("alert immediately for severe breaches") only becomes verifiable once
  *you've* turned it into concrete inputs and an expected output.
- If your test would pass against a trivial or wrong implementation (e.g., one that always
  alerts), that's a signal your test is incomplete — a test suite is a spec, and specs get
  reviewed the same way code does.
