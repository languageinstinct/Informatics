"""Detect reporting periods and time ranges in records."""

from __future__ import annotations

import re
from typing import Iterable

MONTHS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]


def detect_periods(text: str) -> list[str]:
    """
    Extract period markers like YYYY or YYYY-MM or month-year words from text.
    """
    periods = set()
    for year_match in re.findall(r"(20\d{2})", text):
        periods.add(year_match)
    for ym_match in re.findall(r"(20\d{2})[-_/](0[1-9]|1[0-2])", text):
        periods.add(f"{ym_match[0]}-{ym_match[1]}")
    for month in MONTHS:
        for match in re.findall(rf"{month}\s+20\d{{2}}", text, flags=re.IGNORECASE):
            periods.add(match.lower())
    return sorted(periods)


def detect_missing_months(periods: Iterable[str]) -> list[str]:
    """
    Given detected YYYY-MM strings, flag missing months in the covered year range.
    """
    ym_values = [p for p in periods if re.match(r"(20\d{2})-(0[1-9]|1[0-2])", p)]
    if not ym_values:
        return []

    years = sorted({int(p.split("-")[0]) for p in ym_values})
    months_present = {int(p.split("-")[1]) for p in ym_values}
    missing = []
    for year in years:
        for month in range(1, 13):
            if month not in months_present:
                missing.append(f"{year}-{month:02d}")
    return missing
