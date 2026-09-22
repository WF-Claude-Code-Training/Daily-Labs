# WM-118: Advisors can't see what changed between two statement dates

Now that a statement can be reissued as of any prior date (WM-114), advisors are asking a
different question: not "what did the statement say on this date," but *"what changed between
this date and that one, for the same household?"* Right now they'd have to pull two statements
and compare them by eye.

Give them a comparison.

---

*Reframe this before you write code. "A comparison" is not an outcome. Which fields matter for
an advisor deciding whether to call a client, and what does "changed" mean for a trade, same
symbol, same action, different dollar amount, is that a change or not? There's no test file
for this one. Decide, write down the decision, and have `test-author` turn it into tests before
anyone implements anything.*
