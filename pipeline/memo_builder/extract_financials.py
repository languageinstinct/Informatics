"""Extract financial metrics from classified records."""

from __future__ import annotations

import re
from typing import Iterable


def _extract_metric(text: str, keyword: str) -> list[tuple[str, float]]:
    """Find keyword followed by a number and optional year."""
    pattern = rf"{keyword}[^\\d]*(20\\d{{2}})?[^\\d]*(-?\\d[\\d,\\.]+)"
    results: list[tuple[str, float]] = []
    for match in re.findall(pattern, text, flags=re.IGNORECASE):
        year = match[0] or "unknown"
        value_str = match[1].replace(",", "")
        try:
            value = float(value_str)
            results.append((year, value))
        except ValueError:
            continue
    return results


def extract(financial_texts: Iterable[str]) -> dict:
    """
    Extract simple financial metrics (revenue, ebitda, net income) from text blobs.
    """
    revenue = []
    ebitda = []
    net_income = []
    for text in financial_texts:
        revenue.extend(_extract_metric(text, "revenue"))
        ebitda.extend(_extract_metric(text, "ebitda"))
        net_income.extend(_extract_metric(text, "net income|net\\s+profit"))

    return {
        "revenue": revenue,
        "ebitda": ebitda,
        "net_income": net_income,
    }
