"""Tests for envault.search."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock
from envault.search import search, SearchError


PASSPHRASE = "hunter2"

ENV_CONTENT = """\
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=s3cr3t
API_KEY=abcdef123
DEBUG=true
# a comment

EMPTY_VAL=
"""


@pytest.fixture()
def enc_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    out = tmp_path / ".env.enc"
    lock(env, PASSPHRASE, output=out)
    return out


def test_search_key_glob_match(enc_file: Path) -> None:
    result = search(enc_file, PASSPHRASE, "DB_*")
    assert result.found
    keys = {m.key for m in result.matches}
    assert keys == {"DB_HOST", "DB_PORT", "DB_PASSWORD"}


def test_search_exact_key(enc_file: Path) -> None:
    result = search(enc_file, PASSPHRASE, "API_KEY")
    assert result.found
    assert len(result.matches) == 1
    assert result.matches[0].key == "API_KEY"


def test_search_no_match_returns_empty(enc_file: Path) -> None:
    result = search(enc_file, PASSPHRASE, "NONEXISTENT_*")
    assert not result.found
    assert result.matches == []


def test_search_case_insensitive_by_default(enc_file: Path) -> None:
    result = search(enc_file, PASSPHRASE, "db_*")
    assert result.found
    assert len(result.matches) == 3


def test_search_case_sensitive_no_match(enc_file: Path) -> None:
    result = search(enc_file, PASSPHRASE, "db_*", case_sensitive=True)
    assert not result.found


def test_search_values_flag(enc_file: Path) -> None:
    result = search(enc_file, PASSPHRASE, "*s3cr3t*", search_values=True)
    assert result.found
    assert result.matches[0].key == "DB_PASSWORD"


def test_search_values_not_searched_by_default(enc_file: Path) -> None:
    result = search(enc_file, PASSPHRASE, "*s3cr3t*")
    assert not result.found


def test_search_regex_mode(enc_file: Path) -> None:
    result = search(enc_file, PASSPHRASE, r"^DB_", use_regex=True)
    assert result.found
    assert len(result.matches) == 3


def test_search_regex_value_match(enc_file: Path) -> None:
    result = search(enc_file, PASSPHRASE, r"\d+", search_values=True, use_regex=True)
    assert result.found
    keys = {m.key for m in result.matches}
    assert "DB_PORT" in keys


def test_search_wrong_passphrase_raises(enc_file: Path) -> None:
    with pytest.raises(SearchError, match="Could not decrypt"):
        search(enc_file, "wrongpass", "*")


def test_search_result_has_correct_enc_file(enc_file: Path) -> None:
    result = search(enc_file, PASSPHRASE, "DEBUG")
    assert result.enc_file == enc_file


def test_search_empty_value_key(enc_file: Path) -> None:
    result = search(enc_file, PASSPHRASE, "EMPTY_VAL")
    assert result.found
    assert result.matches[0].value == ""
