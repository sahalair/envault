"""Integration tests for envault.vault lock/unlock operations."""

import pytest
from pathlib import Path
from cryptography.exceptions import InvalidTag
from envault.vault import lock, unlock

PASSPHRASE = "vault-test-passphrase"
ENV_CONTENT = "API_KEY=abc123\nSECRET_TOKEN=xyz987\nDEBUG=false\n"


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(ENV_CONTENT, encoding="utf-8")
    return p


def test_lock_creates_enc_file(env_file: Path):
    enc_path = lock(env_file, PASSPHRASE)
    assert enc_path.exists()
    assert enc_path.suffix == ".enc"


def test_lock_default_output_path(env_file: Path):
    enc_path = lock(env_file, PASSPHRASE)
    assert enc_path == env_file.with_suffix(".env.enc")


def test_unlock_restores_original(env_file: Path, tmp_path: Path):
    enc_path = lock(env_file, PASSPHRASE)
    restored_path = tmp_path / ".env.restored"
    unlock(enc_path, PASSPHRASE, output_path=restored_path)
    assert restored_path.read_text(encoding="utf-8") == ENV_CONTENT


def test_lock_unlock_roundtrip_default_paths(env_file: Path):
    enc_path = lock(env_file, PASSPHRASE)
    # Remove original to prove unlock recreates it
    env_file.unlink()
    out_path = unlock(enc_path, PASSPHRASE)
    assert out_path.read_text(encoding="utf-8") == ENV_CONTENT


def test_unlock_wrong_passphrase_raises(env_file: Path):
    enc_path = lock(env_file, PASSPHRASE)
    with pytest.raises(InvalidTag):
        unlock(enc_path, "bad-passphrase")
