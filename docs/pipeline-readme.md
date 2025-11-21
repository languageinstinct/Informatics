# Pipeline Runtime Flow

## 1. Receive ZIP Package
Sales submits a ZIP with financial records.

## 2. Quality Gate (GOOD or BAD Path)
Evaluates completeness, structure, financial periods, and file validity.

### GOOD Path:
3. OCR (if needed)  
4. Document Classification  
5. Schema Validation  
6. Missing-period detection  
7. Memo Standardization  
8. Store in Good Data Bank

### BAD Path:
3. Flag ZIP and store in Bad Data Bank  
4. Exception workflow opens  
5. (Optional) Auto-email requests missing/incorrect documents

## 3. Structured Output to SLM (Future)
Clean, validated data is compatible with any future SLM the company chooses.
