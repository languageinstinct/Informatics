"""Format extracted insights into a memo output."""

from __future__ import annotations

from typing import Any

from pipeline.utils.file_utils import save_json, save_text


def format_memo(
    package_id: str,
    classification: dict,
    validation_report: dict,
    financials: dict,
    trends: dict,
    output_dir: str,
) -> dict:
    """
    Build text and JSON memo outputs.
    """
    summary = classification.get("summary", {})
    validation_summary = validation_report.get("summary", {})

    lines = [
        f"Credit Memo for {package_id}",
        "=" * 40,
        "",
        "Classification Summary:",
        f"- Documents processed: {summary.get('total_documents', 0)}",
        f"- Top label: {summary.get('top_label')}",
        f"- Average confidence: {summary.get('average_confidence', 0)}%",
        "",
        "Validation Summary:",
        f"- Years detected: {validation_summary.get('years_detected')}",
        f"- Continuity breaks: {validation_summary.get('continuity_breaks')}",
        f"- Missing months: {validation_summary.get('missing_months')}",
        "",
        "Financial Metrics:",
        f"- Revenue points: {financials.get('revenue')}",
        f"- EBITDA points: {financials.get('ebitda')}",
        f"- Net income points: {financials.get('net_income')}",
        "",
        "Trend Analysis:",
        f"- Revenue growth: {trends.get('revenue_growth')}",
        f"- EBITDA growth: {trends.get('ebitda_growth')}",
        f"- Ratios: {trends.get('ratios')}",
    ]
    memo_text = "\n".join(lines)
    memo_json = {
        "package_id": package_id,
        "classification": classification,
        "validation": validation_report,
        "financials": financials,
        "trends": trends,
        "memo_text": memo_text,
    }

    txt_path = save_text(memo_text, f"{output_dir}/credit_memo.txt")
    json_path = save_json(memo_json, f"{output_dir}/credit_memo.json")
    return {"text_path": str(txt_path), "json_path": str(json_path), "content": memo_text}
