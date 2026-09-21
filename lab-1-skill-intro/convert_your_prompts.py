"""Exercise helper for Lab 1 (WM-101 fee-tier bug).

See README.md for the full instructions.

Self-contained: this standalone lab bundles a small, deterministic task-frame scorer
inline (no external `agentic_framing` package, no API key, no network). The scorer is a
teaching aid, not a grader — a high score means "this reads like a task frame," not
"this is a good task." Use it to spot what's missing, then use judgement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


# ── Exercise ─────────────────────────────────────────────────────────────────
TICKET_PROMPT = (
    "WM-101: Write a function that recalculates the advisory fee when a household's "
    "AUM crosses a tier breakpoint."
)

LOW_QUALITY_FRAME = (
    "Fix WM-101 so fees are correct, scoped to the fee module, run tests, "
    "share a summary, and do not break compatibility."
)


# Fill this in during the exercise and re-run.
MY_FRAME = ""


def main() -> int:
    print(rule())
    print("  LAB 1 DEMO — WM-101 tiered AUM breakpoint bug")
    print(rule())
    print(f"\n  Ticket prompt:\n    {TICKET_PROMPT}")
    print(render_score(score_frame(TICKET_PROMPT), show_suggestions=False))

    print("\n  Low Quality frame: (all five ingredients, but still weak):")
    print(f"    {LOW_QUALITY_FRAME}")
    print(render_score(score_frame(LOW_QUALITY_FRAME), show_suggestions=False))

    if MY_FRAME.strip():
        print("\n  Your frame:")
        print(f"    {MY_FRAME.strip()}")
        print(render_score(score_frame(MY_FRAME.strip())))
    else:
        print("\n  (No `MY_FRAME` yet — add one above and re-run.)")

    print("\nDone. Iterate your frame until quality and tests both pass.")
    return 0


# ── The five ingredients of an agentic task frame ────────────────────────────
class Ingredient(str, Enum):
    """The five ingredients of an agentic task frame."""

    OUTCOME = "outcome"
    SCOPE = "scope"
    VERIFICATION = "verification"
    DELIVERABLE = "deliverable"
    GUARDRAILS = "guardrails"

    @property
    def label(self) -> str:
        return self.value.capitalize()


# What to add when the scorer finds an ingredient missing.
_SUGGESTIONS: dict[Ingredient, str] = {
    Ingredient.OUTCOME: "State the goal as an outcome ('make X resilient', 'so that Y'), "
                        "not a single artifact ('write a function that…').",
    Ingredient.SCOPE: "Name the concrete target (module, file, service) and the boundary "
                      "('only in…', 'without changing the public interface').",
    Ingredient.VERIFICATION: "Add a check the agent can run: 'run the tests', 'lint', "
                             "'type-check', 'validate against the sample portfolios'.",
    Ingredient.DELIVERABLE: "Ask for a reviewable artifact: a diff summary, a report, a "
                            "list of changed files, a PR description.",
    Ingredient.GUARDRAILS: "Set boundaries: 'don't touch X', 'keep backward compatible', "
                           "'flag failures', 'ask before deleting anything'.",
}


# ── Heuristic signal sets ────────────────────────────────────────────────────
# Each ingredient is detected by one or more regex patterns. Patterns use word
# boundaries so "test" doesn't fire on "latest". Kept readable on purpose — you
# should be able to open this file and understand exactly why your frame scored
# the way it did.
_SIGNALS: dict[Ingredient, list[str]] = {
    Ingredient.OUTCOME: [
        r"\bso\b", r"\bin order to\b", r"\bresulting in\b", r"\bsuch that\b", r"\bensure(s|d)?\b",
        r"\b(resilient|robust|faster|correct|consistent|identical|unchanged)\b",
        r"\brefactor\b", r"\bmigrate\b", r"\bharden\b", r"\bresolve\b", r"\bimprove\b",
        r"\boptimi[sz]e\b", r"\bintegrate\b", r"\bconsolidat", r"\bremediate\b",
        r"\bspeed up\b", r"\bgoal\b", r"\bend state\b", r"\bobjective\b",
    ],
    Ingredient.SCOPE: [
        r"\bmodule\b", r"\bpackage\b", r"\bservice\b", r"\bcomponent\b", r"\bendpoint\b",
        r"\bfile(s)?\b", r"\bdirectory\b", r"\bclass\b", r"`[^`]+`",
        r"\b[\w./-]+\.(py|java|ts|js|sql|cs|go)\b",
        r"\b(only|limited to|scoped to|within)\b", r"\bwithout (changing|touching|breaking)\b",
        r"\bpublic (api|interface)\b", r"\bboundar", r"[\w-]+/[\w-]+",
    ],
    Ingredient.VERIFICATION: [
        r"\btest(s|ing)?\b", r"\bpytest\b", r"\bunit test", r"\btest suite\b",
        r"\brun\b.*\b(test|suite|lint|check)\b", r"\blint(er|ing)?\b", r"\btype[- ]?check\b",
        r"\bvalidate\b", r"\bverif(y|ies|ication)\b", r"\bconfirm\b", r"\bbenchmark\b",
        r"\ball (tests|checks) pass\b", r"\bcoverage\b", r"\bregression\b", r"\bsmoke test\b",
    ],
    Ingredient.DELIVERABLE: [
        r"\bdiff\b", r"\bsummary\b", r"\bsummari[sz]e\b", r"\breport\b", r"\bchangelog\b",
        r"\bpull request\b", r"\bPR\b", r"\blist of\b", r"\btable\b", r"\bproduce\b",
        r"\bwrite[- ]?up\b", r"\bdocument\b", r"\boutput a\b", r"\bhand back\b",
        r"\bchanged files\b", r"\bexplain what changed\b",
    ],
    Ingredient.GUARDRAILS: [
        r"\bdon'?t\b", r"\bdo not\b", r"\bmust not\b", r"\bnever\b", r"\bavoid\b",
        r"\bask (me )?(first|before)\b", r"\bstop if\b", r"\bflag\b", r"\bpreserve\b",
        r"\bkeep .* (backward|backwards) compatible\b", r"\bleave .* unchanged\b",
        r"\bdon'?t (touch|change|delete)\b", r"\bno breaking changes\b", r"\bconstraint",
    ],
}

# A frame that is *only* a prompt usually opens like this and has nothing else.
_PROMPT_OPENERS = re.compile(
    r"^\s*(write|create|generate|give me|make)\s+(a|an|the|some)?\s*"
    r"(function|method|class|script|snippet|regex|query|loop|helper)\b",
    re.IGNORECASE,
)


@dataclass
class FrameScore:
    """The result of scoring one task frame."""

    text: str
    present: set[Ingredient] = field(default_factory=set)
    quality_points: int = 0
    quality_feedback: list[str] = field(default_factory=list)

    @property
    def missing(self) -> list[Ingredient]:
        return [i for i in Ingredient if i not in self.present]

    @property
    def score(self) -> int:
        """Number of ingredients detected, 0–5."""
        return len(self.present)

    @property
    def quality_score(self) -> int:
        """How actionable/specific the frame is, 0–5."""
        return self.quality_points

    @property
    def total_score(self) -> int:
        """Combined score, 0–10: ingredient completeness + frame quality."""
        return self.score + self.quality_score

    @property
    def verdict(self) -> str:
        if self.score <= 1:
            return "Prompt"
        if self.score <= 3:
            return "Partial frame"
        return "Agentic task frame"

    @property
    def suggestions(self) -> list[str]:
        """Actionable next steps for each missing ingredient."""
        suggestions = [f"Add {i.label}: {_SUGGESTIONS[i]}" for i in self.missing]
        suggestions.extend(self.quality_feedback)
        return suggestions


def score_frame(text: str) -> FrameScore:
    """Score a task frame against the five ingredients."""
    result = FrameScore(text=text)
    for ingredient, patterns in _SIGNALS.items():
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            result.present.add(ingredient)

    # A bare "write a function that…" opener with no other signal is the canonical
    # Prompt — make sure it never sneaks an OUTCOME point from a stray verb.
    if _PROMPT_OPENERS.match(text) and result.score <= 1:
        result.present.discard(Ingredient.OUTCOME)

    result.quality_points, result.quality_feedback = _score_quality(text)
    return result


def _score_quality(text: str) -> tuple[int, list[str]]:
    """Score frame quality independently from ingredient presence.

    A frame can include all five ingredients and still be weak if it is vague.
    """
    points = 0
    feedback: list[str] = []

    checks: list[tuple[bool, str]] = [
        (
            _has_specific_scope(text),
            "Strengthen Scope quality: name concrete files/modules (for example `fees.py`).",
        ),
        (
            _has_runnable_verification(text),
            "Strengthen Verification quality: include executable checks (for example `pytest test_fees.py`).",
        ),
        (
            _has_measurable_acceptance(text),
            "Strengthen Outcome quality: include measurable acceptance criteria (numbers, thresholds, or exact cases).",
        ),
        (
            _has_specific_deliverable(text),
            "Strengthen Deliverable quality: ask for concrete output (changed files, test evidence, before/after values).",
        ),
        (
            _has_specific_guardrails(text),
            "Strengthen Guardrails quality: define concrete boundaries (public API, output format, escalation condition).",
        ),
    ]

    for passed, message in checks:
        if passed:
            points += 1
        else:
            feedback.append(message)

    return points, feedback


def _has_specific_scope(text: str) -> bool:
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in [
            r"`[^`]+`",
            r"\b[\w./-]+\.(py|java|ts|js|sql|cs|go)\b",
        ]
    )


def _has_runnable_verification(text: str) -> bool:
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in [
            r"\bpytest\b",
            r"\bpython\s+-m\s+pytest\b",
            r"\btests?/test_[\w-]+\.py\b",
            r"\btest_[\w-]+\.py\b",
            r"\brun\b.*\btest suite\b",
        ]
    )


def _has_measurable_acceptance(text: str) -> bool:
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in [
            r"\b\d+(\.\d+)?%\b",
            r"\b\d+[_,]?\d*\b",
            r"\b(boundary|breakpoint|threshold|exact)\b",
            r"\bbefore/after\b",
        ]
    )


def _has_specific_deliverable(text: str) -> bool:
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in [
            r"\bchanged files\b",
            r"\btest output\b",
            r"\bdiff summary\b",
            r"\bbefore/after\b",
            r"\binclude\b.*\bresults\b",
        ]
    )


def _has_specific_guardrails(text: str) -> bool:
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in [
            r"\bpublic (api|interface)\b",
            r"\bdon'?t change\b.*\b(output|schema|signature|interface)\b",
            r"\bstop and ask\b",
            r"\bescalat(e|ion)\b",
        ]
    )


# ── Display helpers ──────────────────────────────────────────────────────────
_CHECK = "\u2713"   # ✓
_CROSS = "\u2717"   # ✗
_RULE = "\u2500" * 74


def rule() -> str:
    return _RULE


def render_score(score: FrameScore, *, show_suggestions: bool = True) -> str:
    """Render a FrameScore as an ingredient checklist with a verdict and next steps."""
    lines = [
        rule(),
        f"  Verdict: {score.verdict}   ({score.score}/5 ingredients)",
        f"  Quality: {score.quality_score}/5   Overall: {score.total_score}/10",
        rule(),
    ]
    for ingredient in Ingredient:
        mark = _CHECK if ingredient in score.present else _CROSS
        lines.append(f"    {mark}  {ingredient.label}")
    if show_suggestions and score.suggestions:
        lines.append("")
        lines.append("  To strengthen this frame:")
        for suggestion in score.suggestions:
            lines.append(f"    - {suggestion}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

