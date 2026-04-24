"""Tests for envault.git_store."""

import subprocess
from pathlib import Path

import pytest

from envault.git_store import (
    GitStoreError,
    add_remote,
    commit_file,
    copy_to_store,
    init_store,
)


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    p = tmp_path / "store"
    init_store(p)
    return p


def test_init_store_creates_git_repo(tmp_path: Path) -> None:
    p = tmp_path / "mystore"
    init_store(p)
    assert (p / ".git").is_dir()


def test_init_store_is_idempotent(tmp_path: Path) -> None:
    p = tmp_path / "mystore"
    init_store(p)
    init_store(p)  # should not raise
    assert (p / ".git").is_dir()


def test_copy_to_store(store: Path, tmp_path: Path) -> None:
    src = tmp_path / "secrets.env.enc"
    src.write_text("encrypted-data")
    dest = copy_to_store(src, store)
    assert dest == store / "secrets.env.enc"
    assert dest.read_text() == "encrypted-data"


def test_commit_file(store: Path, tmp_path: Path) -> None:
    src = tmp_path / "vault.env.enc"
    src.write_text("ciphertext")
    dest = copy_to_store(src, store)
    commit_file(store, dest, "test: add vault file")
    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=store,
        capture_output=True,
        text=True,
    )
    assert "test: add vault file" in log.stdout


def test_add_remote_and_update(store: Path) -> None:
    add_remote(store, "https://example.com/repo.git")
    # Calling again with a different URL should update, not raise
    add_remote(store, "https://example.com/other.git")


def test_run_raises_git_store_error_on_bad_command(store: Path) -> None:
    from envault.git_store import _run
    with pytest.raises(GitStoreError):
        _run(["git", "nonexistent-command-xyz"], cwd=store)
