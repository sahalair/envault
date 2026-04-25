"""Tests for envault.cli_import CLI subcommands."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.cli_import import cmd_import_env, cmd_import_file, register_import_subparser


@pytest.fixture()
def isolated(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"overwrite": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# cmd_import_file
# ---------------------------------------------------------------------------

def test_cmd_import_file_prints_imported_keys(isolated: Path, capsys):
    source = isolated / "other.env"
    dest = isolated / ".env"
    source.write_text("API_KEY=abc\nDB_PASS=secret\n")
    ns = _ns(source=str(source), dest=str(dest))
    rc = cmd_import_file(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "DB_PASS" in out


def test_cmd_import_file_no_new_keys_message(isolated: Path, capsys):
    source = isolated / "other.env"
    dest = isolated / ".env"
    source.write_text("FOO=bar\n")
    dest.write_text("FOO=bar\n")
    ns = _ns(source=str(source), dest=str(dest))
    rc = cmd_import_file(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No new keys" in out


def test_cmd_import_file_missing_source_returns_1(isolated: Path, capsys):
    ns = _ns(source=str(isolated / "nope.env"), dest=str(isolated / ".env"))
    rc = cmd_import_file(ns)
    assert rc == 1
    assert "error" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# cmd_import_env
# ---------------------------------------------------------------------------

def test_cmd_import_env_imports_from_environment(isolated: Path, capsys, monkeypatch):
    monkeypatch.setenv("TEST_TOKEN", "tok123")
    dest = isolated / ".env"
    ns = _ns(dest=str(dest), keys=["TEST_TOKEN"])
    rc = cmd_import_env(ns)
    assert rc == 0
    assert "TEST_TOKEN" in dest.read_text()
    assert "TEST_TOKEN" in capsys.readouterr().out


def test_cmd_import_env_missing_key_returns_1(isolated: Path, capsys):
    dest = isolated / ".env"
    ns = _ns(dest=str(dest), keys=["__NO_SUCH_VAR_XYZ__"])
    rc = cmd_import_env(ns)
    assert rc == 1
    assert "error" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# register_import_subparser
# ---------------------------------------------------------------------------

def test_register_import_subparser_registers_commands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    register_import_subparser(sub)
    args = parser.parse_args(["import", "file", "src.env"])
    assert args.source == "src.env"
    assert args.dest == ".env"
