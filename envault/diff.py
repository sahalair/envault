"""diff.py – Compare a decrypted .env file against a locked .enc file.

Provides a human-readable diff between the current plaintext .env and the
contents stored in the encrypted vault file, without permanently decrypting
the vault file to disk.
"""
from __future__ import annotations

import difflib
import io
from pathlib import Path
from typing import Sequence

from envault.vault import unlock


class DiffError(Exception):
    """Raised when the diff operation cannot be completed."""


def _read_lines(path: Path) -> list[str]:
    """Return the lines of *path*, each ending with '\n'."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    # Ensure final newline for clean diff output
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    return lines


def _decrypt_to_lines(enc_path: Path, passphrase: str) -> list[str]:
    """Decrypt *enc_path* using *passphrase* and return its lines.

    Uses a temporary directory so the plaintext never persists on disk beyond
    the scope of this helper.

    Raises
    ------
    DiffError
        If decryption fails for any reason.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_plain = Path(tmp) / "vault_plain.env"
        try:
            unlock(enc_path, passphrase, output_path=tmp_plain)
        except Exception as exc:  # noqa: BLE001
            raise DiffError(f"Failed to decrypt vault file: {exc}") from exc
        return _read_lines(tmp_plain)


def diff_env(
    env_path: Path,
    enc_path: Path,
    passphrase: str,
    *,
    context_lines: int = 3,
) -> str:
    """Return a unified diff string between *env_path* and the decrypted *enc_path*.

    Parameters
    ----------
    env_path:
        Path to the current plaintext ``.env`` file.
    enc_path:
        Path to the encrypted ``.env.enc`` vault file.
    passphrase:
        Passphrase used to decrypt *enc_path*.
    context_lines:
        Number of context lines in the unified diff output.

    Returns
    -------
    str
        Unified diff text.  Empty string means the files are identical.
    """
    if not env_path.exists():
        raise DiffError(f"Plaintext file not found: {env_path}")
    if not enc_path.exists():
        raise DiffError(f"Encrypted file not found: {enc_path}")

    vault_lines = _decrypt_to_lines(enc_path, passphrase)
    current_lines = _read_lines(env_path)

    diff_lines: Sequence[str] = list(
        difflib.unified_diff(
            vault_lines,
            current_lines,
            fromfile=f"vault:{enc_path.name}",
            tofile=f"local:{env_path.name}",
            n=context_lines,
        )
    )
    return "".join(diff_lines)


def has_changes(env_path: Path, enc_path: Path, passphrase: str) -> bool:
    """Return *True* if *env_path* differs from the decrypted *enc_path*."""
    return bool(diff_env(env_path, enc_path, passphrase))
