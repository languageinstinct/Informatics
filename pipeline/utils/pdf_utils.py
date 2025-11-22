"""Utilities for working with PDFs in the pipeline."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


# Attempt lightweight imports; fall back gracefully if unavailable.
try:  # pragma: no cover - optional dependency
    import pdfplumber  # type: ignore
except Exception:  # pragma: no cover
    pdfplumber = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from PyPDF2 import PdfReader  # type: ignore
except Exception:  # pragma: no cover
    PdfReader = None  # type: ignore

PDF_EXTRACTION_AVAILABLE = pdfplumber is not None or PdfReader is not None


def extract_text(pdf_path: str | Path) -> str:
    """
    Extract text from a PDF using pdfplumber, PyPDF2, or a minimal fallback.

    Returns empty string if the file is unreadable.
    """
    path = Path(pdf_path)
    if pdfplumber:
        try:
            with pdfplumber.open(path) as pdf:  # type: ignore[attr-defined]
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception:
            return ""

    if PdfReader:
        try:
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""

    # Minimal fallback: read bytes and return ascii-ish content best-effort.
    try:
        raw = path.read_bytes()
        text = raw.decode("latin-1", errors="ignore")
        return re.sub(r"[^\\x09\\x0a\\x0d\\x20-\\x7E]", "", text)
    except Exception:
        return ""


def detect_corrupt_pdf(pdf_path: str | Path) -> bool:
    """Return True if the PDF appears corrupt or unreadable."""
    text = extract_text(pdf_path)
    return text.strip() == ""


def extract_texts(paths: Iterable[str | Path]) -> dict[str, str]:
    """Extract text for multiple PDFs, returning a mapping of path->text."""
    results: dict[str, str] = {}
    for path in paths:
        results[str(path)] = extract_text(path)
    return results
