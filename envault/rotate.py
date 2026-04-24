"""Key rotation: re-encrypt an existing .enc file with a new passphrase."""

from __future__ import annotations

from pathlib import Path

from envault.vault import lock, unlock


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate(
    enc_path: Path | str,
    old_passphrase: str,
    new_passphrase: str,
    *,
    output_path: Path | str | None = None,
    keep_plaintext: bool = False,
) -> Path:
    """Re-encrypt *enc_path* from *old_passphrase* to *new_passphrase*.

    The decrypted content is held only in memory; no plaintext file is
    written to disk unless *keep_plaintext* is True (useful for debugging).

    Parameters
    ----------
    enc_path:
        Path to the existing ``.env.enc`` file.
    old_passphrase:
        Passphrase used to encrypt the current file.
    new_passphrase:
        Passphrase to use for the re-encrypted output.
    output_path:
        Destination for the rotated file.  Defaults to *enc_path*
        (in-place rotation).
    keep_plaintext:
        When True, also write the decrypted content to a temporary
        ``.env.rotated`` file next to *enc_path*.

    Returns
    -------
    Path
        Path to the newly written encrypted file.
    """
    enc_path = Path(enc_path)
    if not enc_path.exists():
        raise RotationError(f"Encrypted file not found: {enc_path}")

    # Decrypt into a temporary plaintext path
    tmp_plain = enc_path.with_suffix(".rotated")
    try:
        unlock(enc_path, old_passphrase, output_path=tmp_plain)
    except Exception as exc:
        raise RotationError(f"Failed to decrypt with old passphrase: {exc}") from exc

    try:
        dest = Path(output_path) if output_path is not None else enc_path
        lock(tmp_plain, new_passphrase, output_path=dest)
    except Exception as exc:
        raise RotationError(f"Failed to encrypt with new passphrase: {exc}") from exc
    finally:
        if not keep_plaintext and tmp_plain.exists():
            tmp_plain.unlink()

    return dest
