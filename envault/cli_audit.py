"""CLI sub-commands for the audit log: ``envault audit log`` and ``envault audit clear``."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from envault.audit import clear_log, read_log


def cmd_audit_log(args: argparse.Namespace) -> int:
    """Print recent audit entries to stdout."""
    entries = read_log(limit=args.limit)
    if not entries:
        print("No audit entries found.")
        return 0
    for e in entries:
        success_marker = "OK" if e.get("success") else "FAIL"
        profile_part = f" [{e['profile']}]" if e.get("profile") else ""
        path_part = f" {e['path']}" if e.get("path") else ""
        detail_part = f" — {e['detail']}" if e.get("detail") else ""
        print(f"{e['ts']}  {success_marker}  {e['action']}{profile_part}{path_part}{detail_part}")
    return 0


def cmd_audit_clear(args: argparse.Namespace) -> int:
    """Erase the audit log after optional confirmation."""
    if not getattr(args, "yes", False):
        answer = input("Clear audit log? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return 1
    clear_log()
    print("Audit log cleared.")
    return 0


def register_audit_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    audit_parser = subparsers.add_parser("audit", help="Manage the local audit log")
    audit_sub = audit_parser.add_subparsers(dest="audit_cmd", required=True)

    log_parser = audit_sub.add_parser("log", help="Show recent audit entries")
    log_parser.add_argument(
        "-n", "--limit", type=int, default=50, metavar="N",
        help="Maximum number of entries to display (default: 50)",
    )
    log_parser.set_defaults(func=cmd_audit_log)

    clear_parser = audit_sub.add_parser("clear", help="Erase the audit log")
    clear_parser.add_argument(
        "-y", "--yes", action="store_true",
        help="Skip confirmation prompt",
    )
    clear_parser.set_defaults(func=cmd_audit_clear)
