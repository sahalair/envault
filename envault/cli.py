"""Command-line interface for envault.

Provides `lock` and `unlock` subcommands to encrypt and decrypt .env files.
Passphrases can be supplied via the --passphrase flag or the ENVAULT_PASSPHRASE
environment variable to support non-interactive / CI usage.
"""

import os
import sys
import argparse
import getpass

from envault.vault import lock, unlock


def _resolve_passphrase(args: argparse.Namespace) -> str:
    """Return the passphrase from CLI flag, env var, or interactive prompt.

    Priority order:
    1. --passphrase flag
    2. ENVAULT_PASSPHRASE environment variable
    3. Interactive prompt (hidden input)
    """
    if args.passphrase:
        return args.passphrase

    env_pass = os.environ.get("ENVAULT_PASSPHRASE")
    if env_pass:
        return env_pass

    return getpass.getpass("Passphrase: ")


def cmd_lock(args: argparse.Namespace) -> int:
    """Handle the `envault lock` subcommand."""
    passphrase = _resolve_passphrase(args)

    output = args.output  # may be None; vault.lock will derive a default
    try:
        out_path = lock(args.env_file, passphrase, output_path=output)
        print(f"Locked  → {out_path}")
        return 0
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: failed to lock file — {exc}", file=sys.stderr)
        return 1


def cmd_unlock(args: argparse.Namespace) -> int:
    """Handle the `envault unlock` subcommand."""
    passphrase = _resolve_passphrase(args)

    output = args.output
    try:
        out_path = unlock(args.enc_file, passphrase, output_path=output)
        print(f"Unlocked → {out_path}")
        return 0
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        # Wrong passphrase or tampered ciphertext
        print(f"error: decryption failed — {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: failed to unlock file — {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Local-first secrets manager — encrypt and sync .env files.",
    )
    parser.add_argument(
        "--passphrase",
        metavar="PASS",
        default=None,
        help="Passphrase for encryption/decryption (overrides ENVAULT_PASSPHRASE env var).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- lock ---
    lock_parser = subparsers.add_parser(
        "lock",
        help="Encrypt a .env file into an .env.enc file.",
    )
    lock_parser.add_argument(
        "env_file",
        metavar="ENV_FILE",
        help="Path to the plaintext .env file to encrypt.",
    )
    lock_parser.add_argument(
        "-o", "--output",
        metavar="OUTPUT",
        default=None,
        help="Destination path for the encrypted file (default: <ENV_FILE>.enc).",
    )
    lock_parser.set_defaults(func=cmd_lock)

    # --- unlock ---
    unlock_parser = subparsers.add_parser(
        "unlock",
        help="Decrypt an .env.enc file back into a .env file.",
    )
    unlock_parser.add_argument(
        "enc_file",
        metavar="ENC_FILE",
        help="Path to the encrypted .env.enc file to decrypt.",
    )
    unlock_parser.add_argument(
        "-o", "--output",
        metavar="OUTPUT",
        default=None,
        help="Destination path for the decrypted file (default: strip .enc suffix).",
    )
    unlock_parser.set_defaults(func=cmd_unlock)

    return parser


def main() -> None:
    """Entry point invoked by the `envault` console script."""
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
