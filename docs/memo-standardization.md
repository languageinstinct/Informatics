# Credit Request Memo Standardization

## Problem
Credit request memos vary drastically in quality. Some are excellent; others lack financial structure or miss critical information. Analysts currently rewrite these manually.

## Solution
The pipeline standardizes memos by extracting and normalizing the financial signals that matter:

- Revenue, expenses, EBITDA, margins
- Year-over-year trends
- Bank statement summaries
- Debt levels
- Missing-month/year detection
- Consistent narrative template

## Components
- Financial period validator
- Extraction engine for core statements
- Trend analysis module
- Standard memo formatter

## Value
- Consistent memo quality across all analysts
- Removes subjective formatting differences
- Cuts preparation time from **~40 hours to ~15 minutes**
- Provides regulated, auditable structure
- Feeds Good Data Bank with consistent analyst-ready outputs
