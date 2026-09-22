#!/usr/bin/env python3
"""Verifiable target for the *role pod*. Do your subagent definitions honor their contracts?

Authoring a subagent is easy to fake. You can write a file called `contract-reviewer.md`, give
it every tool in the box, and it will happily "review" its own patches. This script turns the
role contracts in ROLES.md into something checkable: it parses each agent definition's
frontmatter and verifies the tool grants and denials the role actually depends on.

Stdlib only, offline, deterministic: no pytest, no YAML library, no network.

    python3 check_pod.py                       # check Lab 7's required pod
    python3 check_pod.py --scope both          # also look in ~/.claude/agents/

Exit code 0 = every required role present and contract-clean. 1 = something to fix.

Why a script and not "read it and see": the whole argument for a read-only reviewer is that the
restriction is *enforced* rather than promised. A promise you never check is just prose.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ── Role contracts ───────────────────────────────────────────────────────────
#
# `must`     : tools the role cannot do its job without.
# `must_not` : tools whose presence defeats the point of the role.
#
# Keep this table in sync with ROLES.md; it is the machine-readable half of the same document.

ROLE_CONTRACTS: dict[str, dict] = {
    "contract-reviewer": {
        "must": {"Read"},
        "must_not": {"Edit", "Write", "MultiEdit", "NotebookEdit", "Bash", "Task"},
        "enforced": True,
        "why": "a reviewer that can patch the code, or shell out to do it, is not an independent reviewer",
    },
    "reference-data-steward": {
        "must": {"Read", "Grep"},
        "must_not": {"Edit", "Write", "MultiEdit", "NotebookEdit", "Bash", "Task"},
        "enforced": True,
        "why": "it judges whether a value belongs in code or in config, a judgment it would corrupt by being able to move the value itself",
    },
    "test-author": {
        "must": {"Read", "Write", "Edit", "Bash"},
        "must_not": {"Task"},
        "enforced": False,
        "why": "it owns test files and runs them; 'tests only' is its contract, not something a tools list can enforce",
    },
    "implementer": {
        "must": {"Read", "Edit", "Bash"},
        "must_not": {"Task"},
        "enforced": False,
        "why": "it changes source and verifies with pytest; 'never edit a test to go green' is its contract, not a tool restriction",
    },
    "impact-mapper": {
        "must": {"Read", "Grep", "Glob"},
        "must_not": {"Edit", "Write", "MultiEdit", "Bash"},
        "enforced": True,
        "why": "it maps blast radius before anyone edits, it has no business editing anything itself",
    },
    "release-scribe": {
        "must": {"Read", "Write"},
        "must_not": {"Edit", "MultiEdit"},
        "enforced": False,
        "why": "it writes notes as new files; denying Edit keeps a docs pass from becoming a code pass",
    },
    "risk-officer": {
        "must": {"Read", "Grep"},
        "must_not": {"Edit", "Write", "MultiEdit", "Bash"},
        "enforced": True,
        "why": "a governance reviewer that can quietly fix what it flags leaves no audit trail of the finding",
    },
}

# Lab 7 pairs the pre-built `logging-reviewer` with a governance role the engineer authors.
# Two reviewers with different checklists is the point: see ROLES.md. `implementer` and
# `contract-reviewer` are NOT part of the required pod here: neither does any work in this
# lab's required flow (Lab 7's implementation is done by the Skill, not a subagent, and its
# review story is logging-reviewer vs risk-officer, not a third generic reviewer). `implementer`
# only matters for the optional agent-scoped-hook stretch goal: check for it there with
# `--require implementer` if you're attempting it, not by default.
DEFAULT_POD = ("risk-officer",)

MIN_DESCRIPTION_CHARS = 60


# ── A deliberately small frontmatter parser ──────────────────────────────────


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Pull the leading `---` block into a flat dict. Returns None if there isn't one.

    Only handles the flat `key: value` shape a subagent definition uses. Nested YAML (e.g. a
    `hooks:` block) is skipped rather than parsed. This checker only cares about the scalar
    keys, so a `hooks:` entry is neither validated nor treated as an error.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None

    fields: dict[str, str] = {}
    key: str | None = None
    for raw in lines[1:end]:
        if not raw.strip():
            continue
        if raw.startswith((" ", "\t", "-")) and key:
            # Continuation of a folded scalar (`description: >-`): append it.
            fields[key] = f"{fields[key]} {raw.strip()}".strip()
            continue
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        key = key.strip()
        fields[key] = value.strip().lstrip(">|-").strip()
    return fields


def parse_tools(value: str) -> set[str]:
    """`tools: Read, Grep, Glob` -> {'Read','Grep','Glob'}. Empty/absent means *all tools*."""
    return {t.strip() for t in value.split(",") if t.strip()}


def agent_files(scope: str, project_root: Path) -> list[Path]:
    roots: list[Path] = []
    if scope in ("project", "both"):
        roots.append(project_root / ".claude" / "agents")
    if scope in ("personal", "both"):
        roots.append(Path.home() / ".claude" / "agents")
    found: list[Path] = []
    for root in roots:
        if root.is_dir():
            found.extend(sorted(root.glob("*.md")))
    return found


# ── Checks ───────────────────────────────────────────────────────────────────


def check_role(name: str, path: Path, fields: dict[str, str]) -> list[str]:
    """Return a list of problems with this role definition. Empty list = clean."""
    problems: list[str] = []
    contract = ROLE_CONTRACTS[name]

    declared = fields.get("tools", "")
    if not declared:
        problems.append(
            "no `tools:` line. The role inherits EVERY tool, so its restriction is imaginary. "
            f"Declare the narrowest set that works ({contract['why']})."
        )
    else:
        tools = parse_tools(declared)
        missing = contract["must"] - tools
        if missing:
            problems.append(f"missing required tool(s): {', '.join(sorted(missing))}")
        granted = contract["must_not"] & tools
        if granted:
            problems.append(
                f"grants forbidden tool(s): {', '.join(sorted(granted))}; {contract['why']}"
            )

    description = fields.get("description", "")
    if len(description) < MIN_DESCRIPTION_CHARS:
        problems.append(
            f"`description:` is {len(description)} chars; aim for {MIN_DESCRIPTION_CHARS}+ that say "
            "*when to use this role*. Proactive delegation is matched against this text. A vague "
            "description means Claude does the work inline instead of delegating."
        )
    if not fields.get("model"):
        problems.append("no `model:` line. Pick one deliberately rather than inheriting by accident")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate subagent role definitions against ROLES.md.")
    parser.add_argument("--require", default=",".join(DEFAULT_POD),
                        help="comma-separated role names that must exist (default: Lab 7's pod)")
    parser.add_argument("--scope", default="project", choices=("project", "personal", "both"),
                        help="where to look for agent definitions (default: project)")
    args = parser.parse_args()

    required = [r.strip() for r in args.require.split(",") if r.strip()]
    unknown = [r for r in required if r not in ROLE_CONTRACTS]
    if unknown:
        print(f"No contract defined for: {', '.join(unknown)}")
        print(f"Known roles: {', '.join(sorted(ROLE_CONTRACTS))}")
        return 2

    project_root = Path(__file__).resolve().parent
    definitions: dict[str, tuple[Path, dict[str, str]]] = {}
    malformed: list[Path] = []
    for path in agent_files(args.scope, project_root):
        fields = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fields is None:
            malformed.append(path)
            continue
        definitions[fields.get("name", path.stem)] = (path, fields)

    print("Role pod check")
    print("=" * 62)

    failures = 0

    for path in malformed:
        print(f"[FAIL] {path.name}: no `---` frontmatter block. Claude Code will not load this")
        failures += 1

    for name in required:
        if name not in definitions:
            print(f"[FAIL] {name}: not found in the agent directories searched ({args.scope})")
            print(f"       expected a file whose frontmatter has `name: {name}`")
            failures += 1
            continue
        path, fields = definitions[name]
        problems = check_role(name, path, fields)
        if not problems:
            kind = "tool-enforced" if ROLE_CONTRACTS[name]["enforced"] else "contract-only"
            print(f"[ok]   {name}  ({path.name}, {kind})")
            print(f"       tools: {fields.get('tools') or 'ALL, see below'}")
        else:
            print(f"[FAIL] {name}  ({path.name})")
            for problem in problems:
                print(f"       - {problem}")
            failures += len(problems)

    # ── Pod-level check: the parallel-writer hazard ──────────────────────────
    #
    # Plain subagents share one working tree. Two roles holding Edit at the same time is the
    # single most reliable way to lose work in a fan-out, and no per-role check catches it.
    writers = sorted(
        name for name, (_, fields) in definitions.items()
        if name in required and {"Edit", "Write", "MultiEdit"} & parse_tools(fields.get("tools", ""))
    )
    print("-" * 62)
    editors = sorted(
        name for name, (_, fields) in definitions.items()
        if name in required and {"Edit", "MultiEdit"} & parse_tools(fields.get("tools", ""))
    )
    print(f"Roles that can write files: {', '.join(writers) or 'none'}")
    if len(editors) > 1:
        print(f"[WARN] more than one role can Edit existing files: {', '.join(editors)}.")
        print("       Subagents share one working tree. Never run two of these in parallel on")
        print("       the same file. Fan out reads and reviews; serialize edits.")

    contract_only = sorted(n for n in required
                           if n in definitions and not ROLE_CONTRACTS[n]["enforced"])
    if contract_only:
        print(f"Contract-only (not tool-enforced): {', '.join(contract_only)}")
        print("       A `tools:` list gates tool TYPES, not file PATHS. These roles can be told")
        print("       which files they own; they cannot be prevented from touching others. That")
        print("       gap is real. Lab 7 introduces the layer (a PreToolUse hook) that closes it.")

    print("=" * 62)
    if failures:
        print(f"{failures} problem(s) to fix. Re-run when you've addressed them.")
        return 1
    print(f"Pod is contract-clean: {', '.join(required)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
