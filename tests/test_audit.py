"""Tests for envault.audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.audit import clear_log, read_log, record


@pytest.fixture()
def audit_file(tmp_path: Path) -> Path:
    return tmp_path / "audit.log"


def test_record_creates_file(audit_file: Path) -> None:
    record("lock", profile="dev", audit_file=audit_file)
    assert audit_file.exists()


def test_record_returns_entry(audit_file: Path) -> None:
    entry = record("unlock", profile="prod", path=".env", audit_file=audit_file)
    assert entry["action"] == "unlock"
    assert entry["profile"] == "prod"
    assert entry["path"] == ".env"
    assert entry["success"] is True


def test_record_failure_flag(audit_file: Path) -> None:
    entry = record("lock", success=False, detail="bad passphrase", audit_file=audit_file)
    assert entry["success"] is False
    assert entry["detail"] == "bad passphrase"


def test_read_log_returns_entries(audit_file: Path) -> None:
    for action in ("lock", "unlock", "push"):
        record(action, audit_file=audit_file)
    entries = read_log(audit_file=audit_file)
    assert len(entries) == 3
    assert entries[0]["action"] == "lock"
    assert entries[2]["action"] == "push"


def test_read_log_empty_when_missing(tmp_path: Path) -> None:
    entries = read_log(audit_file=tmp_path / "nonexistent.log")
    assert entries == []


def test_read_log_limit(audit_file: Path) -> None:
    for i in range(10):
        record(f"action_{i}", audit_file=audit_file)
    entries = read_log(audit_file=audit_file, limit=3)
    assert len(entries) == 3
    assert entries[-1]["action"] == "action_9"


def test_clear_log(audit_file: Path) -> None:
    record("lock", audit_file=audit_file)
    clear_log(audit_file=audit_file)
    assert read_log(audit_file=audit_file) == []


def test_record_appends_jsonl(audit_file: Path) -> None:
    record("lock", audit_file=audit_file)
    record("unlock", audit_file=audit_file)
    lines = [l for l in audit_file.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
    for line in lines:
        json.loads(line)  # must be valid JSON
