"""Tests for envault.export and envault.cli_export."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from envault.vault import lock
from envault.export import ExportError, _parse_env_lines, export_to_env, export_to_shell_script

PASSPHRASE = "test-export-passphrase"


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text('FOO=bar\nBAZ="hello world"\n# comment\nEMPTY=\n', encoding="utf-8")
    return p


@pytest.fixture()
def enc_file(env_file: Path) -> Path:
    out = env_file.with_suffix(".env.enc")
    lock(env_file, PASSPHRASE, output_path=out)
    return out


# ---------------------------------------------------------------------------
# _parse_env_lines
# ---------------------------------------------------------------------------

def test_parse_env_lines_basic():
    text = 'KEY=value\n# skip me\nOTHER="quoted"\n'
    result = _parse_env_lines(text)
    assert result == {"KEY": "value", "OTHER": "quoted"}


def test_parse_env_lines_ignores_blank_and_comments():
    text = "\n# full comment\n   \nA=1\n"
    result = _parse_env_lines(text)
    assert result == {"A": "1"}


def test_parse_env_lines_empty_value():
    result = _parse_env_lines("EMPTY=\n")
    assert result == {"EMPTY": ""}


# ---------------------------------------------------------------------------
# export_to_env
# ---------------------------------------------------------------------------

def test_export_to_env_injects_variables(enc_file: Path, monkeypatch):
    monkeypatch.delenv("FOO", raising=False)
    monkeypatch.delenv("BAZ", raising=False)
    monkeypatch.delenv("EMPTY", raising=False)

    variables = export_to_env(enc_file, PASSPHRASE, overwrite=True)

    assert "FOO" in variables
    assert os.environ["FOO"] == "bar"
    assert os.environ["BAZ"] == "hello world"


def test_export_to_env_conflict_raises(enc_file: Path, monkeypatch):
    monkeypatch.setenv("FOO", "already_set")
    with pytest.raises(ExportError, match="FOO"):
        export_to_env(enc_file, PASSPHRASE, overwrite=False)


def test_export_to_env_overwrite_replaces(enc_file: Path, monkeypatch):
    monkeypatch.setenv("FOO", "old")
    export_to_env(enc_file, PASSPHRASE, overwrite=True)
    assert os.environ["FOO"] == "bar"


def test_export_to_env_wrong_passphrase_raises(enc_file: Path, monkeypatch):
    monkeypatch.delenv("FOO", raising=False)
    with pytest.raises(Exception):
        export_to_env(enc_file, "wrong-passphrase")


# ---------------------------------------------------------------------------
# export_to_shell_script
# ---------------------------------------------------------------------------

def test_export_to_shell_script_creates_file(enc_file: Path, tmp_path: Path):
    script = tmp_path / "env_export.sh"
    result = export_to_shell_script(enc_file, PASSPHRASE, output_path=script)
    assert result == script
    assert script.exists()


def test_export_to_shell_script_contains_exports(enc_file: Path, tmp_path: Path):
    script = tmp_path / "env_export.sh"
    export_to_shell_script(enc_file, PASSPHRASE, output_path=script)
    content = script.read_text()
    assert 'export FOO="bar"' in content
    assert 'export BAZ="hello world"' in content


def test_export_to_shell_script_default_path(enc_file: Path):
    result = export_to_shell_script(enc_file, PASSPHRASE)
    expected = enc_file.with_suffix(".export.sh")
    assert result == expected
    assert result.exists()
    result.unlink()


def test_export_to_shell_script_has_shebang(enc_file: Path, tmp_path: Path):
    script = tmp_path / "env_export.sh"
    export_to_shell_script(enc_file, PASSPHRASE, output_path=script)
    first_line = script.read_text().splitlines()[0]
    assert first_line == "#!/usr/bin/env sh"
