"""Tests for envault.rotate (key rotation)."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock
from envault.rotate import rotate, RotationError


ENV_CONTENT = "DB_URL=postgres://localhost/mydb\nSECRET_KEY=supersecret\n"
OLD_PASS = "old-passphrase"
NEW_PASS = "new-passphrase"


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    """Write a plaintext .env and return its encrypted counterpart."""
    plain = tmp_path / ".env"
    plain.write_text(ENV_CONTENT)
    enc = tmp_path / ".env.enc"
    lock(plain, OLD_PASS, output_path=enc)
    return enc


def test_rotate_produces_new_enc_file(env_file: Path) -> None:
    result = rotate(env_file, OLD_PASS, NEW_PASS)
    assert result == env_file
    assert result.exists()


def test_rotate_old_passphrase_no_longer_works(env_file: Path, tmp_path: Path) -> None:
    rotate(env_file, OLD_PASS, NEW_PASS)
    from envault.vault import unlock
    with pytest.raises(Exception):
        unlock(env_file, OLD_PASS, output_path=tmp_path / "out.env")


def test_rotate_new_passphrase_decrypts_correctly(env_file: Path, tmp_path: Path) -> None:
    rotate(env_file, OLD_PASS, NEW_PASS)
    from envault.vault import unlock
    out = tmp_path / "recovered.env"
    unlock(env_file, NEW_PASS, output_path=out)
    assert out.read_text() == ENV_CONTENT


def test_rotate_custom_output_path(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "rotated.env.enc"
    result = rotate(env_file, OLD_PASS, NEW_PASS, output_path=dest)
    assert result == dest
    assert dest.exists()
    # Original should be untouched (still encrypted with OLD_PASS)
    from envault.vault import unlock
    out = tmp_path / "orig_check.env"
    unlock(env_file, OLD_PASS, output_path=out)
    assert out.read_text() == ENV_CONTENT


def test_rotate_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(RotationError, match="not found"):
        rotate(tmp_path / "nonexistent.env.enc", OLD_PASS, NEW_PASS)


def test_rotate_wrong_old_passphrase_raises(env_file: Path) -> None:
    with pytest.raises(RotationError, match="old passphrase"):
        rotate(env_file, "wrong-pass", NEW_PASS)


def test_rotate_no_leftover_plaintext(env_file: Path) -> None:
    rotate(env_file, OLD_PASS, NEW_PASS)
    leftover = env_file.with_suffix(".rotated")
    assert not leftover.exists()


def test_rotate_keep_plaintext_flag(env_file: Path) -> None:
    rotate(env_file, OLD_PASS, NEW_PASS, keep_plaintext=True)
    leftover = env_file.with_suffix(".rotated")
    assert leftover.exists()
    assert leftover.read_text() == ENV_CONTENT
