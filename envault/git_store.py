"""Git-backed store for syncing encrypted vault files."""

import subprocess
import shutil
from pathlib import Path


class GitStoreError(Exception):
    """Raised when a git operation fails."""


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a git command, raising GitStoreError on failure."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitStoreError(
            f"Command {' '.join(cmd)} failed:\n{result.stderr.strip()}"
        )
    return result


def init_store(store_path: Path) -> None:
    """Initialise a new git repository at *store_path*."""
    store_path.mkdir(parents=True, exist_ok=True)
    if not (store_path / ".git").exists():
        _run(["git", "init"], cwd=store_path)


def add_remote(store_path: Path, remote_url: str, name: str = "origin") -> None:
    """Add or update a remote in the store repository."""
    result = subprocess.run(
        ["git", "remote", "get-url", name],
        cwd=store_path,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        _run(["git", "remote", "set-url", name, remote_url], cwd=store_path)
    else:
        _run(["git", "remote", "add", name, remote_url], cwd=store_path)


def commit_file(store_path: Path, file_path: Path, message: str) -> None:
    """Stage *file_path* and create a commit in the store."""
    _run(["git", "add", str(file_path)], cwd=store_path)
    _run(["git", "commit", "-m", message, "--allow-empty"], cwd=store_path)


def push(store_path: Path, remote: str = "origin", branch: str = "main") -> None:
    """Push the store to *remote*."""
    _run(["git", "push", remote, branch], cwd=store_path)


def pull(store_path: Path, remote: str = "origin", branch: str = "main") -> None:
    """Pull latest changes from *remote* into the store."""
    _run(["git", "pull", remote, branch], cwd=store_path)


def copy_to_store(src: Path, store_path: Path) -> Path:
    """Copy *src* into *store_path* and return the destination path."""
    store_path.mkdir(parents=True, exist_ok=True)
    dest = store_path / src.name
    shutil.copy2(src, dest)
    return dest
