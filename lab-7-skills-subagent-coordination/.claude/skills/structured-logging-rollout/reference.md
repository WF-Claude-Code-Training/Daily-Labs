# Reference: structured-logging-rollout field conventions

Loaded on demand by `SKILL.md` — not needed for discovery, only once you're actually about to
write a log call.

## The shared logger

```python
from agentic_framing.logging_utils import get_logger

logger = get_logger("fees")  # -> logs under "agentic_framing.fees"
logger.info("fee_calculated", aum=aum, fee=fee)
```

`get_logger(domain)` returns a `StructuredLogger` with `.info` / `.warning` / `.error`, each
taking an `event` name and arbitrary keyword fields. Every call emits one JSON line:

```json
{"timestamp": "...", "level": "INFO", "logger": "agentic_framing.fees", "event": "fee_calculated", "aum": 1000000, "fee": 10000.0}
```

## Naming conventions

- **`domain`** (the `get_logger(...)` argument): the module's short name — `fees`,
  `reconcile`, `drift`. One per module, defined once at module level.
- **`event`**: `snake_case`, past-tense, specific — `fee_calculated`, `position_resolved`,
  `position_escalated`, `drift_alert_fired`. Not `log`, `event`, `info`, or anything else that
  doesn't say what happened.
- **Fields**: the identifiers a human auditing the event would ask for first — an ID
  (`portfolio_id`, `symbol`), the input that drove the decision (`aum`, `drift_percent`), and
  the outcome (`fee`, `strategy`, `risk_level`). Prefer the same field name the function's own
  parameters/return value already use — don't invent a new name for the same concept.

## Events already in use (WM-109)

| Module | `domain` | Event | Fields | When |
|---|---|---|---|---|
| `labs/lab1/fees.py` | `fees` | `fee_calculated` | `aum`, `fee` | Every call to `annual_advisory_fee` |
| `labs/lab4/reconcile.py` | `reconcile` | `position_resolved` | `symbol`, `strategy` | A mismatch a known strategy explained |
| `labs/lab4/reconcile.py` | `reconcile` | `position_escalated` | `symbol`, `risk_level`, `reason` | A mismatch escalated (genuine break or dollar-risk override) |
| `labs/lab3/drift.py` | `drift` | `drift_alert_fired` | `portfolio_id`, `drift_percent` | `check_drift_alert` returns an alert (not `None`) |

## What NOT to log

Routine, no-op outcomes are not audit-worthy and add noise, not signal:
- An exact `MATCHED` position in reconciliation (nothing happened — don't log it).
- A drift check that stays within threshold (`check_drift_alert` returns `None` — don't log it).

If you're unsure whether a path counts as "routine," ask: would a compliance reviewer scanning
the audit trail want to see this, or would it just be noise between the real events?

## Worked example: threading it through `fees.py`

Before:

```python
def annual_advisory_fee(aum: int, tiers: tuple[FeeTier, ...] = DEFAULT_FEE_TIERS) -> float:
    if aum < 0:
        raise ValueError("AUM cannot be negative")
    for tier in tiers:
        if tier.upper_aum is None or aum <= tier.upper_aum:
            return round(aum * (tier.rate_bps / 10_000), 2)
    raise ValueError("AUM exceeds all configured fee tiers")
```

After:

```python
from agentic_framing.logging_utils import get_logger

logger = get_logger("fees")


def annual_advisory_fee(aum: int, tiers: tuple[FeeTier, ...] = DEFAULT_FEE_TIERS) -> float:
    if aum < 0:
        raise ValueError("AUM cannot be negative")
    for tier in tiers:
        if tier.upper_aum is None or aum <= tier.upper_aum:
            fee = round(aum * (tier.rate_bps / 10_000), 2)
            logger.info("fee_calculated", aum=aum, fee=fee)
            return fee
    raise ValueError("AUM exceeds all configured fee tiers")
```

Note what didn't change: the return value, the tier logic, the error path. Only one new import,
one module-level logger, and one log call at the single point where a fee is actually produced.
