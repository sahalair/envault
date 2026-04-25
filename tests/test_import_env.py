"""Tests for envault.import_env."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from envault.import_env import ImportError as EnvImportError
from envault.import_env import _parse_raw_env, import_from_environ, import_from_file


# ---------------------------------------------------------------------------
# _parse_raw_env
# ---------------------------------------------------------------------------

def test_parse_raw_env_basic():
    text = "FOO=bar\nBAZ=qux\n"
    assert _parse_raw_env(text) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_raw_env_ignores_comments_and_blanks():
    text = "# comment\n\nFOO=bar\n"
    assert _parse_raw_env(text) == {"FOO": "bar"}


def test_parse_raw_env_strips_quotes():
    text = 'KEY="hello world"\nKEY2=\'value\'\n'
    result = _parse_raw_env(text)
    assert result["KEY"] == "hello world"
    assert result["KEY2"] == "value"


def test_parse_raw_env_empty_value():
    assert _parse_raw_env("EMPTY=\n") == {"EMPTY": ""}


# ---------------------------------------------------------------------------
# import_from_file
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_env(tmp_path: Path):
    return tmp_path


def test_import_from_file_basic(tmp_env: Path):
    source = tmp_env / "source.env"
    dest = tmp_env / ".env"
    source.write_text("FOO=bar\nBAZ=qux\n")
    keys = import_from_file(source, dest)
    assert set(keys) == {"FOO", "BAZ"}
    content = dest.read_text()
    assert "FOO=bar" in content
    assert "BAZ=qux" in content


def test_import_from_file_no_overwrite_by_default(tmp_env: Path):
    source = tmp_env / "source.env"
    dest = tmp_env / ".env"
    dest.write_text("FOO=original\n")
    source.write_text("FOO=new\nBAR=added\n")
    keys = import_from_file(source, dest)
    assert keys == ["BAR"]
    assert "FOO=original" in dest.read_text()


def test_import_from_file_overwrite(tmp_env: Path):
    source = tmp_env / "source.env"
    dest = tmp_env / ".env"
    dest.write_text("FOO=original\n")
    source.write_text("FOO=new\n")
    keys = import_from_file(source, dest, overwrite=True)
    assert "FOO" in keys
    assert "FOO=new" in dest.read_text()


def test_import_from_file_missing_source_raises(tmp_env: Path):
    with pytest.raises(EnvImportError, match="Source file not found"):
        import_from_file(tmp_env / "nonexistent.env", tmp_env / ".env")


# ---------------------------------------------------------------------------
# import_from_environ
# ---------------------------------------------------------------------------

def test_import_from_environ_specific_keys(tmp_env: Path, monkeypatch):
    monkeypatch.setenv("MY_SECRET", "s3cr3t")
    dest = tmp_env / ".env"
    keys = import_from_environ(["MY_SECRET"], dest)
    assert "MY_SECRET" in keys
    assert "MY_SECRET=s3cr3t" in dest.read_text()


def test_import_from_environ_missing_key_raises(tmp_env: Path):
    with pytest.raises(EnvImportError, match="Keys not found in environment"):
        import_from_environ(["__DEFINITELY_NOT_SET_XYZ__"], tmp_env / ".env")


def test_import_from_environ_no_overwrite(tmp_env: Path, monkeypatch):
    monkeypatch.setenv("EXISTING", "new_value")
    dest = tmp_env / ".env"
    dest.write_text("EXISTING=old_value\n")
    keys = import_from_environ(["EXISTING"], dest, overwrite=False)
    assert keys == []
    assert "EXISTING=old_value" in dest.read_text()
