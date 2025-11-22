"""Hold or log records that fail gates or validation."""

from __future__ import annotations

from pathlib import Path

from pipeline.utils.file_utils import copy_file, ensure_dir, save_json


def quarantine(package_id: str, zip_path: str, reason: str, score_report: dict | None = None, classification_attempt: dict | None = None) -> dict:
    """
    Save rejected packages with context for later review.
    """
    base = ensure_dir(Path("pipeline/data_banks/bad_bank") / package_id)
    copied = {"zip_path": str(copy_file(zip_path, base / Path(zip_path).name))}
    report = {
        "package_id": package_id,
        "reason": reason,
        "score_report": score_report,
        "classification_attempt": classification_attempt,
    }
    report_path = save_json(report, base / "rejection_report.json")
    copied["rejection_report"] = str(report_path)
    return copied
