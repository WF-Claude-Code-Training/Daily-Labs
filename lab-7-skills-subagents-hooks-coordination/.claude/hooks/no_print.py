#!/usr/bin/env python3
"""A working PreToolUse hook — WM-109's "not printed" requirement, enforced.

**This is the worked example.** Read it before you write `protected_regions.py`. It is a
complete, tested, wired-up hook, and it is deliberately the *opposite shape* to the one you're
about to build — so it's a template for the mechanics, not an answer you can rename.

    This hook (additive check):     does the change ADD something forbidden?
    Yours (subtractive check):      does the change REMOVE something required?

Both answer the same question — "should this tool call be allowed?" — from opposite directions.
Ours can look only at what the change introduces. Yours has to simulate the change against
what's on disk and check that a protected snippet survived, which is why yours is the harder one.

## What it enforces

WM-109 says every audit-worthy event must be "logged as a structured (JSON) event — **not
printed**, not silently dropped." A `print()` added to a domain module during a logging rollout
is always the wrong answer: it isn't parseable, it isn't queryable, it goes to stdout where
nothing collects it, and it looks like progress. This hook makes adding one impossible in the
three modules the ticket names.

## The hook contract (identical for the one you'll write)

- Claude Code sends the PreToolUse event as **JSON on stdin**.
- **Exit 0** = allow. **Exit 2** = block, with the reason on **stderr** — Claude Code feeds
  stderr back to the model, so the message is a prompt, not a log line. Write it for a reader
  who has to decide what to do next.
- Any other exit code is treated as an error and does not block.

## A design decision worth copying: fail open

Every `return 0` below marked "can't tell" is a deliberate choice. If the hook can't parse its
input, can't read the file, or can't work out what the change would do, it **allows** the call.

The reasoning is specific to what's being protected. A missed `print()` is caught by review, by
the Skill's checker, and by the reviewer subagents — this hook is one layer of several, so
failing open costs a little coverage and never blocks legitimate work. **Your hook protects
something different**: a silently mispriced fee table that review already missed once (see
WM-121). Decide fail-open vs fail-closed for yourself, on those terms, and write down why.

## Known limitation, stated rather than discovered

The check is textual (a regex for `print(`), not an AST walk. `getattr(builtins, "pri" + "nt")`
walks straight past it. That's an acceptable trade for a training lab and for this guardrail —
someone assembling `print` from string fragments is not making an honest mistake, and this hook
is aimed at honest mistakes. A hook aimed at adversaries would need to parse the AST.

Wired in ../settings.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# The modules WM-109 names. Note this list lives in code, unlike the registry your hook reads
# from `protected_regions.json` — and that difference is on purpose. This list changes when the
# *ticket* changes, so code is the right home. Protected-region snippets change when *policy*
# changes, which is someone else's job and shouldn't require a release. Same lesson as Lab 4's
# WM-115: where a value lives is a question about who owns it.
GUARDED_MODULES = ("fees.py", "reconcile.py", "drift.py")

PRINT_CALL = re.compile(r"\bprint\s*\(")


def added_text(tool_name: str, tool_input: dict, current: str) -> str | None:
    """The text this tool call would introduce, or None if we can't tell.

    For `Edit`/`MultiEdit` that's just the replacement string(s) — we don't need to simulate the
    whole file, because we only care about what's new. For `Write` there is no "new" portion, so
    the caller compares counts against the current content instead.
    """
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name == "Edit":
        return tool_input.get("new_string", "")
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        return "\n".join(e.get("new_string", "") for e in edits)
    return None


def introduces_print(tool_name: str, new_text: str, current: str) -> bool:
    """Would this call leave the file with a `print(` it doesn't already have?

    A whole-file `Write` that preserves existing prints shouldn't be blocked, so for `Write` we
    compare counts rather than presence. For the edit tools, any `print(` in the replacement
    text is new by definition.
    """
    if tool_name == "Write":
        return len(PRINT_CALL.findall(new_text)) > len(PRINT_CALL.findall(current))
    return bool(PRINT_CALL.search(new_text))


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return 0  # can't tell — see "fail open" above

    tool_name = event.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return 0  # not a file-modifying tool

    tool_input = event.get("tool_input", {})
    file_path = tool_input.get("file_path")
    if not file_path or Path(file_path).name not in GUARDED_MODULES:
        return 0  # not a module this ticket protects

    new_text = added_text(tool_name, tool_input, "")
    if new_text is None:
        return 0  # can't tell

    try:
        current = Path(file_path).read_text(encoding="utf-8")
    except OSError:
        current = ""  # new file — everything in it is added

    if not introduces_print(tool_name, new_text, current):
        return 0

    print(
        f"Blocked: this edit would add a print() call to {Path(file_path).name}.\n"
        "WM-109 requires a structured log event, not printed output — print() isn't parseable,\n"
        "isn't queryable, and goes to stdout where nothing collects it.\n"
        "Use the shared logger instead:\n"
        "    from agentic_framing.logging_utils import get_logger\n"
        '    logger = get_logger("<domain>")\n'
        '    logger.info("<event_name>", field=value)',
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
