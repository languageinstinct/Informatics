# Context Model Alignment

This shows how the pipeline maps to real stakeholders and data flows.

| Actor / Entity        | Pipeline Component                          |
|-----------------------|----------------------------------------------|
| Sales                 | Intake Service + ZIP Quality Scoring         |
| Analysts              | Exception Path + Standardized Memo Output    |
| Compliance / Audit    | Validation Logs + Data Lineage               |
| Document Types        | Classification + Schema Validation           |
| External Businesses   | Missing-doc Notification Automation          |
| Future SLM / Models   | Downstream Consumer of Structured Data       |

The architecture and context model intentionally align to ensure:
- Clear ownership
- Governance and auditability
- Smooth SLM integration later
