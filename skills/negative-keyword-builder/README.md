# Negative Keyword Builder

## Why Negative Keywords Matter

Every paid search account leaks budget to irrelevant queries. The question is not whether it is happening — it is how much. In mature accounts, 10-20% of search spend goes to queries that will never convert. In new or poorly maintained accounts, that number can be 40% or higher.

Negative keywords are the fix. But most teams approach negation reactively — reviewing search term reports one query at a time, making one-off decisions, and missing the patterns. This tool takes a structured approach: classify queries by theme, evaluate each theme's performance in aggregate, and build negation lists that address categories of waste rather than individual queries.

## The Layered Negation Model

Negative keywords operate at three levels. Using the wrong level creates collateral damage.

### Account-Level Negatives
Themes that are universally irrelevant. No campaign in the account should show for these.

**Examples:** job-seeking queries ("careers", "hiring", "salary"), DIY/free queries when you sell a paid product ("free", "open source", "tutorial"), competitor brand terms you have decided not to bid on.

### Campaign-Level Negatives
Themes relevant to some campaigns but not others. A brand campaign should negate generic terms. A top-of-funnel campaign should negate brand terms.

**Examples:** Brand terms negated from non-brand campaigns, product-specific terms negated from campaigns targeting different products.

### Ad Group-Level Negatives
Precision negation to prevent overlap between ad groups within the same campaign. This keeps each ad group's traffic clean and its quality score isolated.

**Examples:** "enterprise" negated from the SMB ad group. "free trial" negated from the demo-request ad group.

## Theme Classification

Rather than evaluating queries individually, group them into themes and evaluate the theme.

| Theme | Signal | Typical Action |
|-------|--------|---------------|
| Job seekers | "jobs", "careers", "hiring", "salary", "interview" | Account-level exact + phrase negative |
| Competitor research | Competitor brand names, "vs", "alternative to", "review" | Depends on strategy — sometimes worth bidding |
| Educational/informational | "what is", "how to", "definition", "wiki" | Campaign-level — may be relevant for awareness campaigns |
| Free/DIY | "free", "open source", "template", "DIY" | Account-level for paid products; keep for freemium |
| Wrong geography | City names, country names outside target | Account-level |
| Wrong audience segment | Industry terms outside your target vertical | Campaign-level |
| Price sensitive | "cheap", "discount", "coupon", "free shipping" | Depends on positioning |
| Irrelevant modifiers | "used", "vintage", "wholesale", "bulk" | Varies by business |

## Confidence Thresholds

Not every low-performing query should be negated. The tool uses thresholds to separate signal from noise.

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Impressions | >= 10 | Below this, not enough data to judge |
| Spend | >= $5 | Minimum spend before a query is worth evaluating |
| Conversions | 0 in last 90 days | Zero-conversion with meaningful spend is the strongest signal |
| Conversion rate | < 50% of account average | Underperforming by half or more after sufficient volume |
| Cost per conversion | > 2x account target | Too expensive even if it converts occasionally |

Queries that meet the volume threshold but convert well should never be negated, regardless of theme classification. The theme is a starting hypothesis; performance data is the verdict.

## Match Type Selection

Choosing the right negative match type prevents over-negation.

| Match Type | When to Use | Risk Level |
|------------|-------------|------------|
| Exact | You want to block this specific query and nothing else | Low — surgical |
| Phrase | You want to block any query containing this phrase | Medium — watch for collateral |
| Broad | You want to block any query containing all these words in any order | High — can block legitimate traffic |

**Default recommendation:** Start with phrase match for theme-level negatives. Use exact match for individual high-spend zero-conversion queries. Avoid broad match negatives unless the theme is unambiguously irrelevant.

## Output Format

The tool produces a structured recommendation:

```
THEME: Job Seekers
  Queries matched: 47
  Total spend: $823.50
  Conversions: 0
  Recommended action: NEGATE
  Level: Account
  Match type: Phrase
  Negative keywords:
    - "careers"
    - "hiring"
    - "salary"
    - "job openings"

THEME: Competitor Research
  Queries matched: 12
  Total spend: $445.20
  Conversions: 3
  Recommended action: REVIEW — converts at low rate but non-zero
  Level: N/A (requires manual decision)
```

## Usage

```bash
# Analyze a search term report
python classify.py --csv search_terms.csv

# With custom classification rules
python classify.py --csv search_terms.csv --rules custom_rules.json

# Set minimum spend threshold
python classify.py --csv search_terms.csv --min-spend 10

# Export negatives list for upload
python classify.py --csv search_terms.csv --export negatives.csv
```

## Expected CSV Format

The input CSV should contain columns from a Google Ads search terms report (or equivalent):

| Column | Description |
|--------|-------------|
| `search_term` | The actual query the user searched |
| `campaign` | Campaign name |
| `ad_group` | Ad group name |
| `impressions` | Impression count |
| `clicks` | Click count |
| `cost` | Spend amount |
| `conversions` | Conversion count |
