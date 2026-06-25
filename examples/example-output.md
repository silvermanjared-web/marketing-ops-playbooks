# Example Output

This example shows the intended shape of output from marketing operations playbooks and validation workflows using mock inputs. It is illustrative, not connected to private campaign, account, or customer data.

The repo contains both executable validators and documented diagnostic methods. This file makes that distinction explicit so reviewers can tell what can be run immediately and what is a reusable operating framework.

## Executable example: UTM Taxonomy Validator

### Single URL command

```bash
python skills/utm-taxonomy-validator/validate.py --url "https://example.com/?utm_source=google&utm_medium=cpc&utm_campaign=brand-search"
```

### Sample console output

```text

[PASS] https://example.com/?utm_source=google&utm_medium=cpc&utm_campaign=brand-search

============================================================
Total: 1  |  PASS: 1  |  FAIL: 0  |  WARNING: 0
============================================================
```

### CSV command

```bash
python skills/utm-taxonomy-validator/validate.py --csv sample_campaign_urls.csv --url-column url
```

### Sample failure output

```text

[FAIL] https://example.com/?utm_source=Google&utm_medium=PaidSocial&utm_campaign=Spring Campaign
  !! utm_source: Value 'Google' contains uppercase characters (should be 'google')
  !! utm_medium: Value 'PaidSocial' contains uppercase characters (should be 'paidsocial')
  !! utm_medium: Value 'paidsocial' not in allowed vocabulary: ['cpc', 'cpm', 'email', 'organic-social', 'paid-social', 'referral', 'display', 'affiliate', 'video', 'retargeting']
  !! utm_campaign: Value 'Spring Campaign' contains uppercase characters (should be 'spring campaign')
  !! utm_campaign: Value 'spring campaign' does not match campaign pattern: ^[a-z0-9]+(-[a-z0-9]+)*$
  !! utm_campaign: Value contains forbidden character: ' '

============================================================
Total: 1  |  PASS: 0  |  FAIL: 1  |  WARNING: 0
============================================================
```

### JSON output command

```bash
python skills/utm-taxonomy-validator/validate.py --url "https://example.com/?utm_source=linkedin&utm_medium=paid-social&utm_campaign=executive-brief" --json-output
```

### Sample JSON output

```json
[
  {
    "url": "https://example.com/?utm_source=linkedin&utm_medium=paid-social&utm_campaign=executive-brief",
    "verdict": "PASS",
    "issues": []
  }
]
```

## Documented method example: Funnel Data Validator

This playbook describes the validation method for funnel data: structural checks, schema checks, and cross-source integrity review. Use this output shape when applying the method to a real dataset or when converting the method into an executable validator.

### Sample findings

| Check | Result | Notes | Next action |
|---|---|---|---|
| Required columns | Pass | All expected fields present | Continue |
| Date format | Pass | ISO date format detected | Continue |
| Stage order | Warning | 3 rows show later-stage count higher than prior-stage count | Inspect source export and dedupe logic |
| Source reconciliation | Review | Paid social totals differ from platform export by 4.8% | Reconcile platform, CRM, and reporting table before readout |

## Documented method example: Performance Media Diagnostics

This framework helps isolate whether a performance issue is caused by media execution, measurement, funnel quality, market demand, or operating cadence.

### Sample diagnostic readout

| Symptom | Likely diagnostic lane | Evidence to inspect | Decision implication |
|---|---|---|---|
| Lead volume down, spend stable | Demand or auction pressure | Impression share, CPC, auction insights, search volume | Do not assume creative failure before checking market/auction movement |
| Leads flat, applications down | Funnel quality or handoff | Lead source mix, form completion, CRM stage movement | Fix quality or handoff before scaling spend |
| CPA improved, revenue flat | Attribution or quality mismatch | Down-funnel conversion, value by source, incrementality | Do not scale based only on platform efficiency |

## What this demonstrates

The playbooks turn recurring marketing operations judgment into reusable methods. Executable validators enforce the parts that should fail fast. Documented frameworks structure the parts that require human diagnosis.

## Notes

- This example uses mock data.
- Do not commit private exports, live account IDs, customer data, or sensitive performance data.
- Outputs should support human review, not replace it.
- Keep examples aligned to the actual CLI when a script exists.
