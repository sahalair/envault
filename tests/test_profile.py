"""Tests for envault.profile."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.profile import (
    add_profile,
    get_profile,
    remove_profile,
    list_profiles,
    ProfileError,
)


@pytest.fixture()
def profiles_file(tmp_path: Path) -> Path:
    return tmp_path / "profiles.json"


def test_add_and_get_profile(profiles_file):
    add_profile("dev", ".env", "/store/dev", remote="git@gh:x/r", profiles_path=profiles_file)
    profile = get_profile("dev", profiles_path=profiles_file)
    assert profile["env_file"] == ".env"
    assert profile["store_dir"] == "/store/dev"
    assert profile["remote"] == "git@gh:x/r"


def test_add_profile_no_remote(profiles_file):
    add_profile("local", ".env", "/store/local", profiles_path=profiles_file)
    profile = get_profile("local", profiles_path=profiles_file)
    assert profile["remote"] is None


def test_add_profile_overwrites_existing(profiles_file):
    add_profile("dev", ".env", "/store/v1", profiles_path=profiles_file)
    add_profile("dev", ".env", "/store/v2", profiles_path=profiles_file)
    profile = get_profile("dev", profiles_path=profiles_file)
    assert profile["store_dir"] == "/store/v2"


def test_get_profile_missing_raises(profiles_file):
    with pytest.raises(ProfileError, match="not found"):
        get_profile("ghost", profiles_path=profiles_file)


def test_remove_profile(profiles_file):
    add_profile("staging", ".env", "/store/s", profiles_path=profiles_file)
    remove_profile("staging", profiles_path=profiles_file)
    with pytest.raises(ProfileError):
        get_profile("staging", profiles_path=profiles_file)


def test_remove_profile_missing_raises(profiles_file):
    with pytest.raises(ProfileError, match="not found"):
        remove_profile("ghost", profiles_path=profiles_file)


def test_list_profiles_empty(profiles_file):
    assert list_profiles(profiles_path=profiles_file) == []


def test_list_profiles_sorted(profiles_file):
    for name in ["prod", "dev", "staging"]:
        add_profile(name, ".env", f"/store/{name}", profiles_path=profiles_file)
    assert list_profiles(profiles_path=profiles_file) == ["dev", "prod", "staging"]


def test_profiles_persisted_as_json(profiles_file):
    add_profile("ci", ".env.ci", "/store/ci", profiles_path=profiles_file)
    raw = json.loads(profiles_file.read_text())
    assert "ci" in raw
    assert raw["ci"]["env_file"] == ".env.ci"
