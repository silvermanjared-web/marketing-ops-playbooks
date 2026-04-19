# Funnel Data Validator

## The Problem

Funnel data is the foundation of marketing performance analysis. It connects spend at the top to revenue at the bottom. When funnel data is wrong, every conclusion built on it is wrong — and the errors are often subtle enough that no one catches them until a board meeting or budget review.

Most funnel data issues are not dramatic. They are quiet: a stage with slightly more conversions than the stage above it (impossible in a real funnel). A date range that ends a day early. An attribution source that sums to 15% more than the total. A conversion rate that is technically valid but physiologically impossible for the business.

This validator catches those issues before they reach a decision-maker.

## Three-Tier Validation

Funnel data validation works in layers. Each tier assumes the previous tier passed. There is no point checking conversion rate logic if the file cannot be parsed.

### Tier 1: Structural Integrity

Before touching the data itself, confirm the container is sound.

| Check | What It Catches |
|-------|----------------|
| File encoding | UTF-8 BOM artifacts, Latin-1 encoding from Excel exports, null bytes |
| Required columns | Missing stage names, date fields, or metric columns |
| Row-level completeness | Null values in critical fields, entirely blank rows |
| Duplicate detection | Repeated rows that would inflate totals |
| Date parsing | Inconsistent date formats within the same file, unparseable values |

**Verdict if failed:** FAIL. Do not proceed to Tier 2.

### Tier 2: Schema and Funnel Logic

The data parses correctly. Now check whether it makes sense as a funnel.

| Check | What It Catches |
|-------|----------------|
| Stage ordering | Stages must be monotonically decreasing (or equal). If "Qualified" > "Leads", the data is wrong. |
| Conversion rate bounds | Rates should be between 0% and 100%. A 140% stage-to-stage rate means a numerator/denominator mismatch. |
| Rate plausibility | A 0.01% conversion rate or a 99.8% rate is technically valid but worth flagging — it often indicates a stage definition error. |
| Temporal consistency | Day-over-day volume should not have implausible jumps (10x one day, back to baseline the next) without explanation. |
| Metric sign | Conversion counts, spend, and revenue should be non-negative. Negative values usually indicate refunds or data corrections that need separate handling. |

**Verdict if failed:** FAIL on hard violations (stages out of order, rates > 100%). WARNING on plausibility issues.

### Tier 3: Cross-Source Integrity

The funnel data is internally consistent. Now check whether it agrees with reality.

| Check | What It Catches |
|-------|----------------|
| Attribution sum | If you sum conversions by source, does it match the total? Over-attribution (> 100%) suggests double-counting. Under-attribution suggests an "unassigned" bucket is missing. |
| Source reconciliation | Does the Google Ads spend column match what the platform reports? Does the CRM conversion count match the analytics conversion count? |
| Lag detection | Are recent dates systematically lower than historical? This often indicates conversion lag rather than a true performance drop. |
| Cohort completeness | If analyzing by cohort, are all cohorts fully matured? Comparing a 30-day-old cohort to a 7-day-old cohort without adjustment produces misleading metrics. |

**Verdict if failed:** FAIL on attribution math that does not sum. WARNING on lag or completeness concerns.

## Common Failure Modes

**Excel auto-formatting.** Dates get reformatted, leading zeros are stripped from IDs, and long numbers become scientific notation. These are silent data corruption.

**Timezone misalignment.** Platform A reports in UTC. Platform B reports in the account timezone. A "daily" join produces off-by-one errors on every row.

**Partial data pulls.** An API query times out and returns 80% of the data. The totals look plausible but are systematically low. The validator flags suspiciously round or low totals.

**Stage definition drift.** "Marketing Qualified Lead" meant one thing last quarter and something different this quarter after a CRM update. The validator cannot catch semantic drift, but it can catch the resulting rate anomalies.

**Currency mixing.** Revenue data from multiple regions in different currencies concatenated without conversion. The validator checks for mixed currency indicators.

## Output Format

```
TIER 1 — Structural Integrity
  [PASS] File encoding: UTF-8
  [PASS] Required columns: all present
  [FAIL] Duplicate rows: 14 exact duplicates found

TIER 2 — Schema & Funnel Logic
  (skipped — Tier 1 failures must be resolved first)

TIER 3 — Cross-Source Integrity
  (skipped — Tier 1 failures must be resolved first)

VERDICT: FAIL
Resolution: Remove duplicate rows and re-run validation.
```

When all tiers pass with only minor warnings:

```
VERDICT: PASS WITH CAVEATS
Caveats:
  - Conversion lag detected in last 3 days of data (Tier 3)
  - One stage-to-stage rate is unusually high at 89% (Tier 2)
```

## Usage

```bash
# Basic validation
python validate.py --csv funnel_data.csv

# With cross-source reconciliation
python validate.py --csv funnel_data.csv --source-totals platform_totals.csv

# Custom stage ordering
python validate.py --csv funnel_data.csv --stages "impressions,clicks,leads,qualified,opportunities,closed"
```
