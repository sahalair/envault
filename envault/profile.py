"""Profile management for envault — named configurations that store
vault path, store path, and remote URL together."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

DEFAULT_PROFILES_PATH = Path.home() / ".envault" / "profiles.json"


class ProfileError(Exception):
    """Raised when a profile operation fails."""


def _load_profiles(profiles_path: Path = DEFAULT_PROFILES_PATH) -> dict:
    if not profiles_path.exists():
        return {}
    with profiles_path.open("r") as fh:
        return json.load(fh)


def _save_profiles(data: dict, profiles_path: Path = DEFAULT_PROFILES_PATH) -> None:
    profiles_path.parent.mkdir(parents=True, exist_ok=True)
    with profiles_path.open("w") as fh:
        json.dump(data, fh, indent=2)


def add_profile(
    name: str,
    env_file: str,
    store_dir: str,
    remote: Optional[str] = None,
    profiles_path: Path = DEFAULT_PROFILES_PATH,
) -> None:
    """Create or overwrite a named profile."""
    data = _load_profiles(profiles_path)
    data[name] = {
        "env_file": str(env_file),
        "store_dir": str(store_dir),
        "remote": remote,
    }
    _save_profiles(data, profiles_path)


def get_profile(name: str, profiles_path: Path = DEFAULT_PROFILES_PATH) -> dict:
    """Return a profile dict; raise ProfileError if not found."""
    data = _load_profiles(profiles_path)
    if name not in data:
        raise ProfileError(f"Profile '{name}' not found.")
    return data[name]


def remove_profile(name: str, profiles_path: Path = DEFAULT_PROFILES_PATH) -> None:
    """Delete a named profile; raise ProfileError if not found."""
    data = _load_profiles(profiles_path)
    if name not in data:
        raise ProfileError(f"Profile '{name}' not found.")
    del data[name]
    _save_profiles(data, profiles_path)


def list_profiles(profiles_path: Path = DEFAULT_PROFILES_PATH) -> list[str]:
    """Return sorted list of profile names."""
    return sorted(_load_profiles(profiles_path).keys())
