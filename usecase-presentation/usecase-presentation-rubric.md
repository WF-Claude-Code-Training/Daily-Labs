# Day 3 capstone presentation rubric: greenfield pod build, presented live

This scores the **live presentation** of a pod's Day 3 greenfield build (their own use case,
built from scratch under the same governed workflow practiced all week: plan mode,
checkpoints, diff review, tests as a pre-commit gate). It does not assume any specific app,
business rules, or subagent count. Each pod's build is different by design.

**For compliance reasons, this rubric scores workflow evidence only:** how many Skills and
subagents were used and the general benefit each provided, what hooks/guardrails were
configured, and the measured token cost per line of code. It never requires the pod to show or
read out the build's actual code, prompts, or business content.

Publish this file to learners ahead of the build, alongside
[`capstone-presentation-guide.md`](capstone-presentation-guide.md) in this same folder. This is
scored live by a facilitator, not by an automated pipeline. There is no answer key and no judge
model behind it.

`rubric_version: 1.0.0`

---

## Format

| | |
|---|---|
| Presenters | Pod (the same pod that built the submission) |
| Suggested length | ~10 minutes; confirm your actual slot with your facilitator. If this runs as a shared "lightning round" across several pods, scale down to the compressed version in the guide instead of trying to fit the full rubric into 2–3 minutes. |
| Scored by | Facilitator, live |

**Required artifacts on screen:**
- `git log --oneline --stat` (first checkpoint through the final commit): commit counts and
  timing only. Keep commit messages high-level, not feature-specific.
- Audit log or hook output, if hooks/audit logging were configured for this build
- A count of Skills and subagents built or reused for this build, each with a one-line generic
  description of its purpose (not the `SKILL.md`/config content itself)
- The token-usage-per-LOC table (see [`capstone-presentation-guide.md`](capstone-presentation-guide.md))

---

## Axes (weights sum to 100)

| Axis | Weight | Intent |
|---|---|---|
| **Skills design & reuse** | 15 | Did the pod package any part of this build as a Skill: something the next task, or the next engineer, can invoke rather than re-derive from scratch? A build that only ever existed as one-off prompts in this one session hasn't produced anything reusable. |
| **Subagent orchestration & verifiable targets** | 40 | Heaviest axis, by design. Anyone can claim "I used subagents." This axis scores whether the pod can name, for each subagent it used, the concrete target that proved its output was correct *before* it was trusted, such as a passing test, a change that stayed within its declared scope, or an independent check, rather than a retrospective narrative. A pod that built everything solo scores 0 on the subagent-specific criteria (CP-3–CP-5) but can still be graded on CP-6. |
| **Context & token efficiency** | 25 | Agentic delegation has a real cost. This axis scores whether the pod measured it (tokens consumed relative to code shipped) and can explain where the cost went and whether that spend was deliberate or wasteful. |
| **Delivery & defensibility** | 20 | Can the pod defend a specific design choice under a follow-up question, in the time allotted, in language a non-engineer stakeholder could follow? |

---

## Score bands

Applied to the 0–100 total, **after** the gate below.

| Band | Minimum score |
|---|---|
| Exemplary | 90 |
| Proficient | 75 |
| Developing | 60 |
| Not yet | 0 |

---

## Gate: narrative integrity

**Tied to CP-10.** Overridable by facilitator (with a recorded reason).

> If the pod's live account of what it built, or how it was verified, contradicts what's
> actually visible in its own git history or audit log, that is a governance failure in the
> retelling, not just a missed presentation point. Examples: a claimed test that doesn't exist,
> a claimed safety control that was never configured, or a claimed subagent boundary the commit
> history doesn't respect. A confident, well-delivered presentation that misrepresents its own
> artifact is a worse outcome than an awkward one that gets it right. **Cap the presentation
> score at "not yet" regardless of every other axis.**

---

## Criteria

`check: facilitator_live` for every criterion below: scored in the room, against required
evidence shown on screen. A claim with nothing on screen to back it scores at the bottom of its
band.

### Axis 1 · Skills design & reuse (15 pts)

| ID | Criterion (weight) | Asks | Evidence required | Scoring |
|---|---|---|---|---|
| **CP-1** | A Skill was built or reused, and the pod can say why (8) | Did the pod package part of this build's workflow as a Skill, and can they explain what makes it reusable beyond this one build? | The Skill's name and a one-sentence description of when it's invoked, stated aloud, not the underlying `SKILL.md` content | **8**: Skill named and a concrete reuse example beyond this build<br>**5**: Skill named, but reuse case is vague or hypothetical<br>**2**: skill-shaped workflow described but never packaged as a Skill<br>**0**: no Skill, nothing framed as reusable |
| **CP-2** | The Skill is scoped like a workflow, not a saved prompt (7) | Is the trigger narrow enough that this Skill would fire only for the task it targets, not as a generic wrapper for many unrelated requests? | The pod's spoken characterization of the trigger's scope (narrow vs. broad) and confirmation of one thing it correctly does *not* fire on, not the literal description text read aloud | **7**: pod describes a narrow, specific trigger scope and confirms it excludes an unrelated request<br>**4**: trigger described as narrow, but no confirmation it excludes unrelated requests<br>**0**: trigger described as broad/generic, firing on almost any request |

### Axis 2 · Subagent orchestration & verifiable targets (40 pts)

| ID | Criterion (weight) | Asks | Evidence required | Scoring |
|---|---|---|---|---|
| **CP-3** | Decomposition rationale (8) | Can the pod explain, in general terms, why the build was split into these subagents (if any): parallelism, safety isolation, or tool restriction? | A count of subagents used and the general rationale category for each, not the subagent briefs/configs themselves | **8**: a rationale category (parallelism, safety, tool restriction) given for every subagent<br>**4**: boundaries counted but rationale asserted, not tied to a specific reason<br>**0**: can't explain the decomposition, or no subagents used and pod doesn't address why |
| **CP-4** | Verifiable target per subagent (15) | For each subagent used, what concrete, falsifiable check had to pass before its output was trusted? | For at least half the subagents, a named check (test result, scope match, independent review) confirmed live | **15**: a distinct target named for every subagent, ≥2 confirmed live<br>**10**: targets named for most, ≥1 confirmed live<br>**5**: targets named for fewer than half, or all described rather than confirmed<br>**0**: no named verifiable target for any subagent, only "I reviewed the output" |
| **CP-5** | At least one rejection or rework, shown honestly (9) | Did any subagent's first output get rejected or sent back, and can the pod describe that moment without displaying the rejected code? | A description of which check caught the rejection (test failure, scope violation, failed independent review) and what changed on retry | **9**: a real rejection is described specifically (what check caught it, what changed)<br>**5**: a rejection is stated but can't be described specifically<br>**0**: every subagent claimed correct on the first pass, no review moment described |
| **CP-6** | Safety architecture narration matches the artifact (8) | Does the pod's spoken account of plan mode, checkpoints, diff review, and the test gate match what's visible in the git log (and audit log, if configured)? | The checkpoint count/timing, plus confirmation that tests ran before each commit | **8**: every spoken claim is immediately backed by something on screen<br>**4**: mostly matches, one claim not immediately locatable<br>**0**: multiple claims contradict what's on screen, or no required evidence can be located |

> **CP-4 note:** this is the single most heavily weighted criterion in the rubric on purpose. It
> is the direct, spoken-aloud proof that delegation didn't mean "trust and skip verification."

### Axis 3 · Context & token efficiency (25 pts)

| ID | Criterion (weight) | Asks | Evidence required | Scoring |
|---|---|---|---|---|
| **CP-7** | Token-usage measurement methodology (8) | Did the pod measure actual token consumption and lines of code shipped, using a documented method? | The completed token-usage-per-LOC table, plus one sentence on how each number was captured | **8**: table complete, method named, broken down by subagent or task<br>**5**: table complete but only aggregate, or method not named<br>**0**: no measurement, or omitted |
| **CP-8** | Deliberate context-management choices (9) | Can the pod name a specific technique used to control context size (subagent isolation, selective file inclusion, `CLAUDE.md` scoping) and connect it to the number in CP-7's table? | The named technique, described in general terms, plus its measured effect on the token/LOC number, not the literal prompt or brief text | **9**: a specific technique named and tied to a measurable effect on the token/LOC number<br>**5**: a technique named, but not connected to a number<br>**0**: no specific technique named, "we just used Claude Code normally" |
| **CP-9** | Efficiency interpretation & tradeoffs (8) | Does the pod correctly read their own number, e.g. a genuinely harder task costing more tokens per line than a simpler one? | A specific comparison from their own table, across at least two subagents/tasks | **8**: a specific, defensible comparison between at least two parts of the build, explained<br>**4**: variation acknowledged but not explained<br>**0**: the aggregate number treated as the whole story |

### Axis 4 · Delivery & defensibility (20 pts)

| ID | Criterion (weight) | Asks | Evidence required | Scoring |
|---|---|---|---|---|
| **CP-10** | Live Q&A defense (10) | When asked a follow-up, does the pod answer from the artifact in front of them, or improvise? | n/a: scored from the live exchange | **10**: specific, consistent, evidence pulled up unprompted<br>**6**: generally consistent but vague, or requires prompting<br>**0**: an answer contradicts the artifact, or the pod cannot answer |
| **CP-11** | Time and structure discipline (5) | Did the pod cover all required sections within the agreed time? | n/a | **5**: all sections covered, within agreed time (±2 min, or within the lightning-round slot)<br>**3**: all sections covered, but significantly over/under time<br>**0**: one or more required sections skipped entirely |
| **CP-12** | Clarity for a non-technical audience (5) | Could a non-engineer stakeholder follow the pod's workflow (how many Skills/subagents, what guardrails) and why one process decision mattered, without needing to know what the build itself does? | n/a: scored from the live exchange | **5**: workflow shape and one process decision translated into plain language unprompted<br>**2**: plain-language framing only appears after the facilitator asks<br>**0**: entire presentation stays in tool/implementation vocabulary |

> **CP-10 note:** this criterion carries the narrative-integrity gate above. An answer that
> contradicts the artifact isn't just a 0 here; it caps the whole presentation score.
