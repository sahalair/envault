"""Search for keys across decrypted vault contents."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import unlock


class SearchError(Exception):
    """Raised when a search operation fails."""


@dataclass
class SearchMatch:
    key: str
    value: str
    line_number: int


@dataclass
class SearchResult:
    enc_file: Path
    matches: List[SearchMatch] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return len(self.matches) > 0


def _parse_env_lines(lines: List[str]) -> List[tuple[int, str, str]]:
    """Return (line_number, key, value) tuples for valid KEY=VALUE lines."""
    results = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        results.append((i, key.strip(), value.strip()))
    return results


def search(
    enc_file: Path,
    passphrase: str,
    pattern: str,
    *,
    search_values: bool = False,
    case_sensitive: bool = False,
    use_regex: bool = False,
) -> SearchResult:
    """Search an encrypted .env file for keys (and optionally values) matching *pattern*.

    Args:
        enc_file: Path to the encrypted ``.env.enc`` file.
        passphrase: Passphrase used to decrypt the file.
        pattern: Glob pattern (or regex when *use_regex* is True) to match against.
        search_values: When True, also match against values.
        case_sensitive: Honour case when matching.
        use_regex: Treat *pattern* as a regular expression instead of a glob.

    Returns:
        A :class:`SearchResult` with all matching entries.

    Raises:
        SearchError: If decryption fails or the file cannot be read.
    """
    try:
        plaintext = unlock(enc_file, passphrase)
    except Exception as exc:  # noqa: BLE001
        raise SearchError(f"Could not decrypt {enc_file}: {exc}") from exc

    flags = 0 if case_sensitive else re.IGNORECASE
    lines = plaintext.splitlines()
    entries = _parse_env_lines(lines)

    result = SearchResult(enc_file=enc_file)
    for lineno, key, value in entries:
        candidates = [key] + ([value] if search_values else [])
        matched = False
        for candidate in candidates:
            if use_regex:
                if re.search(pattern, candidate, flags):
                    matched = True
                    break
            else:
                norm_candidate = candidate if case_sensitive else candidate.lower()
                norm_pattern = pattern if case_sensitive else pattern.lower()
                if fnmatch.fnmatch(norm_candidate, norm_pattern):
                    matched = True
                    break
        if matched:
            result.matches.append(SearchMatch(key=key, value=value, line_number=lineno))

    return result
