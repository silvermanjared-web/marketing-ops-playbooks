# Data Sanity Checker

## What This Is

A pre-flight data quality check designed to run before you use data for anything consequential — analysis, reporting, budget decisions, board decks. It is not a full data validation suite. It is the minimum set of checks that catch the errors most likely to embarrass you.

The philosophy: every dataset is guilty until proven sane.

## Five Check Categories

### 1. Structural Checks

Confirm the data exists in the shape you expect.

- **Null rate per column** — What percentage of values are missing? A 2% null rate in a revenue column silently understates totals.
- **Duplicate rows** — Exact duplicates are almost never intentional. Near-duplicates (same key, different values) are worse.
- **Data type consistency** — Is every value in the "spend" column actually numeric? One stray string breaks aggregation silently in some tools, loudly in others.
- **Column count stability** — If you expect 12 columns and get 11, something upstream changed.
- **Row count reasonableness** — Is today's file roughly the same size as yesterday's? A file that is 60% smaller than usual is often a partial export, not a real data change.

### 2. Temporal Checks

Time-series data has its own failure modes.

- **Date range completeness** — Are there gaps? Missing days in a daily dataset inflate per-day averages and hide trends.
- **Weekend/holiday patterns** — Business data often drops on weekends. If your weekend data looks the same as weekday data, it might be a backfill artifact.
- **Timezone consistency** — Data from UTC sources joined with local-time data produces off-by-one errors on every date boundary.
- **Recency** — Is the most recent row actually recent? Stale data that looks current is dangerous.

### 3. Metric Checks

Do the numbers make sense given what you know about the business?

- **Range validation** — Conversion rates above 100%, negative spend, CTRs above 50%. These are not judgment calls; they are data errors.
- **Outlier detection** — Values more than 3 standard deviations from the column mean. Not always errors, but always worth investigating.
- **Zero-value prevalence** — A column that is 80% zeros is either measuring something rare or broken.
- **Sum consistency** — Do the parts add up to the whole? Channel-level spend should sum to total spend within rounding tolerance.

### 4. Cross-Source Checks

When data comes from multiple systems, they disagree. The question is how much.

- **Total reconciliation** — Does the CRM say the same thing as the ad platform? Within 5% is normal. Beyond 10% is a problem.
- **Dimension cardinality** — If you expect 5 campaign types and find 47, someone is not using the taxonomy.
- **Join coverage** — When you join two tables, what percentage of rows match? A 70% match rate means 30% of your data is being silently excluded.

### 5. Attribution Checks

Attribution data is uniquely fragile.

- **Model consistency** — Are you mixing first-touch and last-touch data in the same analysis?
- **Conversion window** — Does your attribution window match your reporting window? A 28-day attribution window with 7-day reporting creates systematic under-counting.
- **Channel coverage** — Are all channels represented? A missing channel is not zero — it is unknown.
- **Over-attribution** — If you sum attributed conversions across channels and get more than actual conversions, your model is double-counting.

## When to Run This

**Before analysis.** Every time. Not after the analysis is done and the conclusions feel off.

**Before board meetings.** The cost of presenting wrong data is much higher than the cost of running a 30-second check.

**Before budget decisions.** Budget allocation based on unchecked data is how you spend six months optimizing the wrong channel.

**After any upstream change.** New CRM fields, platform migrations, API version updates, new team members with data access — all of these introduce data quality risk.

**On a schedule.** Daily or weekly automated checks against your core datasets. Most issues are easier to fix when caught early.

## Severity Levels

Each check produces one of three severities:

| Severity | Meaning | Action |
|----------|---------|--------|
| **CRITICAL** | Data is materially wrong. Using it will produce incorrect conclusions. | Stop. Fix the data before proceeding. |
| **WARNING** | Data has anomalies that may or may not be errors. | Investigate before relying on affected metrics. |
| **INFO** | Observation worth noting but not blocking. | Log it. Review if other checks also flag issues. |

## Usage

```bash
# Basic check on a CSV
python validate.py --file data.csv

# Check with custom thresholds
python validate.py --file data.csv --null-threshold 0.02 --outlier-sigma 2.5

# JSON output for automation
python validate.py --file data.csv --json-output
```
