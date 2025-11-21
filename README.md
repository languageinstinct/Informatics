# Risk Intelligence Pipeline

## Overview
This project builds the **Risk Intelligence Pipeline**: an upstream system that prepares, validates, and standardizes financial documents before any model interacts with them.

The objective is **not to build a model**, but to remove the conditions that cause hallucinations by ensuring models only ever see complete, structured, validated inputs.

## Why This Matters
Current deal packages contain 5–75 mixed-format files with inconsistent naming, missing periods, and buried financials. Analysts spend ~40 hours manually cleaning and rewriting credit memos.

The pipeline targets reducing that workload to **~15 minutes** by:

- Stopping incomplete/invalid packages before they hit analysis  
- Standardizing how financials are extracted  
- Producing consistent credit request memos  
- Creating a Good Data Bank for future SLM training  
- Creating a Bad Data Bank to track recurring quality issues  
- Enabling future safe SLM adoption by enforcing input quality

## Key Capabilities
- **Quality Gate & Routing** (GOOD vs BAD ZIPs)
- **Document Classification**
- **Schema Validation**
- **Missing Month/Year Detection**
- **Credit Memo Standardization**
- **Good Data Bank / Bad Data Bank**
- **Optional: automated email for missing docs**
- **Future SLM consumer-ready structured data**

## Documentation
- [Architecture](docs/architecture.md)
- [Context Model](docs/context-model.md)
- [Quality Gate](docs/quality-gate.md)
- [Credit Memo Standardization](docs/memo-standardization.md)
- [Data Banks](docs/data-banks.md)
- [Pipeline Runtime Flow](docs/pipeline-readme.md)
