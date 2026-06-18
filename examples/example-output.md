# Example Output

This example shows the intended shape of output from a marketing operations playbook or validation workflow using mock inputs. It is illustrative, not connected to private campaign, account, or customer data.

## Example: UTM Taxonomy Validator

### Input file

```text
sample_campaign_urls.csv
```

### Command

```bash
python skills/utm-taxonomy-validator/validate.py sample_campaign_urls.csv
```

### Sample output

```text
UTM Taxonomy Validator
Rows scanned: 250
Valid rows: 221
Rows with warnings: 21
Rows with errors: 8
Status: review required
```

### Sample findings

| Severity | Field | Issue | Recommended fix |
|---|---|---|---|
| Error | utm_source | Source not in controlled vocabulary | Replace with approved source name |
| Error | utm_medium | Mixed casing detected | Normalize to lowercase standard |
| Warning | utm_campaign | Missing campaign phase | Add phase or launch identifier |
| Warning | utm_content | Duplicate creative label | Add creative variant or placement detail |

## Example: Funnel Data Validator

### Command

```bash
python skills/funnel-data-validator/validate.py sample_funnel.csv
```

### Sample output

```text
Funnel Data Validator
Rows scanned: 500
Structural checks: passed
Schema checks: warning
Cross-source checks: review required
Status: partial pass
```

### Sample findings

| Check | Result | Notes |
|---|---|---|
| Required columns | Pass | All expected fields present |
| Date format | Pass | ISO date format detected |
| Stage order | Warning | 3 rows show later-stage count higher than prior-stage count |
| Source reconciliation | Review | Paid social totals differ from platform export by 4.8% |

## What this demonstrates

The playbooks are designed to turn recurring marketing operations judgment into reusable methods. The output should make it easier to see what passed, what needs review, and what action should happen next.

## Notes

- This example uses mock data.
- Do not commit private exports, live account IDs, customer data, or sensitive performance data.
- Outputs should support human review, not replace it.
