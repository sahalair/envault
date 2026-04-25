"""CLI sub-commands for the *export* feature."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.cli import _resolve_passphrase
from envault.export import ExportError, export_to_env, export_to_shell_script


def cmd_export_env(args: argparse.Namespace) -> int:
    """Inject decrypted variables directly into the running process environment."""
    passphrase = _resolve_passphrase(args)
    if passphrase is None:
        print("error: passphrase required (use --passphrase or ENVAULT_PASSPHRASE)", file=sys.stderr)
        return 1

    enc_path = Path(args.enc_file)
    if not enc_path.exists():
        print(f"error: encrypted file not found: {enc_path}", file=sys.stderr)
        return 1

    try:
        variables = export_to_env(enc_path, passphrase, overwrite=args.overwrite)
    except ExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Exported {len(variables)} variable(s) into the current environment.")
        for key in variables:
            print(f"  {key}")
    return 0


def cmd_export_script(args: argparse.Namespace) -> int:
    """Write a shell-sourceable export script from an encrypted .env file."""
    passphrase = _resolve_passphrase(args)
    if passphrase is None:
        print("error: passphrase required (use --passphrase or ENVAULT_PASSPHRASE)", file=sys.stderr)
        return 1

    enc_path = Path(args.enc_file)
    if not enc_path.exists():
        print(f"error: encrypted file not found: {enc_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else None

    try:
        script_path = export_to_shell_script(enc_path, passphrase, output_path=output_path)
    except ExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Shell script written to: {script_path}")
        print(f"  source it with:  . {script_path}")
    return 0


def register_export_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach *export* sub-commands to *subparsers*."""
    export_parser = subparsers.add_parser("export", help="Export decrypted variables")
    export_sub = export_parser.add_subparsers(dest="export_cmd", required=True)

    # --- export env ---
    p_env = export_sub.add_parser("env", help="Inject variables into the current process environment")
    p_env.add_argument("enc_file", help="Path to the encrypted .env file")
    p_env.add_argument("--passphrase", default=None)
    p_env.add_argument("--overwrite", action="store_true", help="Overwrite existing env vars")
    p_env.add_argument("--quiet", action="store_true")
    p_env.set_defaults(func=cmd_export_env)

    # --- export script ---
    p_script = export_sub.add_parser("script", help="Write a sourceable shell export script")
    p_script.add_argument("enc_file", help="Path to the encrypted .env file")
    p_script.add_argument("--passphrase", default=None)
    p_script.add_argument("--output", default=None, help="Destination path for the shell script")
    p_script.add_argument("--quiet", action="store_true")
    p_script.set_defaults(func=cmd_export_script)
