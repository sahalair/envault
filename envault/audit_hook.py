"""Convenience wrappers that record audit entries around vault and sync operations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault import audit
from envault.vault import lock, unlock
from envault.sync import sync_push, sync_pull


def audited_lock(
    env_path: Path,
    passphrase: str,
    output_path: Optional[Path] = None,
    profile: Optional[str] = None,
) -> Path:
    """Call vault.lock and record the outcome."""
    try:
        result = lock(env_path, passphrase, output_path)
        audit.record("lock", profile=profile, path=str(result), success=True)
        return result
    except Exception as exc:
        audit.record("lock", profile=profile, path=str(env_path), success=False, detail=str(exc))
        raise


def audited_unlock(
    enc_path: Path,
    passphrase: str,
    output_path: Optional[Path] = None,
    profile: Optional[str] = None,
) -> Path:
    """Call vault.unlock and record the outcome."""
    try:
        result = unlock(enc_path, passphrase, output_path)
        audit.record("unlock", profile=profile, path=str(result), success=True)
        return result
    except Exception as exc:
        audit.record("unlock", profile=profile, path=str(enc_path), success=False, detail=str(exc))
        raise


def audited_push(
    store_dir: Path,
    enc_file: Path,
    profile: Optional[str] = None,
) -> None:
    """Call sync.sync_push and record the outcome."""
    try:
        sync_push(store_dir, enc_file)
        audit.record("push", profile=profile, path=str(enc_file), success=True)
    except Exception as exc:
        audit.record("push", profile=profile, path=str(enc_file), success=False, detail=str(exc))
        raise


def audited_pull(
    store_dir: Path,
    filename: str,
    dest: Path,
    profile: Optional[str] = None,
) -> None:
    """Call sync.sync_pull and record the outcome."""
    try:
        sync_pull(store_dir, filename, dest)
        audit.record("pull", profile=profile, path=str(dest), success=True)
    except Exception as exc:
        audit.record("pull", profile=profile, path=str(dest), success=False, detail=str(exc))
        raise
