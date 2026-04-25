"""CLI subcommands for importing secrets into a .env file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.import_env import ImportError as EnvImportError  # noqa: A004
from envault.import_env import import_from_environ, import_from_file


def cmd_import_file(args: argparse.Namespace) -> int:
    """Import key/value pairs from another .env file."""
    source = Path(args.source)
    dest = Path(args.dest)
    overwrite: bool = args.overwrite

    try:
        imported = import_from_file(source, dest, overwrite=overwrite)
    except EnvImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if imported:
        print(f"Imported {len(imported)} key(s) into {dest}:")
        for key in imported:
            print(f"  + {key}")
    else:
        print("No new keys imported (use --overwrite to replace existing keys).")
    return 0


def cmd_import_env(args: argparse.Namespace) -> int:
    """Import keys from the current process environment."""
    dest = Path(args.dest)
    keys = args.keys if args.keys else None
    overwrite: bool = args.overwrite

    try:
        imported = import_from_environ(keys, dest, overwrite=overwrite)
    except EnvImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if imported:
        print(f"Imported {len(imported)} key(s) from environment into {dest}:")
        for key in imported:
            print(f"  + {key}")
    else:
        print("No new keys imported (use --overwrite to replace existing keys).")
    return 0


def register_import_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach 'import' sub-commands to *subparsers*."""
    import_parser = subparsers.add_parser("import", help="Import secrets into a .env file")
    import_sub = import_parser.add_subparsers(dest="import_cmd", required=True)

    # import file
    p_file = import_sub.add_parser("file", help="Import from another .env file")
    p_file.add_argument("source", help="Path to the source .env file")
    p_file.add_argument(
        "dest",
        nargs="?",
        default=".env",
        help="Destination .env file (default: .env)",
    )
    p_file.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing keys in the destination",
    )
    p_file.set_defaults(func=cmd_import_file)

    # import env
    p_env = import_sub.add_parser("env", help="Import from the current shell environment")
    p_env.add_argument(
        "keys",
        nargs="*",
        help="Specific keys to import (omit to import all)",
    )
    p_env.add_argument(
        "--dest",
        default=".env",
        help="Destination .env file (default: .env)",
    )
    p_env.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing keys in the destination",
    )
    p_env.set_defaults(func=cmd_import_env)
