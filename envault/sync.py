"""High-level sync operations: push and pull encrypted vault files."""

from pathlib import Path

from envault.git_store import (
    GitStoreError,
    add_remote,
    commit_file,
    copy_to_store,
    init_store,
    pull,
    push,
)

_DEFAULT_STORE = Path.home() / ".envault" / "store"


def sync_push(
    enc_file: Path,
    remote_url: str,
    store_path: Path = _DEFAULT_STORE,
    branch: str = "main",
    message: str | None = None,
) -> None:
    """Push *enc_file* to the git-backed store and sync to *remote_url*.

    Initialises the local store if it does not yet exist.
    """
    init_store(store_path)
    add_remote(store_path, remote_url)
    dest = copy_to_store(enc_file, store_path)
    commit_msg = message or f"vault: update {enc_file.name}"
    commit_file(store_path, dest, commit_msg)
    push(store_path, branch=branch)


def sync_pull(
    enc_filename: str,
    remote_url: str,
    dest_dir: Path = Path("."),
    store_path: Path = _DEFAULT_STORE,
    branch: str = "main",
) -> Path:
    """Pull the latest *enc_filename* from *remote_url* into *dest_dir*.

    Returns the local path of the pulled file.
    """
    init_store(store_path)
    add_remote(store_path, remote_url)
    pull(store_path, branch=branch)
    src = store_path / enc_filename
    if not src.exists():
        raise GitStoreError(
            f"{enc_filename!r} not found in store after pull."
        )
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / enc_filename
    import shutil
    shutil.copy2(src, dest)
    return dest
