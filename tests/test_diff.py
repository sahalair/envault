"""Tests for envault.diff and envault.cli_diff."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.diff import DiffError, diff_env, has_changes
from envault.vault import lock

PASSPHRASE = "hunter2"


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=value\nFOO=bar\n", encoding="utf-8")
    return p


@pytest.fixture()
def enc_file(env_file: Path, tmp_path: Path) -> Path:
    enc = tmp_path / ".env.enc"
    lock(env_file, PASSPHRASE, output_path=enc)
    return enc


# ---------------------------------------------------------------------------
# diff_env
# ---------------------------------------------------------------------------

def test_diff_env_identical_returns_empty(env_file: Path, enc_file: Path) -> None:
    result = diff_env(env_file, enc_file, PASSPHRASE)
    assert result == ""


def test_diff_env_changed_returns_diff(env_file: Path, enc_file: Path) -> None:
    # Modify the local .env after locking
    env_file.write_text("KEY=changed\nFOO=bar\n", encoding="utf-8")
    result = diff_env(env_file, enc_file, PASSPHRASE)
    assert result != ""
    assert "-KEY=value" in result
    assert "+KEY=changed" in result


def test_diff_env_missing_env_raises(tmp_path: Path, enc_file: Path) -> None:
    missing = tmp_path / "nonexistent.env"
    with pytest.raises(DiffError, match="Plaintext file not found"):
        diff_env(missing, enc_file, PASSPHRASE)


def test_diff_env_missing_enc_raises(env_file: Path, tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.enc"
    with pytest.raises(DiffError, match="Encrypted file not found"):
        diff_env(env_file, missing, PASSPHRASE)


def test_diff_env_wrong_passphrase_raises(env_file: Path, enc_file: Path) -> None:
    with pytest.raises(DiffError, match="Failed to decrypt"):
        diff_env(env_file, enc_file, "wrong-pass")


# ---------------------------------------------------------------------------
# has_changes
# ---------------------------------------------------------------------------

def test_has_changes_false_when_identical(env_file: Path, enc_file: Path) -> None:
    assert has_changes(env_file, enc_file, PASSPHRASE) is False


def test_has_changes_true_after_edit(env_file: Path, enc_file: Path) -> None:
    env_file.write_text("KEY=new_value\n", encoding="utf-8")
    assert has_changes(env_file, enc_file, PASSPHRASE) is True


# ---------------------------------------------------------------------------
# cli_diff (cmd_diff)
# ---------------------------------------------------------------------------

def _make_ns(**kwargs) -> argparse.Namespace:
    defaults = dict(context=3, check=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_diff_no_differences_returns_0(
    env_file: Path, enc_file: Path, capsys
) -> None:
    from envault.cli_diff import cmd_diff

    ns = _make_ns(env_file=str(env_file), enc_file=str(enc_file), passphrase=PASSPHRASE)
    rc = cmd_diff(ns)
    assert rc == 0
    captured = capsys.readouterr()
    assert "No differences" in captured.out


def test_cmd_diff_with_differences_returns_1(
    env_file: Path, enc_file: Path, capsys
) -> None:
    from envault.cli_diff import cmd_diff

    env_file.write_text("KEY=changed\n", encoding="utf-8")
    ns = _make_ns(env_file=str(env_file), enc_file=str(enc_file), passphrase=PASSPHRASE)
    rc = cmd_diff(ns)
    assert rc == 1
    captured = capsys.readouterr()
    assert "KEY=changed" in captured.out


def test_cmd_diff_check_flag_no_diff_returns_0(
    env_file: Path, enc_file: Path, capsys
) -> None:
    from envault.cli_diff import cmd_diff

    ns = _make_ns(
        env_file=str(env_file), enc_file=str(enc_file), passphrase=PASSPHRASE, check=True
    )
    rc = cmd_diff(ns)
    assert rc == 0


def test_cmd_diff_check_flag_with_diff_returns_1(
    env_file: Path, enc_file: Path, capsys
) -> None:
    from envault.cli_diff import cmd_diff

    env_file.write_text("KEY=different\n", encoding="utf-8")
    ns = _make_ns(
        env_file=str(env_file), enc_file=str(enc_file), passphrase=PASSPHRASE, check=True
    )
    rc = cmd_diff(ns)
    assert rc == 1
