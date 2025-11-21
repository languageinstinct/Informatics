# Architecture

The Risk Intelligence Pipeline consists of the following components:

## 1. Intake Service
Receives ZIP packages of documents from Sales.

## 2. Quality Gate & Routing Layer (NEW)
Evaluates completeness, labeling, financial periods, and file validity.

- GOOD ZIPs → Standard Path
- BAD ZIPs → Exception Path

## 3. OCR (if needed)
Extracts text from scanned PDFs.

## 4. Document Classification
Labels files by type (P&L, Balance Sheet, Tax Return, Bank Statements, etc.)

## 5. Schema Validation
Validates expected structure, formats, and year/month completeness.

## 6. Metadata Layer
Generates traceability: timestamps, checksums, missing info, classification confidence.

## 7. Credit Memo Standardization
Outputs a uniform, consistent credit request memo.

## 8. Good Data Bank
Stores validated and structured outputs for reuse, benchmarking, or SLM training.

## 9. Bad Data Bank
Stores incomplete, incorrect, or corrupted submissions for remediation tracking.

## 10. (Optional) Automated Missing-Doc Notification
Requests missing financials automatically.

## 11. SLM / Model Consumer (Future)
Clean data feeds any future SLM the organization chooses.
