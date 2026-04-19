# Marketing Ops Playbooks

A structured set of repeatable playbooks for common marketing operations problems — taxonomy governance, data validation, and performance diagnostics.

## Why This Exists

Marketing operations fails when knowledge lives in people's heads instead of systems. These playbooks encode repeatable methodologies for the work that matters most: making sure the data is right, the taxonomy is clean, the funnel math checks out, and diagnostic thinking follows a framework instead of intuition.

These are designed to reduce variability across teams and improve consistency at scale.

Each skill is:
- **Documented** — clear methodology, not just code
- **Executable** — Python validation scripts you can run against real data
- **Opinionated** — reflects actual operating experience, not generic advice

## Skills

| Skill | What It Does |
|-------|-------------|
| [UTM Taxonomy Validator](skills/utm-taxonomy-validator/) | Validates UTM parameters against a controlled vocabulary before they propagate through your stack |
| [Funnel Data Validator](skills/funnel-data-validator/) | Three-tier validation of conversion funnel data — structural, schema, and cross-source integrity |
| [Data Sanity Checker](skills/data-sanity-checker/) | Pre-flight data quality checks before analysis or reporting — catches nulls, duplicates, drift, and anomalies |
| [Negative Keyword Builder](skills/negative-keyword-builder/) | Automated search term classification and negative keyword strategy from Google Ads query reports |
| [Performance Media Diagnostics](skills/performance-media-diagnostics/) | Structured diagnostic framework for isolating paid media performance issues from measurement, product, and market problems |

## Frameworks

Strategic planning templates for recurring marketing operations work:

| Framework | Purpose |
|-----------|---------|
| [CRO Test Planning](frameworks/cro-test-planning.md) | Phased conversion rate optimization roadmap with hypothesis structure and success criteria |
| [LTV/CAC Audit](frameworks/ltv-cac-audit.md) | Methodology for auditing unit economics models — formula integrity, data completeness, and anomaly detection |
| [Competitive Analysis](frameworks/competitive-analysis.md) | Framework for assessing competitor positioning, messaging, and conversion architecture |

## Design Philosophy

- **Methodology first, code second** — the README explains the thinking; the script automates the execution
- **Controlled vocabulary** — marketing data breaks when naming is ad hoc; these tools enforce structure
- **Three tiers of validation** — structural integrity → schema logic → cross-source reconciliation
- **Diagnostic trees, not checklists** — problems have root causes; frameworks should help you find them, not just list symptoms
