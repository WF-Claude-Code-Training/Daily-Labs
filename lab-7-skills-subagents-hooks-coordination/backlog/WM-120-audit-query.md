# WM-120: Compliance can't actually query the audit trail

We shipped structured logging (WM-109) and compliance still opens a ticket with us every time
they need something. Last one: *"show me every HIGH-risk escalation from the 2am run."* That
took an engineer twenty minutes of `grep` and a spreadsheet.

Give them a way to ask.

---

*Reframe this before you write code. The ask names one question; a tool that answers only that
question is a `grep` alias. What does the analyst need on the second day, and what should
happen when the log file has a truncated line in it, which it will?*
