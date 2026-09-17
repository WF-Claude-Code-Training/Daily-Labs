#!/usr/bin/env python3
"""Lab 7 protected-region hook — PreToolUse.

Enforces this lab's own guardrails (README.md / AGENTS.md: "Don't touch fee-tier,
reconciliation-strategy, or hysteresis logic") as a denial, not just prose. Reads the hook
event JSON Claude Code passes on stdin, simulates the proposed Write/Edit/MultiEdit against the
on-disk file, and blocks (exit 2, reason on stderr) if a protected snippet from
protected_regions.json would be removed or altered. Everything else is allowed, including the
logger.info(...) calls this lab's Skill adds nearby — each registered snippet's boundary was
chosen in protected_regions.json to stop short of the intended log-call insertion point.

Usage (wired in ../settings.json):
    python3 .claude/hooks/protected_regions.py

Known limitation: this is a textual, exact-substring check, not an AST diff — a semantically
equivalent but reformatted rewrite of a protected snippet would also be blocked, and a protected
snippet that's already missing from the file (renamed by an earlier step) is silently skipped
rather than treated as an error. Both are acceptable tradeoffs for a training lab; a production
version would parse the AST instead of matching text.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent / "protected_regions.json"


def load_registry() -> list[dict]:
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data.get("protected_regions", [])


def apply_edit(content: str, old_string: str, new_string: str, replace_all: bool) -> str | None:
    """Return the simulated post-edit content, or None if old_string isn't present."""
    if old_string not in content:
        return None
    count = -1 if replace_all else 1
    return content.replace(old_string, new_string, count)


def simulated_content(tool_name: str, tool_input: dict, current: str) -> str | None:
    """Best-effort simulation of what the file will look like after this tool call."""
    if tool_name == "Write":
        return tool_input.get("content", "")

    if tool_name == "Edit":
        return apply_edit(
            current,
            tool_input.get("old_string", ""),
            tool_input.get("new_string", ""),
            bool(tool_input.get("replace_all", False)),
        )

    if tool_name == "MultiEdit":
        working = current
        for edit in tool_input.get("edits", []):
            result = apply_edit(
                working,
                edit.get("old_string", ""),
                edit.get("new_string", ""),
                bool(edit.get("replace_all", False)),
            )
            if result is None:
                return None
            working = result
        return working

    return None


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return 0  # can't parse the event — don't block on a hook-input problem

    tool_name = event.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return 0

    tool_input = event.get("tool_input", {})
    file_path = tool_input.get("file_path")
    if not file_path:
        return 0

    entries = [e for e in load_registry() if Path(file_path).name == e.get("path")]
    if not entries:
        return 0

    try:
        current = Path(file_path).read_text(encoding="utf-8")
    except OSError:
        return 0  # new file — nothing protected in it yet

    new_content = simulated_content(tool_name, tool_input, current)
    if new_content is None:
        return 0  # couldn't simulate (e.g. old_string not found) — let the tool itself error

    violations = [
        entry for entry in entries
        if entry["snippet"] in current and entry["snippet"] not in new_content
    ]
    if not violations:
        return 0

    lines = ["Blocked: this edit would remove or alter a protected region:"]
    for entry in violations:
        lines.append(f"  - {entry['path']}: {entry['reason']}")
    lines.append("Only add logging here — leave this logic exactly as it is.")
    print("\n".join(lines), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
