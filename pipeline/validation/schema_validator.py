"""Validate records against a predefined schema."""

from __future__ import annotations

import re
from pathlib import Path

from pipeline.utils.file_utils import save_json
from pipeline.validation.period_detector import detect_missing_months, detect_periods


def _extract_numbers(text: str) -> list[float]:
    """Extract numeric values from text to approximate tables."""
    numbers: list[float] = []
    for match in re.findall(r"-?\d{1,3}(?:,\d{3})*(?:\.\d+)?", text):
        try:
            normalized = match.replace(",", "")
            numbers.append(float(normalized))
        except ValueError:
            continue
    return numbers


def _detect_dates(text: str) -> bool:
    """Detect presence of date-like patterns."""
    if re.search(r"20\d{2}[-/](0[1-9]|1[0-2])", text):
        return True
    if re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+20\d{2}", text, flags=re.IGNORECASE):
        return True
    return False


def validate_documents(pdf_texts: dict[str, str], classification: dict | None = None, output_path: str | None = None) -> dict:
    """
    Perform validation across classified documents.

    Checks:
      - numeric content presence
      - period coverage and continuity
      - missing months in detected ranges
      - per-document completeness flags from classification structured output
    """
    details = []
    all_periods: list[str] = []
    missing_months_global: list[str] = []

    # Map classification by path for flag reuse
    classification_map = {}
    if classification:
        for doc in classification.get("documents", []):
            classification_map[str(doc.get("path"))] = doc.get("structured", {})

    for path, text in pdf_texts.items():
        periods = detect_periods(text)
        all_periods.extend(periods)
        numbers = _extract_numbers(text)
        missing_months = detect_missing_months(periods)
        missing_months_global.extend(missing_months)

        has_dates = _detect_dates(text)
        alpha_chars = len(re.findall(r"[A-Za-z]", text))
        numeric_count = len(numbers)
        sparse_text = alpha_chars < 20 and numeric_count < 5

        classification_flags = classification_map.get(path, {})
        flags = classification_flags.get("flags", {}) if isinstance(classification_flags, dict) else {}

        missing_fields = flags.get("missing_fields", []) if flags else []
        suspicious_values = flags.get("suspicious_values", []) if flags else []
        format_errors = flags.get("format_errors", []) if flags else []

        if not has_dates:
            format_errors.append("missing dates")
        if sparse_text:
            format_errors.append("sparse content")

        detail = {
            "path": path,
            "periods": periods,
            "numeric_values_found": numeric_count,
            "missing_months": missing_months,
            "passes_numeric_presence": len(numbers) > 5,
            "passes_period_detection": len(periods) > 0,
            "has_dates": has_dates,
            "missing_fields": missing_fields,
            "suspicious_values": suspicious_values,
            "format_errors": format_errors,
        }
        details.append(detail)

    years = sorted({int(p[:4]) for p in all_periods if len(p) >= 4 and p[:4].isdigit()})
    continuity_breaks = []
    for prev, current in zip(years, years[1:]):
        if current - prev > 1:
            continuity_breaks.append(f"Gap between {prev} and {current}")

    completeness_failures = [
        d for d in details if d["missing_fields"] or d["format_errors"] or not d["passes_numeric_presence"]
    ]

    validation_summary = {
        "documents_validated": len(pdf_texts),
        "years_detected": years,
        "continuity_breaks": continuity_breaks,
        "missing_months": sorted(set(missing_months_global)),
        "completeness_failures": len(completeness_failures),
        "passes": not continuity_breaks and len(completeness_failures) == 0,
    }

    report = {"summary": validation_summary, "details": details}
    if output_path:
        save_json(report, output_path)
    return report
