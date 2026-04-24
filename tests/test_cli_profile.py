"""Integration tests for the profile CLI sub-commands."""

from __future__ import annotations

import argparse
import pytest
from pathlib import Path
from unittest.mock import patch

from envault.cli_profile import (
    cmd_profile_add,
    cmd_profile_show,
    cmd_profile_remove,
    cmd_profile_list,
)
from envault import profile as profile_mod


@pytest.fixture(autouse=True)
def isolated_profiles(tmp_path, monkeypatch):
    """Redirect all profile I/O to a temp file for every test."""
    fake_path = tmp_path / "profiles.json"
    monkeypatch.setattr(profile_mod, "DEFAULT_PROFILES_PATH", fake_path)
    return fake_path


def _ns(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_cmd_profile_add_prints_confirmation(capsys):
    args = _ns(name="dev", env_file=".env", store_dir="/s", remote=None)
    rc = cmd_profile_add(args)
    assert rc == 0
    assert "dev" in capsys.readouterr().out


def test_cmd_profile_show_prints_fields(capsys):
    add_args = _ns(name="dev", env_file=".env", store_dir="/s", remote="git@gh:a/b")
    cmd_profile_add(add_args)
    rc = cmd_profile_show(_ns(name="dev"))
    assert rc == 0
    out = capsys.readouterr().out
    assert ".env" in out
    assert "/s" in out
    assert "git@gh:a/b" in out


def test_cmd_profile_show_missing_returns_1(capsys):
    rc = cmd_profile_show(_ns(name="ghost"))
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_cmd_profile_remove_success(capsys):
    cmd_profile_add(_ns(name="tmp", env_file=".env", store_dir="/s", remote=None))
    rc = cmd_profile_remove(_ns(name="tmp"))
    assert rc == 0
    assert "removed" in capsys.readouterr().out


def test_cmd_profile_remove_missing_returns_1(capsys):
    rc = cmd_profile_remove(_ns(name="ghost"))
    assert rc == 1


def test_cmd_profile_list_empty(capsys):
    rc = cmd_profile_list(_ns())
    assert rc == 0
    assert "No profiles" in capsys.readouterr().out


def test_cmd_profile_list_shows_names(capsys):
    for name in ["prod", "dev"]:
        cmd_profile_add(_ns(name=name, env_file=".env", store_dir="/s", remote=None))
    rc = cmd_profile_list(_ns())
    assert rc == 0
    out = capsys.readouterr().out
    assert "dev" in out
    assert "prod" in out
