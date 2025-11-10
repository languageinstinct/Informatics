# Risk Intelligence Pipeline

Pipeline for automating risk and financial document ingestion, normalization, and validation.
Prepares consistent JSON data for downstream SLM or GPT-based analysis.

## Overview
Sales teams upload mixed document packages (5–75 files).  
The pipeline:
1. Unzips and OCRs files.
2. Classifies them as structured or unstructured.
3. Extracts relevant data and summaries.
4. Validates completeness and consistency.
5. Outputs a master JSON ready for model analysis.

## Tech Stack
- Python 3.11+
- FastAPI (optional service wrapper)
- pandas, openpyxl, PyPDF2, camelot
- tesseract (OCR)
- pydantic (schema validation)
- dotenv for environment variables

## Run Locally
```bash
git clone https://github.com/<yourname>/risk-intel-pipeline.git
cd risk-intel-pipeline
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py


# Architecture

[Sales ZIP Upload]
        ↓
 Ingest + OCR + Normalize
        ↓
 Classify (structured / unstructured)
        ↓
 Route to Extractors
     ├─ Structured → deterministic parser
     └─ Unstructured → placeholder summarizer (mock)
        ↓
 Aggregate + Validate
        ↓
 Produce master_JSON + report
        ↓
 Handoff (to-be-plugged model)
