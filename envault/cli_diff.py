"""cli_diff.py – CLI sub-commands for the diff feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.diff import DiffError, diff_env, has_changes


def cmd_diff(args: argparse.Namespace) -> int:
    """Print a unified diff between the local .env and the vault .enc file.

    Exit codes
    ----------
    0  – files are identical (or --check passed and no differences found)
    1  – differences exist (or an error occurred)
    """
    env_path = Path(args.env_file)
    enc_path = Path(args.enc_file)
    passphrase: str = args.passphrase

    try:
        result = diff_env(env_path, enc_path, passphrase, context_lines=args.context)
    except DiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.check:
        if result:
            print("Differences found between local .env and vault.", file=sys.stderr)
            return 1
        print("No differences found.")
        return 0

    if result:
        print(result, end="")
        return 1  # mimic `diff` exit-code convention: 1 = differences
    print("No differences found.")
    return 0


def register_diff_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach the *diff* sub-command to *subparsers*."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "diff",
        help="Show differences between the local .env and the encrypted vault file.",
    )
    parser.add_argument(
        "env_file",
        nargs="?",
        default=".env",
        help="Path to the plaintext .env file (default: .env).",
    )
    parser.add_argument(
        "enc_file",
        nargs="?",
        default=".env.enc",
        help="Path to the encrypted vault file (default: .env.enc).",
    )
    parser.add_argument(
        "-p",
        "--passphrase",
        required=True,
        help="Passphrase to decrypt the vault file.",
    )
    parser.add_argument(
        "-U",
        "--context",
        type=int,
        default=3,
        metavar="N",
        help="Number of context lines in the diff output (default: 3).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with code 1 if differences exist, 0 otherwise (no diff printed).",
    )
    parser.set_defaults(func=cmd_diff)
