# WM-115: Ops can't add a split ratio without an engineer

ORCL announced a 3-for-2 forward split. Reconciliation escalated the position every night for
a week because the ratio wasn't in our table, and the only way to add it was a code change and
a release.

Ops should be able to load a newly announced ratio themselves.

---

*Reframe this before you write code. As written it names a symptom, not an outcome, and says
nothing about what must keep working: e.g. what reconciliation should do at 2am if the file
Ops maintains is missing, malformed, or half-written.*
