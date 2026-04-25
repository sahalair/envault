"""CLI sub-commands for vault search."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.cli import _resolve_passphrase
from envault.search import SearchError, search


def cmd_search(args: argparse.Namespace) -> int:
    """Search an encrypted vault for matching keys / values."""
    passphrase = _resolve_passphrase(args)
    if passphrase is None:
        print("error: passphrase is required", file=sys.stderr)
        return 1

    enc_file = Path(args.enc_file)
    if not enc_file.exists():
        print(f"error: encrypted file not found: {enc_file}", file=sys.stderr)
        return 1

    try:
        result = search(
            enc_file,
            passphrase,
            args.pattern,
            search_values=args.values,
            case_sensitive=args.case_sensitive,
            use_regex=args.regex,
        )
    except SearchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not result.found:
        print("No matches found.")
        return 0

    print(f"Found {len(result.matches)} match(es) in {enc_file}:\n")
    for match in result.matches:
        if args.show_values:
            print(f"  line {match.line_number:>4}: {match.key}={match.value}")
        else:
            print(f"  line {match.line_number:>4}: {match.key}")

    return 0


def register_search_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach the *search* sub-command to *subparsers*."""
    p = subparsers.add_parser("search", help="Search keys/values inside an encrypted vault")
    p.add_argument("enc_file", help="Path to the encrypted .env.enc file")
    p.add_argument("pattern", help="Glob pattern (or regex with --regex) to search for")
    p.add_argument(
        "--values",
        action="store_true",
        default=False,
        help="Also search inside values (not just keys)",
    )
    p.add_argument(
        "--show-values",
        dest="show_values",
        action="store_true",
        default=False,
        help="Display matched values in output",
    )
    p.add_argument(
        "--case-sensitive",
        dest="case_sensitive",
        action="store_true",
        default=False,
        help="Enable case-sensitive matching",
    )
    p.add_argument(
        "--regex",
        action="store_true",
        default=False,
        help="Treat pattern as a regular expression",
    )
    p.add_argument("-p", "--passphrase", default=None, help="Encryption passphrase")
    p.add_argument(
        "--passphrase-env",
        dest="passphrase_env",
        default="ENVAULT_PASSPHRASE",
        metavar="VAR",
        help="Environment variable holding the passphrase (default: ENVAULT_PASSPHRASE)",
    )
    p.set_defaults(func=cmd_search)
