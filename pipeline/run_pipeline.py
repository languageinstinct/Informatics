from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from pipeline.classification.classify import classify_documents
from pipeline.data_banks.bad_bank import quarantine
from pipeline.data_banks.good_bank import store as store_good
from pipeline.intake.receive_zip import save_zip_locally
from pipeline.intake.unzipper import unzip_archive
from pipeline.memo_builder.analyze_trends import analyze
from pipeline.memo_builder.extract_financials import extract
from pipeline.memo_builder.memo_formatter import format_memo
from pipeline.quality_gate.router import route
from pipeline.quality_gate.scorer import score_zip
from pipeline.utils.file_utils import ensure_dir, package_workdir, save_json
from pipeline.utils.pdf_utils import extract_texts
from pipeline.validation.schema_validator import validate_documents


class Colors:
    OK = "\033[92m"
    WARN = "\033[93m"
    BAD = "\033[91m"
    END = "\033[0m"


@dataclass
class PipelineResult:
    package_id: str
    status: str
    workdir: str
    artifacts: dict
    elapsed_seconds: float


def _log(message: str, level: str = "info") -> None:
    color = Colors.OK if level == "info" else Colors.WARN if level == "warn" else Colors.BAD
    print(f"{color}{message}{Colors.END}")


def run_pipeline(zip_path: str, base_workdir: str = "data/workdir") -> PipelineResult:
    start_time = time.perf_counter()
    package_id = Path(zip_path).stem
    workdir = package_workdir(base_workdir, package_id)
    _log(f"Starting pipeline for {package_id} → workdir: {workdir}")

    stage_start = time.perf_counter()
    local_zip = save_zip_locally(zip_path, workdir)
    _log(f"[Intake] Copied ZIP in {time.perf_counter() - stage_start:.3f}s")

    stage_start = time.perf_counter()
    score = score_zip(local_zip, workdir=str(workdir))
    _log(f"[Quality Gate] Score: {score['total_score']} ({score['status']}) in {time.perf_counter() - stage_start:.3f}s")
    path = route(score)
    artifacts: dict = {"score_json": score.get("score_json")}

    if path == "EXCEPTION_PATH":
        _log("Bad ZIP detected → sending to Bad Data Bank", level="bad")
        quarantine(package_id, local_zip, "Quality gate failure", score_report=score)
        return PipelineResult(package_id, "REJECTED", str(workdir), artifacts, time.perf_counter() - start_time)

    # Extract ZIP
    stage_start = time.perf_counter()
    extracted_dir = ensure_dir(workdir / "extracted")
    extracted_paths = unzip_archive(local_zip, extracted_dir)
    pdf_paths = [p for p in extracted_paths if p.suffix.lower() == ".pdf"]
    _log(f"[Unzip] Extracted {len(extracted_paths)} files ({len(pdf_paths)} PDFs) in {time.perf_counter() - stage_start:.3f}s")

    # Extract text
    stage_start = time.perf_counter()
    pdf_texts = extract_texts(pdf_paths)
    pdf_texts_path = save_json(pdf_texts, workdir / "pdf_texts.json")
    _log(f"[Text Extraction] Completed in {time.perf_counter() - stage_start:.3f}s")
    artifacts["pdf_texts_json"] = str(pdf_texts_path)

    # Classification
    stage_start = time.perf_counter()
    classification_report = classify_documents(
        pdf_texts,
        label_map_path=Path(__file__).parent / "classification" / "label_map.json",
        output_path=workdir / "classification.json",
    )
    _log(f"[Classification] Completed in {time.perf_counter() - stage_start:.3f}s")
    artifacts["classification_json"] = str(workdir / "classification.json")

    # Validation
    stage_start = time.perf_counter()
    validation_report = validate_documents(
        pdf_texts,
        classification=classification_report,
        output_path=workdir / "validation_report.json",
    )
    _log(f"[Validation] Completed in {time.perf_counter() - stage_start:.3f}s")
    artifacts["validation_json"] = str(workdir / "validation_report.json")

    if not validation_report.get("summary", {}).get("passes", True):
        _log("[Validation] Failures detected → sending to Bad Data Bank", level="bad")
        quarantine(
            package_id,
            local_zip,
            "Validation failures",
            score_report=score,
            classification_attempt=classification_report,
        )
        return PipelineResult(package_id, "REJECTED_VALIDATION", str(workdir), artifacts, time.perf_counter() - start_time)

    # Financial extraction and memo
    stage_start = time.perf_counter()
    financials = extract(pdf_texts.values())
    trends = analyze(financials)
    memo = format_memo(
        package_id,
        classification_report,
        validation_report,
        financials,
        trends,
        output_dir=str(workdir),
    )
    _log(f"[Memo] Built memo in {time.perf_counter() - stage_start:.3f}s")
    artifacts["memo_text"] = memo["text_path"]
    artifacts["memo_json"] = memo["json_path"]

    # Persist in Good Data Bank
    stage_start = time.perf_counter()
    stored = store_good(package_id, str(workdir), artifacts, version=1)
    _log(f"[Good Bank] Stored artifacts in {time.perf_counter() - stage_start:.3f}s")

    elapsed = time.perf_counter() - start_time
    _log(f"Pipeline completed in {elapsed:.3f}s")
    return PipelineResult(package_id, "COMPLETED", str(workdir), stored, elapsed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Risk Intelligence Pipeline")
    parser.add_argument("zip_path", help="Path to the ZIP file to process")
    args = parser.parse_args(argv)

    result = run_pipeline(args.zip_path)
    _log(f"Result: {result.status} → artifacts: {result.artifacts}")
    return 0 if result.status == "COMPLETED" else 1


if __name__ == "__main__":
    sys.exit(main())
