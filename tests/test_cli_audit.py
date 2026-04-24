"""Tests for envault.cli_audit."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault import audit as audit_module
from envault.cli_audit import cmd_audit_clear, cmd_audit_log, register_audit_subparser


@pytest.fixture(autouse=True)
def isolated_audit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    log = tmp_path / "audit.log"
    monkeypatch.setattr(audit_module, "DEFAULT_AUDIT_FILE", log)
    yield log


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"limit": 50, "yes": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_audit_log_empty(capsys):
    rc = cmd_audit_log(_ns())
    assert rc == 0
    assert "No audit entries found" in capsys.readouterr().out


def test_cmd_audit_log_shows_entries(capsys):
    audit_module.record("lock", profile="dev", success=True)
    audit_module.record("unlock", profile="prod", success=False, detail="wrong pass")
    rc = cmd_audit_log(_ns(limit=10))
    assert rc == 0
    out = capsys.readouterr().out
    assert "lock" in out
    assert "[dev]" in out
    assert "FAIL" in out
    assert "wrong pass" in out


def test_cmd_audit_clear_with_yes_flag(capsys):
    audit_module.record("push")
    rc = cmd_audit_clear(_ns(yes=True))
    assert rc == 0
    assert audit_module.read_log() == []
    assert "cleared" in capsys.readouterr().out.lower()


def test_cmd_audit_clear_aborted(capsys):
    audit_module.record("push")
    with patch("builtins.input", return_value="n"):
        rc = cmd_audit_clear(_ns(yes=False))
    assert rc == 1
    assert len(audit_module.read_log()) == 1


def test_register_audit_subparser():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd")
    register_audit_subparser(subs)
    args = parser.parse_args(["audit", "log", "-n", "5"])
    assert args.limit == 5
    assert args.func is not None
