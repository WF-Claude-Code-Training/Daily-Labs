# Day 3 capstone presentation guide for participants

Your pod built its own greenfield use case under the same governed workflow practiced all
week: plan mode, checkpoints, diff review, tests as a gate. **For compliance reasons, your
presentation reports on your workflow, not your code or your use case's business content.**
Report the KPI metrics you observed: how many Skills and subagents you used and the general
benefit each gave you, what hooks/guardrails you configured, and your measured token cost per
line of code. Back every number with evidence you can pull up live. This guide tells you what
to prepare and how it's scored.

**Scored against:** [`capstone-presentation-rubric.md`](capstone-presentation-rubric.md) in
this same folder. Read it before you prepare, not after. It is the whole rubric; nothing about
scoring is held back from you.

**If your presentation claims something your own git log, audit log, or code doesn't back up,
that is the failure mode this rubric exists to catch. Bring the evidence; don't just describe
it.**

---

## 1. Format

- **Confirm your exact slot length with your facilitator.** If this runs as a full capstone
  slot, budget ~10 minutes presenting plus a few minutes of Q&A. If it runs as a shared
  **lightning round** across several pods in one shorter block, use the compressed version in
  §2 instead of trying to force the full structure into 2–3 minutes.
- **One laptop, screen-shared, artifacts already open** in tabs before you start: your terminal
  (for `git log --stat` and, if configured, your audit log tail) and your completed
  token-usage-per-LOC table (§3 below). Keep Skill files, plan docs, and code diffs off screen.
  The presentation reports counts and measured metrics, not the underlying artifacts.
- **Every pod member should be ready to field a question.** Q&A (CP-10) is scored on whoever
  answers, not just whoever is speaking when the question lands.

## 2. Required structure (maps to the four rubric axes)

| # | Section | Maps to | Full slot | Lightning round |
|---|---|---|---|---|
| 1 | Skills: how many you packaged or reused, and the general reuse benefit | CP-1, CP-2 | 2 min | 30 sec |
| 2 | Orchestration: how many subagents you used and how each was verified | CP-3, CP-4, CP-5, CP-6 | 4 min | 1 min |
| 3 | Context & token efficiency: your measured cost and what drove it | CP-7, CP-8, CP-9 | 2 min | 30 sec |
| 4 | One safety-control decision (e.g. a hook or guardrail configured), described generically, plus Q&A | CP-10, CP-11, CP-12 | 2 min + Q&A | 1 min |

If you're in a lightning round, don't try to cover everything. Pick your single strongest, most
concrete piece of evidence per section (one subagent's verification result, one number from your
token table, one instance where you rejected and reworked a subagent's output) rather than a
shallow pass over all of it. A facilitator scoring a compressed slot will weight what you *do*
show more heavily than what you skip.

### What "verified before trusted" looks like (for section 2)

For each subagent you used, be ready to name one concrete thing, not a feeling:

- A test result: its test was red until you approved the change, then green.
- A scope check: its change only touched the files it was scoped to, nothing else.
- An independent review: a second agent (or the pod) independently checked its output against
  its assigned scope before merging.

"I read the output and it looked right" is not a verifiable target. If that's genuinely all you
have for a given subagent, say so. CP-5 specifically rewards pods that show an honest rework
moment over pods that claim a flawless run with no evidence to back it. If you built solo with
no subagents at all, say that plainly; you're scored 0 on the subagent-specific criteria, not
penalized further for not fabricating an orchestration story.

## 3. The token-usage-per-LOC worksheet

CP-7/8/9 need a real, measured number, not an estimate presented as a measurement. Do this
**before** presentation day, while your session history is still available.

### Step 1: Get token counts

Claude Code's session cost summary reports total input/output tokens for a session. **Confirm
the exact command in your installed version before relying on it in front of the room.** As of
this writing it is the `/cost` slash command inside an interactive session. If your version
differs, ask your facilitator rather than guessing on stage.

Run it (or the equivalent for your version) once per subagent session, or once for the whole
session if your subagents ran as sub-tasks within one session rather than separate sessions.
Record whichever granularity your setup gives you. A breakdown by feature or subagent is worth
more (CP-7's top band), but an honest aggregate number beats a fabricated breakdown.

**If no per-session token count is available in your setup:** fall back to an estimate and
*label it as one*. A standard rough approximation: character count of the prompts and responses
involved, divided by 4. A labeled estimate still earns partial credit under CP-7; an unlabeled
guess presented as measured does not.

### Step 2: Get lines of code

From your repo, after your first checkpoint:

```bash
git diff --stat <first-checkpoint-sha>..HEAD -- '<your source file pattern>'
```

Count **net added lines** (insertions minus deletions) in production code. Decide up front
whether test files count toward this denominator, and say which you chose when you present it.
Either choice is defensible; an unstated choice isn't.

### Step 3: Build the table

Adapt the rows to however you actually split the work, by feature, by subagent, or both:

| Feature / subagent task | Tokens (in+out) | Net LOC added | Tokens / LOC |
|---|---|---|---|
| | | | |
| | | | |
| **Total** | | | |

### Step 4: Interpret it, don't just report it (CP-9)

Before you present, agree as a pod on at least one comparison you can defend, e.g.:

- "The [harder feature] cost more per line than [the simpler one]. That's expected: it needed
  more context about an edge case and produced a test alongside the code, not just a lookup."
- "[Feature X] produced almost no code, only a decision doc. Its 'cost' is entirely
  documentation. That's the point: it was a risk we chose to flag rather than build around."

A single aggregate "we used X tokens total" with no per-feature story is the bottom of CP-9's
band, even if the number itself is accurate.

## 4. Dos and don'ts

**Do:**
- Have your terminal open and ready to run `git log`, or tail your audit log if you configured
  one. A question answered by pulling up the real file beats a remembered answer every time.
- Say "we don't have that" if you don't have it. CP-10 rewards consistency with your own
  artifact over confident improvisation.
- Translate your workflow's shape (how many Skills/subagents, what guardrails) and one key
  process decision into plain business language unprompted (CP-12), without detailing what the
  build itself does.

**Don't:**
- Don't spend your limited time walking through what your app does, or any feature/business
  specifics. Spend it on how you know each piece was verified before you trusted it.
- Don't present a build with zero rejected subagent outputs as a point of pride. CP-5 asks for
  the rework moment, not a flawless-run narrative.
- Don't round or estimate your token/LOC numbers without saying so out loud. An unlabeled guess
  is scored as if it were a fabricated number.
- Don't let the presentation contradict your own git log or audit log. If you're unsure what
  they show, check before you present. That's what the gate in
  [`capstone-presentation-rubric.md`](capstone-presentation-rubric.md) exists to catch.
