"""High-level vault operations: lock (encrypt) and unlock (decrypt) .env files."""

from pathlib import Path
from envault.crypto import encrypt, decrypt

ENCRYPTED_EXTENSION = ".enc"


def lock(env_path: str | Path, passphrase: str, output_path: str | Path | None = None) -> Path:
    """Encrypt an .env file and write the encrypted bundle to disk.

    Args:
        env_path: Path to the plaintext .env file.
        passphrase: Secret passphrase used to derive the encryption key.
        output_path: Destination for the encrypted file. Defaults to
                     <env_path>.enc alongside the original file.

    Returns:
        Path to the written encrypted file.
    """
    env_path = Path(env_path)
    if output_path is None:
        output_path = env_path.with_suffix(env_path.suffix + ENCRYPTED_EXTENSION)
    output_path = Path(output_path)

    plaintext = env_path.read_text(encoding="utf-8")
    encrypted = encrypt(plaintext, passphrase)
    output_path.write_text(encrypted, encoding="utf-8")
    return output_path


def unlock(enc_path: str | Path, passphrase: str, output_path: str | Path | None = None) -> Path:
    """Decrypt an encrypted .env bundle and write the plaintext to disk.

    Args:
        enc_path: Path to the encrypted bundle file.
        passphrase: Secret passphrase used to derive the decryption key.
        output_path: Destination for the decrypted file. Defaults to stripping
                     the .enc extension from the encrypted file name.

    Returns:
        Path to the written plaintext file.
    """
    enc_path = Path(enc_path)
    if output_path is None:
        stem = enc_path.stem  # removes .enc
        output_path = enc_path.with_name(stem)
    output_path = Path(output_path)

    encoded = enc_path.read_text(encoding="utf-8")
    plaintext = decrypt(encoded, passphrase)
    output_path.write_text(plaintext, encoding="utf-8")
    return output_path
