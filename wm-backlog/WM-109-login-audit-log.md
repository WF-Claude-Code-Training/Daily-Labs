# WM-109 — No structured audit trail across fee, reconciliation, and drift logic

Fee calculations, reconciliation exceptions, and drift alerts all happen without a
structured log record. When compliance asks "why did this fee/escalation/alert happen,"
there is nothing to query.

Add a shared structured-logging abstraction and thread it through `fees.py`, `reconcile.py`,
and `drift.py` so every fee calculation, every reconciliation exception, and every fired
drift alert is logged as a structured JSON event.
