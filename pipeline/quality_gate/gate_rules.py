"""Quality gate rules for incoming ZIP packages."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Iterable

# Expected document archetypes for financial packages.
REQUIRED_DOC_TYPES = {
    "income_statement": [r"income[_\\s]?statement", r"p&l", r"profit[_\\s]?and[_\\s]?loss"],
    "balance_sheet": [r"balance[_\\s]?sheet"],
    "cash_flow": [r"cash[_\\s]?flow", r"cashflow"],
}


def find_missing_required(file_names: Iterable[str]) -> list[str]:
    """Return required document types that are not present in file names."""
    lowered = [name.lower() for name in file_names]
    missing: list[str] = []
    for doc_type, patterns in REQUIRED_DOC_TYPES.items():
        if not any(re.search(pattern, name) for name in lowered for pattern in patterns):
            missing.append(doc_type)
    return missing


def detect_folder_structure(file_names: Iterable[str]) -> list[str]:
    """
    Identify odd folder structures (deep nesting or multiple top-level folders).
    Returns list of human-readable issues.
    """
    depths = [len(Path(name).parts) for name in file_names]
    issues: list[str] = []
    if any(depth > 3 for depth in depths):
        issues.append("Files nested more than 2 levels deep")

    top_levels = [Path(name).parts[0] for name in file_names if len(Path(name).parts) > 1]
    top_level_counts = Counter(top_levels)
    if len(top_level_counts) > 3:
        issues.append("Multiple top-level folders detected")
    return issues


def detect_inconsistent_naming(file_names: Iterable[str]) -> list[str]:
    """Flag names with whitespace, unusual characters, or duplicates ignoring case."""
    issues: list[str] = []
    lowered = [name.lower() for name in file_names]
    duplicates = [name for name, count in Counter(lowered).items() if count > 1]
    if duplicates:
        issues.append(f"Duplicate names: {', '.join(duplicates)}")

    bad_chars = [name for name in file_names if re.search(r"[^a-zA-Z0-9_./\\-]", name)]
    if bad_chars:
        issues.append("Non-alphanumeric characters in file names")
    return issues
