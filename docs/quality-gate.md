# Quality Gate & Routing Layer

## Purpose
Prevent hallucinations and analyst rework by stopping bad data before any model sees it.

## What It Checks
- Missing financial years or months
- Mislabeled or incorrectly named files
- Incorrect file types
- Corrupted or unreadable PDFs
- Missing required documents (e.g., 3 years of financials)
- ZIP structure issues (nested folders, empty folders)

## Routing Logic
- **GOOD ZIP**  
  → Continue to OCR → classification → validation  
  → Stored in Good Data Bank

- **BAD ZIP**  
  → Flagged, logged, stored in Bad Data Bank  
  → Sent to Exception workflow  
  → (Optional) Auto-email to Sales requesting missing docs

## Why This Matters
Instead of trying to fix hallucinations downstream, the pipeline ensures models never encounter missing-data situations in the first place.
