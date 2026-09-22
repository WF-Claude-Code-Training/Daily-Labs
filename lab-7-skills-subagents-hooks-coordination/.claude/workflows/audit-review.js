export const meta = {
  name: 'audit-review',
  description: 'Review the WM-109 logging diff across four independent dimensions, then adversarially verify every finding',
  whenToUse: 'After the WM-109 logging rollout is implemented, when you want broader review coverage than one reviewer subagent can give in a single pass.',
  phases: [
    { title: 'Review', detail: 'one reviewer per dimension, all in parallel' },
    { title: 'Verify', detail: 'two skeptics per finding, each trying to refute it' },
  ],
}

// ── The four dimensions ──────────────────────────────────────────────────────
//
// These are deliberately NOT four copies of `logging-reviewer`. Each one is blind to what the
// others are looking at, which is the entire reason to fan out instead of asking one reviewer
// to check four things in sequence and run out of attention on the fourth.

const TARGETS = 'fees.py, reconcile.py, and drift.py'

const DIMENSIONS = [
  {
    key: 'coverage',
    prompt: `Read ${TARGETS} in this repo. WM-109 requires a structured log event at every
audit-worthy decision point: a fee calculation completing, a reconciliation mismatch being
resolved or escalated, a drift alert firing.

Find every audit-worthy path that emits NO event. Report only paths you can point at a specific
line for. Do not report style, naming, or anything about paths that already log.`,
  },
  {
    key: 'noise',
    prompt: `Read ${TARGETS} in this repo. WM-109 explicitly requires that routine, no-op
outcomes stay silent: an exact MATCHED reconciliation result, a drift check that stays within
threshold, and any early return that decided nothing.

Find every log call on a routine path — an event that would add volume to a seven-year archive
without recording a decision. Report only actual log calls you can cite by line.`,
  },
  {
    key: 'scope',
    prompt: `Read ${TARGETS} in this repo. WM-109 is a logging rollout and nothing else. The
only legitimate changes are: one import, one module-level get_logger(...) call, and
logger.info/warning/error(...) calls at existing decision points.

Find anything else that changed — an altered return value, a changed condition, a "while I was
in here" refactor, a modified signature, a touched fee tier, a reordered strategy tuple. Cite
the line. If the logic is untouched, report no findings rather than inventing a nit.`,
  },
  {
    key: 'reconstructability',
    prompt: `Read ${TARGETS} in this repo, then read the emitted events as a compliance analyst
would in twelve months, with no access to this codebase and no one left who worked on it.

For each of the three domains, name one question an auditor would ask that this trail cannot
answer — "why was this escalated rather than resolved?", "which tier produced this fee?". Report
each as a finding naming the missing field and the question it would answer. This dimension is
about sufficiency, not correctness — a trail can be perfectly conformant and still useless.`,
  },
]

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          file: { type: 'string' },
          line: { type: 'integer' },
          title: { type: 'string' },
          detail: { type: 'string' },
        },
        required: ['file', 'title', 'detail'],
      },
    },
  },
  required: ['findings'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    reasoning: { type: 'string' },
  },
  required: ['refuted', 'reasoning'],
}

// ── Review each dimension, verify its findings as soon as they land ──────────
//
// pipeline(), not parallel(): the `coverage` reviewer's findings start getting verified while
// the `reconstructability` reviewer is still reading. No barrier, so no reviewer sits idle
// waiting for the slowest one to finish.

log(`Reviewing ${TARGETS} across ${DIMENSIONS.length} dimensions`)

const results = await pipeline(
  DIMENSIONS,
  (dimension) =>
    agent(dimension.prompt, {
      label: `review:${dimension.key}`,
      phase: 'Review',
      schema: FINDINGS_SCHEMA,
    }),

  (review, dimension) =>
    parallel(
      (review?.findings ?? []).map((finding) => () =>
        // Two independent skeptics per finding, each told to default to refuted when unsure.
        // A reviewer reading fast produces plausible-sounding findings; this is what stops
        // them reaching the engineer as if they were confirmed.
        parallel([0, 1].map((i) => () =>
          agent(
            `A reviewer examining ${TARGETS} claims:

  ${finding.file}${finding.line ? `:${finding.line}` : ''} — ${finding.title}
  ${finding.detail}

Read the actual file and try to REFUTE this. It is refuted if the claim misreads the code, cites
a line that does not say what it claims, describes intended behavior as a defect, or is a matter
of taste rather than a violation of WM-109's requirements. Default to refuted=true if you are
uncertain — a false finding costs an engineer more than a missed one costs here.

(Independent check ${i + 1} of 2.)`,
            { label: `verify:${dimension.key}:${finding.file}`, phase: 'Verify', schema: VERDICT_SCHEMA },
          ),
        ))
          .then((votes) => {
            const heard = votes.filter(Boolean)
            const refuted = heard.filter((v) => v.refuted).length
            // Any refutation kills it. With two voters, requiring unanimity to survive is the
            // right bias: this is a training lab, and a confident wrong finding teaches the
            // wrong lesson about what review is worth.
            return { ...finding, dimension: dimension.key, survived: heard.length > 0 && refuted === 0,
                     votes: heard }
          }),
      ),
    ),
)

const all = results.flat().filter(Boolean)
const confirmed = all.filter((f) => f.survived)

log(`${all.length} raised, ${confirmed.length} survived verification`)

// No silent caps: report what was dropped, not just what survived.
return {
  confirmed: confirmed.map((f) => ({ dimension: f.dimension, file: f.file, line: f.line ?? null,
                                     title: f.title, detail: f.detail })),
  refuted_count: all.length - confirmed.length,
  refuted: all.filter((f) => !f.survived).map((f) => ({ dimension: f.dimension, title: f.title,
                                                        why: f.votes.find((v) => v.refuted)?.reasoning ?? 'no vote recorded' })),
  by_dimension: DIMENSIONS.map((d) => ({
    dimension: d.key,
    raised: all.filter((f) => f.dimension === d.key).length,
    confirmed: confirmed.filter((f) => f.dimension === d.key).length,
  })),
}
