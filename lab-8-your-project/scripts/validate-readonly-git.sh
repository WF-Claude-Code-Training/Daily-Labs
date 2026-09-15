#!/bin/bash
# PreToolUse hook for the pattern-scout subagent's Bash tool.
#
# pattern-scout is only allowed to run read-only `git` history inspection — everything else,
# including any non-git command, is blocked here rather than left to the subagent's judgment.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  exit 0
fi

TRIMMED=$(echo "$COMMAND" | sed -E 's/^[[:space:]]+//')

if ! echo "$TRIMMED" | grep -qE '^git[[:space:]]'; then
  echo "Blocked: pattern-scout may only run 'git' commands via Bash — use Read/Grep/Glob for everything else." >&2
  exit 2
fi

if ! echo "$TRIMMED" | grep -qE '^git[[:space:]]+(log|blame|shortlog|show|diff|status|ls-files|rev-parse|grep|branch)([[:space:]]|$)'; then
  echo "Blocked: only read-only git subcommands are allowed (log, blame, shortlog, show, diff, status, ls-files, rev-parse, grep, branch)." >&2
  exit 2
fi

exit 0
