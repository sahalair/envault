"""Import secrets from external sources into an envault-managed .env file."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


_VALID_KEY_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _parse_raw_env(text: str) -> Dict[str, str]:
    """Parse KEY=VALUE lines, skipping blanks and comments."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if '=' not in stripped:
            continue
        key, _, value = stripped.partition('=')
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if _VALID_KEY_RE.match(key):
            result[key] = value
    return result


def import_from_file(source: Path, dest: Path, overwrite: bool = False) -> List[str]:
    """Import key/value pairs from *source* .env into *dest* .env.

    Returns a list of keys that were imported (added or overwritten).
    Raises ImportError on I/O or parse problems.
    """
    if not source.exists():
        raise ImportError(f"Source file not found: {source}")

    try:
        incoming = _parse_raw_env(source.read_text())
    except OSError as exc:
        raise ImportError(f"Cannot read source file: {exc}") from exc

    existing: Dict[str, str] = {}
    if dest.exists():
        try:
            existing = _parse_raw_env(dest.read_text())
        except OSError as exc:
            raise ImportError(f"Cannot read destination file: {exc}") from exc

    imported_keys: List[str] = []
    for key, value in incoming.items():
        if key in existing and not overwrite:
            continue
        existing[key] = value
        imported_keys.append(key)

    lines = [f"{k}={v}" for k, v in existing.items()]
    try:
        dest.write_text("\n".join(lines) + "\n")
    except OSError as exc:
        raise ImportError(f"Cannot write destination file: {exc}") from exc

    return imported_keys


def import_from_environ(keys: Optional[List[str]], dest: Path, overwrite: bool = False) -> List[str]:
    """Import selected (or all) keys from the current process environment into *dest* .env.

    If *keys* is None, all environment variables are imported.
    Returns a list of keys that were imported.
    """
    source_vars: Dict[str, str]
    if keys is None:
        source_vars = dict(os.environ)
    else:
        missing = [k for k in keys if k not in os.environ]
        if missing:
            raise ImportError(f"Keys not found in environment: {', '.join(missing)}")
        source_vars = {k: os.environ[k] for k in keys}

    existing: Dict[str, str] = {}
    if dest.exists():
        try:
            existing = _parse_raw_env(dest.read_text())
        except OSError as exc:
            raise ImportError(f"Cannot read destination file: {exc}") from exc

    imported_keys: List[str] = []
    for key, value in source_vars.items():
        if not _VALID_KEY_RE.match(key):
            continue
        if key in existing and not overwrite:
            continue
        existing[key] = value
        imported_keys.append(key)

    lines = [f"{k}={v}" for k, v in existing.items()]
    try:
        dest.write_text("\n".join(lines) + "\n")
    except OSError as exc:
        raise ImportError(f"Cannot write destination file: {exc}") from exc

    return imported_keys
