# Day 1 · Lab 1 — Framing quality, using a Skill, and shipping a real fix

> **Standalone package.** This folder is a self-contained copy of Lab 1 from a larger Claude
> Code training course — it needs no access to the rest of the course repo. Setup:
> ```bash
> cd lab1-standalone
> python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
> pip install -r requirements.txt
> ```
> All commands below assume you're running them from this folder.

> **Environment notes.** If `python3` isn't on PATH (common on Windows), substitute `py -3` or
> `python` in every command below. If `pip install` fails behind the Wells Fargo corporate
> proxy, confirm the current proxy environment variables or internal package index with your TA
> before the session — don't spend lab time debugging network config.

> **Core idea.** A code fix only works if the task frame is specific enough for an agent to act
> safely and verify the result. This lab teaches that discipline with a real WM-101 advisory-fee
> bug in a small, deterministic module.

---

## User story

**WM-101:** Advisory fees are incorrect when household AUM crosses tier breakpoints.

**Given** a household's AUM crosses one or more tiered fee breakpoints (e.g., $1,000,000 and
$5,000,000), **When** `annual_advisory_fee` calculates the annual advisory fee, **Then** the
fee must be computed progressively — each tier's rate applies only to the portion of AUM
within that tier — instead of the current cliff-edge behavior, where crossing a breakpoint
applies a single tier's rate to the entire AUM.

### Definition of done

1. `annual_advisory_fee` returns the progressive/marginal fee at, just above, and above each
   breakpoint (matching the documented example: first $1,000,000 at 1.00%, next $4,000,000 at
   0.80%, remainder at 0.60%).
2. `test_fees.py` passes in full, with no tests edited to fit the bug.
3. The full suite (`pytest`) passes with no regressions elsewhere.
4. Negative AUM still raises `ValueError`.

> **Verifiable target (Agentic Mindset — Verification ingredient):** `test_fees.py`
> — this is what "done" means before you hand anything back. Delegating an outcome only works
> if the agent can check it against something concrete, not vibes.

---

## Lab outcomes

By the end of this exercise, you should be able to:

1. Spot the difference between a complete frame (all five ingredients) and a high-quality one.
2. Improve framing until it is specific enough to execute safely.
3. Leverage an existing, reusable Skill (`scoped-bugfix-flow`) instead of writing an ad hoc prompt.
4. Implement and verify a WM bug fix with a test harness.
5. Return a clear deliverable summary suitable for code review.

---

## Step 1 - Run the prompt-quality demo

```bash
python3 convert_your_prompts.py
```

What you should observe:

1. The raw ticket prompt scores low.
2. A sample frame can have all five ingredients and still score only medium overall.

---

## Step 2 - Write and refine your own frame

Open `convert_your_prompts.py` and edit `MY_FRAME`.

Use this target:

1. Keep all five ingredients.
2. Reach at least `9/10` overall.
3. Keep the intent fixed (do not change the user story).

Re-run the script until you get there:

```bash
python3 convert_your_prompts.py
```

---

## Step 3 - Implement the WM-101 fix using your frame

Use Claude Code with the starter skill `scoped-bugfix-flow` and your improved frame. This
Skill has no built-in knowledge of WM-101. It's a reusable bounded bug-fix pattern that
derives its scope and verification targets from whatever frame you hand it, so your frame
text has to actually name the file(s) and test command for it to work.

Use this exact sequence (substitute your own frame text for `<your frame>`):

1. Analysis pass (no code changes):
   - "Use skill `scoped-bugfix-flow` with this frame: <your frame>. Run Phase A only. Do not edit files yet."
2. Implementation pass:
   - "Use skill `scoped-bugfix-flow`. Execute Phase B within scope."
3. Verification + handoff:
   - "Use skill `scoped-bugfix-flow`. Run Phase C and Phase D and return output contract."

Keep implementation scoped to fee logic and supporting tests.

Suggested execution checks:

```bash
python3 -m pytest test_fees.py
python3 -m pytest
```

---

## Step 4 - Produce the deliverable

Hand back:

1. The final task frame text.
2. Test evidence (`test_fees.py` and full suite result).
3. Short diff summary (what changed and why).
4. Any assumptions or escalations you had to make.

---

## Guardrails

1. Do not edit tests to dodge the requirement; fix behavior in code.
2. Do not broaden scope beyond WM-101.
3. Preserve public behavior except for the breakpoint bug fix.
4. Stop and ask if expected breakpoint behavior is unclear.

---

## Optional stretch

Turn on `USE_CLAUDE = True` in `convert_your_prompts.py` and compare your frame with a model draft.
Keep yours unless the draft is measurably better.

The model output is never ground truth.
