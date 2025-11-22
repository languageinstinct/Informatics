import json
import time
import zipfile
from pathlib import Path
from typing import Iterable

from pipeline.quality_gate.gate_rules import (
    detect_folder_structure,
    detect_inconsistent_naming,
    find_missing_required,
)
from pipeline.utils.file_utils import ensure_dir, save_json
from pipeline.utils.pdf_utils import PDF_EXTRACTION_AVAILABLE, detect_corrupt_pdf, extract_text


def _scan_for_corrupt_pdfs(extracted_paths: Iterable[Path]) -> list[str]:
    corrupt: list[str] = []
    for path in extracted_paths:
        if path.suffix.lower() != ".pdf":
            continue
        if detect_corrupt_pdf(path):
            corrupt.append(str(path))
    return corrupt


def _scan_for_sparse_content(extracted_paths: Iterable[Path]) -> list[str]:
    """Identify PDFs with very little numeric data, indicating missing values."""
    sparse: list[str] = []
    import re
    for path in extracted_paths:
        if path.suffix.lower() != ".pdf":
            continue
        text = extract_text(path)
        numbers = len(re.findall(r"-?\d[\d,\.]*", text))
        if numbers < 5:
            sparse.append(str(path))
    return sparse


def _detect_missing_financial_terms(extracted_paths: Iterable[Path]) -> list[str]:
    """
    Check whether common financial terms appear across the provided PDFs.
    """
    if not PDF_EXTRACTION_AVAILABLE:
        return []
    terms = ["revenue", "cash", "assets", "liabilities", "income", "balance", "flow"]
    aggregated_text = " ".join(extract_text(path) for path in extracted_paths if path.suffix.lower() == ".pdf")
    missing_terms = [term for term in terms if term not in aggregated_text.lower()]
    if len(missing_terms) >= len(terms) - 2:  # most terms absent
        return [f"Missing key financial terms: {', '.join(missing_terms)}"]
    return []


def _extract_for_scan(zip_path: str, scan_dir: Path) -> list[Path]:
    ensure_dir(scan_dir)
    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if member.endswith("/"):
                continue
            dest = scan_dir / member
            ensure_dir(dest.parent)
            with zf.open(member) as src, dest.open("wb") as dst:
                dst.write(src.read())
            extracted.append(dest)
    return extracted


def score_zip(zip_path: str, workdir: str | None = None) -> dict:
    """
    Score the ZIP package for quality gate rules and persist score.json if workdir is provided.
    """
    start = time.time()
    zip_path_obj = Path(zip_path)
    if not zipfile.is_zipfile(zip_path_obj):
        result = {
            "status": "BAD",
            "total_score": 0,
            "issues": ["Not a valid zip archive"],
            "missing_required": [],
            "corrupt_pdfs": [],
            "inconsistent_naming": [],
            "folder_issues": [],
            "files": [],
            "elapsed_seconds": round(time.time() - start, 3),
        }
        if workdir:
            save_json(result, Path(workdir) / "score.json")
        return result

    with zipfile.ZipFile(zip_path_obj, "r") as zf:
        file_names = [name for name in zf.namelist() if not name.endswith("/")]

    missing_required = find_missing_required(file_names)
    folder_issues = detect_folder_structure(file_names)
    naming_issues = detect_inconsistent_naming(file_names)

    scan_dir = Path(workdir) / "gate_scan" if workdir else Path(zip_path_obj).parent / "gate_scan"
    extracted_paths = _extract_for_scan(zip_path, scan_dir)
    corrupt_pdfs = _scan_for_corrupt_pdfs(extracted_paths)
    sparse_pdfs = _scan_for_sparse_content(extracted_paths)
    missing_terms = _detect_missing_financial_terms(extracted_paths)

    penalties = (
        len(missing_required) * 20
        + len(folder_issues) * 10
        + len(naming_issues) * 5
        + len(corrupt_pdfs) * 25
        + len(sparse_pdfs) * 10
        + len(missing_terms) * 10
    )
    total_score = max(0, 100 - penalties)
    status = "GOOD" if total_score >= 70 and not missing_required and not corrupt_pdfs else "BAD"
    issues: list[str] = []
    if missing_required:
        issues.append(f"Missing required docs: {', '.join(missing_required)}")
    issues.extend(folder_issues)
    issues.extend(naming_issues)
    if corrupt_pdfs:
        issues.append(f"Corrupt PDFs: {', '.join(Path(p).name for p in corrupt_pdfs)}")
    if sparse_pdfs:
        issues.append(f"Sparse numeric content in: {', '.join(Path(p).name for p in sparse_pdfs)}")
    issues.extend(missing_terms)

    result = {
        "status": status,
        "total_score": total_score,
        "issues": issues,
        "missing_required": missing_required,
        "corrupt_pdfs": corrupt_pdfs,
        "sparse_pdfs": sparse_pdfs,
        "missing_terms": missing_terms,
        "inconsistent_naming": naming_issues,
        "folder_issues": folder_issues,
        "files": file_names,
        "elapsed_seconds": round(time.time() - start, 3),
        "score_json": None,
        "scan_dir": str(scan_dir),
    }

    if workdir:
        score_path = Path(workdir) / "score.json"
        save_json(result, score_path)
        result["score_json"] = str(score_path)
    return result
