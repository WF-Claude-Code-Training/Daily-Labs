# WM-109 — No structured audit trail across fee, reconciliation, and drift logic

Advisor logins aren't the only thing missing from the audit trail: fee calculations,
reconciliation exceptions, and drift alerts all happen with no structured log record — just
whatever ad hoc `print()`s exist, if any. When compliance asks "why did this fee/escalation/
alert happen," there's nothing to query.

Add a shared structured-logging abstraction and thread it through `fees.py`, `reconcile.py`,
and `drift.py` so every fee calculation, every reconciliation exception (resolved or
escalated), and every fired drift alert is logged as a structured (JSON) event — not printed,
not silently dropped.
