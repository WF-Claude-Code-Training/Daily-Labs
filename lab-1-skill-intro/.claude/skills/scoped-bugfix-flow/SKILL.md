---
name: scoped-bugfix-flow
description: >-
  Run a deterministic, bounded bug-fix flow (analyze -> implement -> verify -> deliver)
  driven by a five-ingredient task frame (Outcome/Scope/Verification/Deliverable/Guardrails).
  USE WHEN the caller supplies a task frame for a scoped bug fix and wants a repeatable,
  reviewable sequence instead of an open-ended edit.
---

# Skill: scoped-bugfix-flow

Use this skill to run a predictable bounded bug-fix workflow for *any* ticket that comes
with a five-ingredient task frame. Keep the work small, verifiable, and reviewable. This
skill has no built-in knowledge of any specific ticket, file, or bug — every run is
parameterized by the frame supplied in the invocation.

## Intent

Fix the behavior described in the frame's Outcome without turning this into an
open-ended refactor.

## Scope

Derive scope entirely from the invoking task frame:
- **Primary code target(s)**: the file(s)/module(s) named in the frame's **Scope**.
- **Primary verification target(s)**: the test(s)/command(s) named in the frame's
  **Verification**.
- **Allowed supporting edits**: only what the frame's Scope explicitly allows.
- **Out of bounds unless explicitly requested**: anything not named in the frame's Scope.

## Phase flow

1. **Phase A: Analyze only (no code changes).**
   - Read the code and test files named in the frame's Scope/Verification.
   - Restate the frame's Outcome in your own words.
   - Provide a minimal implementation plan in 3-5 bullets.
   - Stop and wait for confirmation.

2. **Phase B: Implement bounded fix.**
   - Modify only files in scope.
   - Keep function/API signatures stable unless the frame says otherwise.
   - Keep logic readable and deterministic.

3. **Phase C: Verify.**
   - Run the command(s) named in the frame's Verification.
   - If test tools are unavailable, report the exact blocker.

4. **Phase D: Deliver.**
   - Return the artifact named in the frame's Deliverable, at minimum:
     - Files changed
     - Behavior summary tied to the Outcome
     - Test results
     - Assumptions or escalation points

## Output contract

Always present results in this order:
1. Scope confirmation
2. Changes made
3. Verification evidence
4. Risks or assumptions

## Guardrails

- Do not edit tests to fake correctness.
- Do not widen scope beyond what the frame's Scope names.
- If expected behavior conflicts with tests, stop and ask.
- If the frame is vague or missing an ingredient, stop and ask rather than assuming.
- The agent output is never ground truth; tests and review decide.
