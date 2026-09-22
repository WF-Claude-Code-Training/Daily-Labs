"""Tests for the worked-example hook (`.claude/hooks/no_print.py`).

**These pass on a fresh checkout.** They're here as proof the example hook actually works, and
as the template for how a hook gets tested, which is the same shape
`test_protected_regions_hook.py` uses for the hook you write in Part 2.

Read this file before you write your hook. The mechanics it demonstrates are the mechanics
you'll need:

  * Run the hook as a **subprocess**, feeding it PreToolUse JSON on **stdin**, exactly how
    Claude Code invokes it. Don't import and call its functions; test the real interface.
  * Assert on the **exit code**: `2` = blocked, `0` = allowed.
  * When it blocks, assert the **stderr** message says something useful. Claude Code feeds
    stderr back to the model, so an unhelpful reason is a real defect, not a cosmetic one.
  * Copy targets into `tmp_path` first. A hook test that runs against the repo's own files can
    corrupt this lab when an assertion fails partway through.

Note what *isn't* tested here: that Claude Code invokes the hook at all. That's wiring, not
logic, and the only way to check it is to try an edit yourself and watch the denial, which is
why Part 2 has you do exactly that.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
HOOK = REPO_ROOT / ".claude" / "hooks" / "no_print.py"


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


# ── Blocking: a print() added to a guarded module ────────────────────────────


def test_blocks_edit_that_adds_a_print_call(tmp_path):
    target = _copy_target(tmp_path, "fees.py")
    result = _run_hook({
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(target),
            "old_string": "    return round(aum * (tier.rate_bps / 10_000), 2)",
            "new_string": ('    print(f"fee for {aum}")\n'
                           "    return round(aum * (tier.rate_bps / 10_000), 2)"),
        },
    })

    assert result.returncode == 2
    assert "print()" in result.stderr
    # The reason has to point at the alternative, not just say no.
    assert "get_logger" in result.stderr


def test_blocks_multiedit_when_any_edit_adds_a_print(tmp_path):
    """One bad edit in a batch is enough. The hook can't allow a call partially."""
    target = _copy_target(tmp_path, "drift.py")
    result = _run_hook({
        "tool_name": "MultiEdit",
        "tool_input": {
            "file_path": str(target),
            "edits": [
                {"old_string": "from datetime import datetime",
                 "new_string": ("from datetime import datetime\n\n"
                                "from agentic_framing.logging_utils import get_logger")},
                {"old_string": "    if not readings:",
                 "new_string": '    print("checking drift")\n    if not readings:'},
            ],
        },
    })

    assert result.returncode == 2


def test_blocks_write_that_introduces_a_print(tmp_path):
    target = _copy_target(tmp_path, "reconcile.py")
    content = target.read_text(encoding="utf-8").replace(
        "    return results", '    print(results)\n    return results', 1)
    result = _run_hook({
        "tool_name": "Write",
        "tool_input": {"file_path": str(target), "content": content},
    })

    assert result.returncode == 2


# ── Allowing: everything else ────────────────────────────────────────────────


def test_allows_the_logging_call_this_ticket_actually_wants(tmp_path):
    """The whole point. A hook that blocks the intended change gets disabled on day one."""
    target = _copy_target(tmp_path, "fees.py")
    result = _run_hook({
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(target),
            "old_string": "    return round(aum * (tier.rate_bps / 10_000), 2)",
            "new_string": ("    fee = round(aum * (tier.rate_bps / 10_000), 2)\n"
                           '    logger.info("fee_calculated", aum=aum, fee=fee)\n'
                           "    return fee"),
        },
    })

    assert result.returncode == 0


def test_allows_a_write_that_preserves_an_existing_print(tmp_path):
    """Counts, not presence: a whole-file rewrite shouldn't be blocked by a print it inherited.

    Getting this wrong makes the hook unusable: any `Write` to a file that already contains a
    `print()` would be refused forever, including the edit that removes it.
    """
    target = tmp_path / "fees.py"
    shutil.copy(REPO_ROOT / "fees.py", target)
    with_print = target.read_text(encoding="utf-8") + '\n\nprint("legacy debug line")\n'
    target.write_text(with_print, encoding="utf-8")

    result = _run_hook({
        "tool_name": "Write",
        "tool_input": {"file_path": str(target), "content": with_print},
    })

    assert result.returncode == 0


def test_allows_print_in_a_module_this_ticket_does_not_name(tmp_path):
    """Scope discipline. WM-109 named three modules; the hook has no opinion about the rest."""
    target = _copy_target(tmp_path, "test_logging.py")
    result = _run_hook({
        "tool_name": "Write",
        "tool_input": {"file_path": str(target), "content": 'print("fine here")\n'},
    })

    assert result.returncode == 0


def test_ignores_tools_that_do_not_modify_files():
    result = _run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "python3 -c 'print(1)'"},
    })

    assert result.returncode == 0


# ── Fail open: the design decision, made testable ────────────────────────────


def test_malformed_hook_input_does_not_block():
    """Documented as "fail open" in the hook's docstring. So it's asserted, not assumed.

    Your hook gets to make the opposite choice. Whichever you pick, pin it down with a test like
    this one: a fail-open/fail-closed decision that lives only in a comment will drift.
    """
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="this is not json",
        text=True, capture_output=True,
    )

    assert result.returncode == 0


def test_missing_file_path_does_not_block():
    result = _run_hook({"tool_name": "Edit", "tool_input": {"old_string": "a", "new_string": "b"}})

    assert result.returncode == 0
