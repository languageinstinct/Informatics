"""Classify documents using regex + heuristic rules with scoring and extraction."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from pipeline.utils.file_utils import save_json


LABEL_PATTERNS = {
    "income_statement": [r"income[_\\s]?statement", r"p&l", r"profit[_\\s]?loss"],
    "balance_sheet": [r"balance[_\\s]?sheet"],
    "cash_flow": [r"cash[_\\s]?flow"],
    "bank_statement": [r"bank[_\\s]?statement"],
    "ar_aging": [r"aging", r"accounts[_\\s]?receivable"],
    "cap_table": [r"cap[_\\s]?table", r"capitalization"],
    "contract": [r"contract", r"agreement"],
}


def _load_label_map(label_map_path: str | Path | None = None) -> dict[str, int]:
    """Load the label map if present to include ids in results."""
    if not label_map_path:
        return {}
    try:
        return json.loads(Path(label_map_path).read_text())
    except Exception:
        return {}


def _score_label(patterns: list[str], text: str, filename: str) -> tuple[float, list[str]]:
    reasons: list[str] = []
    hits = 0
    for pattern in patterns:
        if re.search(pattern, filename, flags=re.IGNORECASE):
            hits += 1
            reasons.append(f"Filename matches {pattern}")
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits += 1
            reasons.append(f"Text matches {pattern}")
    confidence = min(1.0, 0.25 * hits)
    return confidence, reasons


def _extract_number(text: str, patterns: Iterable[str]) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        number_str = match.group(1).replace(",", "")
        try:
            return float(number_str)
        except ValueError:
            continue
    return None


def _has_placeholder(value: str) -> bool:
    return bool(re.search(r"\\b(tbd|n/?a|--+|\\?\\?\\?)\\b", value, flags=re.IGNORECASE))


def _extract_income_statement(text: str) -> dict:
    fields = {
        "revenue": _extract_number(text, [r"revenue[^\\d]+(-?[\\d,\\.]+)"]),
        "cogs": _extract_number(text, [r"cogs[^\\d]+(-?[\\d,\\.]+)", r"cost of goods[^\\d]+(-?[\\d,\\.]+)"]),
        "operating_expenses": _extract_number(text, [r"operating expenses[^\\d]+(-?[\\d,\\.]+)"]),
        "ebitda": _extract_number(text, [r"ebitda[^\\d]+(-?[\\d,\\.]+)"]),
        "net_income": _extract_number(text, [r"net income[^\\d]+(-?[\\d,\\.]+)", r"net profit[^\\d]+(-?[\\d,\\.]+)"]),
    }
    missing = [k for k, v in fields.items() if v is None and k != "ebitda"]
    suspicious = [k for k, v in fields.items() if v is not None and v < 0]
    format_errors = []
    for token in re.findall(r"[A-Za-z]+", text):
        if _has_placeholder(token):
            format_errors.append("placeholder detected")
            break
    return fields, missing, suspicious, format_errors


def _extract_balance_sheet(text: str) -> tuple[dict, list[str], list[str], list[str]]:
    fields = {
        "cash": _extract_number(text, [r"cash[^\\d]+(-?[\\d,\\.]+)"]),
        "accounts_receivable": _extract_number(text, [r"accounts receivable[^\\d]+(-?[\\d,\\.]+)"]),
        "inventory": _extract_number(text, [r"inventory[^\\d]+(-?[\\d,\\.]+)"]),
        "pp&e": _extract_number(text, [r"p\\s?p\\s?&\\s?e[^\\d]+(-?[\\d,\\.]+)", r"property[^\\d]+(-?[\\d,\\.]+)"]),
        "accounts_payable": _extract_number(text, [r"accounts payable[^\\d]+(-?[\\d,\\.]+)"]),
        "short_term_debt": _extract_number(text, [r"short[-\\s]?term debt[^\\d]+(-?[\\d,\\.]+)"]),
        "long_term_debt": _extract_number(text, [r"long[-\\s]?term debt[^\\d]+(-?[\\d,\\.]+)"]),
        "equity": _extract_number(text, [r"equity[^\\d]+(-?[\\d,\\.]+)"]),
    }
    missing_core = [k for k, v in fields.items() if v is None and k in {"cash", "accounts_receivable", "accounts_payable", "equity"}]
    suspicious = [k for k, v in fields.items() if v is not None and v < 0]
    format_errors = []
    if _has_placeholder(text):
        format_errors.append("placeholder detected")
    # Balance check if totals present
    total_assets = _extract_number(text, [r"total assets[^\\d]+(-?[\\d,\\.]+)"])
    total_liab_equity = _extract_number(text, [r"total liabilities[^\\d]+equity[^\\d]+(-?[\\d,\\.]+)", r"total liabilities[^\\d]+(-?[\\d,\\.]+).*equity[^\\d]+(-?[\\d,\\.]+)"])
    if total_assets is not None and total_liab_equity is not None and abs(total_assets - total_liab_equity) > 1:
        format_errors.append("non_balancing: assets != liabilities + equity")
    return fields, missing_core, suspicious, format_errors


def _extract_bank_statement(text: str) -> tuple[dict, list[str], list[str], list[str]]:
    fields = {
        "starting_balance": _extract_number(text, [r"starting balance[^\\d]+(-?[\\d,\\.]+)", r"beginning balance[^\\d]+(-?[\\d,\\.]+)"]),
        "ending_balance": _extract_number(text, [r"ending balance[^\\d]+(-?[\\d,\\.]+)", r"closing balance[^\\d]+(-?[\\d,\\.]+)"]),
        "list_of_transactions": [],
    }
    transactions = re.findall(r"(\\d{1,2}/\\d{1,2}/\\d{2,4}).{0,40}?(-?[\\d,\\.]+)", text)
    fields["list_of_transactions"] = [{"date": d, "amount": float(a.replace(',', ''))} for d, a in transactions]
    missing = [k for k, v in fields.items() if (v is None or v == []) and k != "list_of_transactions"]
    suspicious = []
    if fields["starting_balance"] is not None and fields["starting_balance"] < 0:
        suspicious.append("negative starting_balance")
    format_errors = []
    if not transactions:
        format_errors.append("incomplete transaction sections")
    return fields, missing, suspicious, format_errors


def _extract_ar_aging(text: str) -> tuple[dict, list[str], list[str], list[str]]:
    customers = []
    for line in text.splitlines():
        parts = re.findall(r"([A-Za-z0-9 ]+)\\s+(\\d+[\\d,\\.\\-]*)\\s+(\\d+[\\d,\\.\\-]*)\\s+(\\d+[\\d,\\.\\-]*)\\s+(\\d+[\\d,\\.\\-]*)", line)
        for name, cur, d30, d60, d90 in parts:
            customers.append(
                {
                    "customer": name.strip(),
                    "current": float(cur.replace(",", "")),
                    "thirty_days": float(d30.replace(",", "")),
                    "sixty_days": float(d60.replace(",", "")),
                    "ninety_plus_days": float(d90.replace(",", "")),
                }
            )
    fields = {"customers": customers}
    missing = ["current", "thirty_days", "sixty_days", "ninety_plus_days"] if not customers else []
    suspicious = []
    format_errors = []
    return fields, missing, suspicious, format_errors


def _extract_cap_table(text: str) -> tuple[dict, list[str], list[str], list[str]]:
    rows = []
    for line in text.splitlines():
        parts = re.findall(r"([A-Za-z ]+)\\s+(\\d{1,3}(?:\\.\\d+)?%)\\s+(\\d+[\\d,\\.\\-]*)", line)
        for name, pct, shares in parts:
            try:
                pct_val = float(pct.strip("%"))
                shares_val = float(shares.replace(",", ""))
                rows.append({"shareholder": name.strip(), "ownership_percent": pct_val, "shares": shares_val})
            except ValueError:
                continue
    total_pct = sum(r["ownership_percent"] for r in rows)
    fields = {"rows": rows, "ownership_total": total_pct if rows else None}
    missing = []
    if not rows:
        missing.extend(["shareholder", "ownership_percent", "shares"])
    suspicious = []
    format_errors = []
    if rows and abs(total_pct - 100) > 0.5:
        format_errors.append("ownership total not equal to 100%")
    return fields, missing, suspicious, format_errors


def _extract_contract(text: str) -> tuple[dict, list[str], list[str], list[str]]:
    fields = {
        "customer_name": None,
        "contract_value": _extract_number(text, [r"(?:contract|agreement) value[^\\d]+(-?[\\d,\\.]+)", r"value[^\\d]+(-?[\\d,\\.]+)"]),
        "term_length": _extract_number(text, [r"term[^\\d]+(\\d+)", r"\\b(\\d+) months\\b"]),
        "payment_terms": None,
    }
    name_match = re.search(r"between\\s+([A-Za-z0-9 &]+)", text, flags=re.IGNORECASE)
    if name_match:
        fields["customer_name"] = name_match.group(1).strip()
    pay_match = re.search(r"payment terms[^\\n]+", text, flags=re.IGNORECASE)
    if pay_match:
        fields["payment_terms"] = pay_match.group(0).strip()

    missing = [k for k, v in fields.items() if v is None and k in {"customer_name", "contract_value", "term_length"}]
    suspicious = []
    format_errors = []
    return fields, missing, suspicious, format_errors


def _build_structured(label: str, text: str) -> dict:
    """
    Build strict JSON structure per document.
    """
    extractors = {
        "income_statement": _extract_income_statement,
        "balance_sheet": _extract_balance_sheet,
        "bank_statement": _extract_bank_statement,
        "ar_aging": _extract_ar_aging,
        "cap_table": _extract_cap_table,
        "contract": _extract_contract,
    }
    if label not in extractors:
        return {
            "document_type": "unknown",
            "fields": {},
            "flags": {"missing_fields": [], "suspicious_values": [], "format_errors": ["unknown document type"]},
        }

    fields, missing, suspicious, format_errors = extractors[label](text)
    # Ensure nulls represented as None in Python (JSON null when saved)
    for key, value in fields.items():
        if value is None:
            fields[key] = None
    return {
        "document_type": label,
        "fields": fields,
        "flags": {
            "missing_fields": missing,
            "suspicious_values": suspicious,
            "format_errors": format_errors,
        },
    }


def classify_document(path: str, text: str) -> dict:
    """Return classification result with confidence, rationale, and structured extraction."""
    best_label = "unknown"
    best_confidence = 0.0
    reasons: list[str] = ["No patterns matched"]
    for label, patterns in LABEL_PATTERNS.items():
        confidence, explanation = _score_label(patterns, text, Path(path).name)
        if confidence > best_confidence:
            best_label = label
            best_confidence = confidence
            reasons = explanation
    structured = _build_structured(best_label, text)
    return {
        "path": path,
        "label": best_label,
        "confidence": round(best_confidence * 100, 1),  # percentage
        "reasons": reasons,
        "structured": structured,
    }


def classify_documents(pdf_texts: dict[str, str], label_map_path: str | None = None, output_path: str | None = None) -> dict:
    """
    Classify multiple documents and optionally persist a structured report.
    """
    label_map = _load_label_map(label_map_path)
    documents = []
    label_counts: dict[str, int] = {}
    for path, text in pdf_texts.items():
        result = classify_document(path, text)
        if label_map:
            result["label_id"] = label_map.get(result["label"])
        documents.append(result)
        label_counts[result["label"]] = label_counts.get(result["label"], 0) + 1

    summary = {
        "total_documents": len(documents),
        "labels": label_counts,
        "top_label": max(label_counts, key=label_counts.get) if label_counts else None,
        "average_confidence": round(
            sum(doc["confidence"] for doc in documents) / len(documents), 1
        )
        if documents
        else 0.0,
    }

    classification = {"documents": documents, "summary": summary}
    if output_path:
        save_json(classification, output_path)
    return classification
