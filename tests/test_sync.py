"""Tests for envault.sync (push/pull using a local bare repo as remote)."""

import subprocess
from pathlib import Path

import pytest

from envault.sync import sync_pull, sync_push


@pytest.fixture()
def bare_remote(tmp_path: Path) -> Path:
    """Create a local bare git repo to act as a remote."""
    remote = tmp_path / "remote.git"
    remote.mkdir()
    subprocess.run(["git", "init", "--bare", str(remote)], check=True)
    return remote


@pytest.fixture()
def enc_file(tmp_path: Path) -> Path:
    f = tmp_path / "project.env.enc"
    f.write_text("fake-encrypted-content")
    return f


def test_sync_push_creates_commit_and_pushes(
    tmp_path: Path, bare_remote: Path, enc_file: Path
) -> None:
    store = tmp_path / "store"
    sync_push(
        enc_file,
        remote_url=str(bare_remote),
        store_path=store,
        branch="main",
    )
    # Verify the file reached the bare remote by cloning it
    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", str(bare_remote), str(clone)], check=True
    )
    assert (clone / enc_file.name).read_text() == "fake-encrypted-content"


def test_sync_pull_retrieves_file(
    tmp_path: Path, bare_remote: Path, enc_file: Path
) -> None:
    store_push = tmp_path / "store_push"
    sync_push(
        enc_file,
        remote_url=str(bare_remote),
        store_path=store_push,
        branch="main",
    )

    dest_dir = tmp_path / "dest"
    store_pull = tmp_path / "store_pull"
    pulled = sync_pull(
        enc_file.name,
        remote_url=str(bare_remote),
        dest_dir=dest_dir,
        store_path=store_pull,
        branch="main",
    )
    assert pulled == dest_dir / enc_file.name
    assert pulled.read_text() == "fake-encrypted-content"


def test_sync_pull_missing_file_raises(
    tmp_path: Path, bare_remote: Path, enc_file: Path
) -> None:
    store_push = tmp_path / "store_push"
    sync_push(
        enc_file,
        remote_url=str(bare_remote),
        store_path=store_push,
        branch="main",
    )
    from envault.git_store import GitStoreError
    with pytest.raises(GitStoreError, match="not found in store"):
        sync_pull(
            "nonexistent.env.enc",
            remote_url=str(bare_remote),
            dest_dir=tmp_path / "dest",
            store_path=tmp_path / "store_pull",
            branch="main",
        )
