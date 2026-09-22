"""Structured logging: shared infrastructure for this lab (WM-109).

This module gives every domain module in this package one small, consistent way to emit an
**audit trail**: instead of ad hoc `print()`/string-interpolated log lines, call sites log an
`event` name plus structured keyword fields, and get back a JSON line, parseable by log
tooling, greppable, and (for this course) capturable deterministically in tests with
`capture_log_events`.

This lab threads it through `fees.py`, `reconcile.py`, and `drift.py`, three modules carried
forward from earlier labs in the full course, which is why this lives here rather than inside
a single lab's exercise folder: it's infrastructure the whole package shares, not one module's
exercise code.
"""

from __future__ import annotations

import json
import logging
import sys
from contextlib import contextmanager
from typing import Any, Iterator

_NAMESPACE = "agentic_framing"


class JsonFormatter(logging.Formatter):
    """Render each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
        }
        fields = getattr(record, "fields", None)
        if fields:
            payload.update(fields)
        else:
            payload["message"] = record.getMessage()
        return json.dumps(payload, sort_keys=True, default=str)


class StructuredLogger:
    """Thin wrapper over stdlib `logging` that emits structured fields, not free-form strings.

    Every call site names an `event` plus whatever domain fields matter (e.g.
    `aum=`, `symbol=`, `portfolio_id=`) instead of interpolating them into a message string.
    That's what keeps the output machine-parseable and the audit trail queryable.
    """

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def log_event(self, level: int, event: str, **fields: Any) -> None:
        self._logger.log(level, event, extra={"fields": {"event": event, **fields}})

    def info(self, event: str, **fields: Any) -> None:
        self.log_event(logging.INFO, event, **fields)

    def warning(self, event: str, **fields: Any) -> None:
        self.log_event(logging.WARNING, event, **fields)

    def error(self, event: str, **fields: Any) -> None:
        self.log_event(logging.ERROR, event, **fields)


_configured = False


def _ensure_configured() -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger(_NAMESPACE)
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    root.propagate = False
    _configured = True


def get_logger(name: str) -> StructuredLogger:
    """Return a `StructuredLogger` scoped under the shared `agentic_framing` namespace.

    `name` should be the domain the call site belongs to, e.g. `get_logger("fees")`,
    `get_logger("reconcile")`, `get_logger("drift")`, this becomes part of the logger's
    dotted name (`agentic_framing.fees`, ...), so output can be filtered per domain.
    """
    _ensure_configured()
    return StructuredLogger(f"{_NAMESPACE}.{name}")


@contextmanager
def capture_log_events(domain: str) -> Iterator[list[dict[str, Any]]]:
    """Test helper: capture the structured `fields` dicts logged under `domain` in this block.

    Yields a list that fills in place as events are logged, so a test can call the code under
    test inside the `with` block and assert on the list afterward, deterministic, no need to
    parse stdout.

    Example:
        with capture_log_events("fees") as events:
            annual_advisory_fee(1_000_000)
        assert events[0]["event"] == "fee_calculated"
    """
    captured: list[dict[str, Any]] = []

    class _CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            fields = getattr(record, "fields", None)
            if fields is not None:
                captured.append(dict(fields))

    logger = logging.getLogger(f"{_NAMESPACE}.{domain}")
    handler = _CaptureHandler()
    logger.addHandler(handler)
    previous_propagate = logger.propagate
    previous_level = logger.level
    logger.propagate = False
    logger.setLevel(logging.INFO)
    try:
        yield captured
    finally:
        logger.removeHandler(handler)
        logger.propagate = previous_propagate
        logger.setLevel(previous_level)
