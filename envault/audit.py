"""Audit log: records vault operations to a local JSONL file."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_AUDIT_FILE = Path.home() / ".envault" / "audit.log"


def _audit_path(audit_file: Optional[Path] = None) -> Path:
    return Path(audit_file) if audit_file else DEFAULT_AUDIT_FILE


def record(
    action: str,
    profile: Optional[str] = None,
    path: Optional[str] = None,
    success: bool = True,
    detail: Optional[str] = None,
    audit_file: Optional[Path] = None,
) -> dict:
    """Append a structured audit entry and return it."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "profile": profile,
        "path": str(path) if path else None,
        "success": success,
        "detail": detail,
        "user": os.environ.get("USER") or os.environ.get("USERNAME"),
    }
    log_path = _audit_path(audit_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def read_log(audit_file: Optional[Path] = None, limit: int = 100) -> list[dict]:
    """Return the last *limit* audit entries (oldest first)."""
    log_path = _audit_path(audit_file)
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").splitlines()
    entries = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries[-limit:]


def clear_log(audit_file: Optional[Path] = None) -> None:
    """Erase the audit log."""
    log_path = _audit_path(audit_file)
    if log_path.exists():
        log_path.write_text("", encoding="utf-8")
