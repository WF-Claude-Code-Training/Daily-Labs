"""Run the WM-106 reconciliation triage report from the command line.

Standalone runner — this lab package has no CLI framework or shared app to hang this off of,
just this one entry point over `reconcile.triage`.

Usage (from this folder's root, opened as the workspace root):
    python3 run_reconcile.py fixtures/book_positions.csv fixtures/custodian_file.csv
"""

from __future__ import annotations

import argparse

from reconcile import TriageResult, load_positions, triage


def render_triage_report(report: TriageResult) -> str:
    """Render a TriageResult as MATCHED/RESOLVED/ESCALATED groups with an audit trail."""
    rule = "=" * 60
    lines = [rule, "  Reconciliation triage — book vs custodian", rule]
    if report.matched:
        lines.append(f"\nMATCHED ({len(report.matched)}):")
        lines += [f"  {r.symbol}" for r in report.matched]
    if report.resolved:
        lines.append(f"\nRESOLVED ({len(report.resolved)}):")
        lines += [f"  {r.symbol:<8} via {r.strategy}" for r in report.resolved]
    if report.escalated:
        lines.append(f"\nESCALATED ({len(report.escalated)}):")
        for r in report.escalated:
            tried = ", ".join(r.attempted_strategies) or "none"
            lines.append(f"  {r.symbol:<8} [{r.risk_level}]  tried [{tried}]")
            lines.append(f"      {r.detail}")
    lines.append("")
    lines.append(f"{len(report.matched)} matched, {len(report.resolved)} resolved, "
                 f"{len(report.escalated)} escalated")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile book vs custodian positions (WM-106).")
    parser.add_argument("book_file", help="CSV of book positions")
    parser.add_argument("custodian_file", help="CSV of custodian positions")
    args = parser.parse_args()

    try:
        book = load_positions(args.book_file)
        custodian = load_positions(args.custodian_file)
    except FileNotFoundError as exc:
        print(f"File not found: {exc}")
        return 1

    print(render_triage_report(triage(book, custodian)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
