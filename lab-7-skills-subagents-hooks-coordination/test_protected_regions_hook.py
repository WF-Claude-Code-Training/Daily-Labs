"""Tests for the Lab 7 protected-region hook (WM-109's PreToolUse enforcement).

Exercises `.claude/hooks/protected_regions.py` directly by feeding it the same JSON on stdin
Claude Code sends for a PreToolUse event, and asserting on its exit code. Exit code 2 means
"blocked" (Claude Code feeds stderr back to the model as the reason); exit code 0 means
"allowed". These tests never touch the real fees.py/reconcile.py/drift.py on disk. The hook
runs against copies in tmp_path so a failing assertion can't corrupt this lab's files.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
HOOK = REPO_ROOT / ".claude" / "hooks" / "protected_regions.py"


def _run_hook(event: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
    )


def _copy_target(tmp_path: Path, name: str) -> Path:
    dest = tmp_path / name
    shutil.copy(REPO_ROOT / name, dest)
    return dest


def test_blocks_edit_that_changes_fee_tier_values(tmp_path):
    target = _copy_target(tmp_path, "fees.py")
    event = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(target),
            "old_string": (
                "DEFAULT_FEE_TIERS: tuple[FeeTier, ...] = (\n"
                "    FeeTier(upper_aum=1_000_000, rate_bps=100),\n"
                "    FeeTier(upper_aum=5_000_000, rate_bps=80),\n"
                "    FeeTier(upper_aum=None, rate_bps=60),\n"
                ")"
            ),
            "new_string": (
                "DEFAULT_FEE_TIERS: tuple[FeeTier, ...] = (\n"
                "    FeeTier(upper_aum=2_000_000, rate_bps=100),\n"
                "    FeeTier(upper_aum=5_000_000, rate_bps=80),\n"
                "    FeeTier(upper_aum=None, rate_bps=60),\n"
                ")"
            ),
        },
    }

    result = _run_hook(event)

    assert result.returncode == 2
    assert "fee-tier" in result.stderr.lower()


def test_blocks_write_that_drops_a_reconcile_strategy(tmp_path):
    target = _copy_target(tmp_path, "reconcile.py")
    original = target.read_text(encoding="utf-8")
    without_currency_strategy = original.replace(
        'Strategy("currency_conversion", currency_conversion),\n)',
        ")",
    )
    assert without_currency_strategy != original  # sanity: the replace actually changed something

    event = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(target), "content": without_currency_strategy},
    }

    result = _run_hook(event)

    assert result.returncode == 2
    assert "reconciliation-strategy" in result.stderr.lower()


def test_blocks_edit_that_changes_drift_hysteresis_condition(tmp_path):
    target = _copy_target(tmp_path, "drift.py")
    event = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(target),
            "old_string": "        if abs(reading.drift_percent) > threshold_percent:",
            "new_string": "        if abs(reading.drift_percent) > threshold_percent * 2:",
        },
    }

    result = _run_hook(event)

    assert result.returncode == 2
    assert "hysteresis" in result.stderr.lower()


def test_allows_logging_call_inserted_next_to_protected_drift_condition(tmp_path):
    target = _copy_target(tmp_path, "drift.py")
    event = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(target),
            "old_string": (
                "            # Alert immediately: ignores min_duration_minutes\n"
                "            return DriftAlert("
            ),
            "new_string": (
                "            # Alert immediately: ignores min_duration_minutes\n"
                "            logger.info(\"drift_alert_fired\", portfolio_id=portfolio_id, "
                "drift_percent=reading.drift_percent)\n"
                "            return DriftAlert("
            ),
        },
    }

    result = _run_hook(event)

    assert result.returncode == 0


def test_allows_unrelated_edit_to_a_protected_file(tmp_path):
    target = _copy_target(tmp_path, "fees.py")
    event = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(target),
            "old_string": "from dataclasses import dataclass",
            "new_string": (
                "from dataclasses import dataclass\n\n"
                "from agentic_framing.logging_utils import get_logger"
            ),
        },
    }

    result = _run_hook(event)

    assert result.returncode == 0


def test_ignores_files_with_no_registry_entry(tmp_path):
    target = _copy_target(tmp_path, "test_logging.py")
    event = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(target), "content": "# anything goes here"},
    }

    result = _run_hook(event)

    assert result.returncode == 0
