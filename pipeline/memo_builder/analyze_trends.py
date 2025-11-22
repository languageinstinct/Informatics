"""Analyze financial trends to support memo insights."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable


def _compute_growth(series: list[tuple[str, float]]) -> list[dict]:
    """Compute year-over-year growth for a list of (year, value)."""
    # Normalize into dict of latest value per year
    yearly = {}
    for year, value in series:
        yearly[year] = value
    growth = []
    for prev_year, year in zip(sorted(yearly), sorted(yearly)[1:]):
        prev_val = yearly[prev_year]
        curr_val = yearly[year]
        if prev_val == 0:
            pct = None
        else:
            pct = round(((curr_val - prev_val) / abs(prev_val)) * 100, 2)
        growth.append({"from": prev_year, "to": year, "growth_pct": pct})
    return growth


def analyze(financials: dict) -> dict:
    """Compute basic ratio and growth metrics from extracted financials."""
    revenue_growth = _compute_growth(financials.get("revenue", []))
    ebitda_growth = _compute_growth(financials.get("ebitda", []))

    ratios = []
    revenue_dict = defaultdict(float)
    ebitda_dict = defaultdict(float)
    for year, value in financials.get("revenue", []):
        revenue_dict[year] = value
    for year, value in financials.get("ebitda", []):
        ebitda_dict[year] = value

    for year in revenue_dict:
        rev = revenue_dict[year]
        ebitda_val = ebitda_dict.get(year)
        if ebitda_val is not None and rev:
            ratios.append({"year": year, "ebitda_margin_pct": round((ebitda_val / rev) * 100, 2)})

    return {
        "revenue_growth": revenue_growth,
        "ebitda_growth": ebitda_growth,
        "ratios": ratios,
    }
