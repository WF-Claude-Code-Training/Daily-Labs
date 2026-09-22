# WM-121: Someone changed the fee tiers during an unrelated rollout

Postmortem from last quarter: during the WM-109 logging rollout, an edit to `fees.py` also
altered the tier breakpoints. Nobody caught it in review. The diff was three files wide and
the reviewer was looking at log calls. It priced 400 households wrong for nine days.

The guardrail already existed. It was written in the ticket, in `AGENTS.md`, and in the Skill.
It was followed every time except once.

Make it not depend on being followed.

---

*Reframe this before you write code. Note what the postmortem is actually telling you: the
guardrail was communicated correctly and still failed. Which changes what kind of fix this is.*
