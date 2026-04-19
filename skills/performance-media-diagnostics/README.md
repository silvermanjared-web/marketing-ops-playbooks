# Performance Media Diagnostics

## The Problem This Solves

"Performance is down" is the most common and least useful statement in marketing. It triggers a scramble: someone pulls a report, someone else blames a creative change, a third person suggests increasing budget. None of these responses are diagnostic. They are reactions.

Effective performance troubleshooting follows a structured order. Most teams jump directly to media levers (budgets, bids, targeting) because those are the easiest to change. But the majority of performance issues originate upstream — in measurement, product, market conditions, or funnel mechanics. Changing media levers to fix a measurement problem makes the measurement problem worse.

This framework enforces a diagnostic sequence that starts with the most common (and most overlooked) root causes.

## The Four-Level Diagnostic Tree

### Level 1: Is the Measurement System Trustworthy?

Before diagnosing performance, confirm you are measuring it correctly. Measurement issues masquerade as performance issues constantly.

| Check | What It Catches |
|-------|----------------|
| Conversion tag firing | Tags silently break during site deploys. A "performance drop" that coincides with a site release is usually a tracking break. |
| Conversion lag | Many platforms report conversions with 1-7 day lag. A "bad week" may just be an incomplete week. |
| Attribution window changes | Platform default attribution windows change. A silent shift from 28-day to 7-day click attribution makes performance look worse instantly. |
| Pixel/SDK version | Outdated tracking code produces data loss. iOS updates, browser privacy changes, and consent management all affect conversion visibility. |
| Cross-domain tracking | If your conversion path crosses domains (marketing site to app, for example), cross-domain tracking breaks are invisible unless you check. |
| Bot/spam traffic | A sudden traffic spike with zero conversions may be bot traffic inflating your denominator. |

**If Level 1 fails:** Fix measurement before changing anything else. Adjusting bids based on broken data makes things worse.

### Level 2: Are There Non-Media Root Causes?

The media is working correctly and you are measuring it correctly. But performance is still off. Before touching media levers, check whether external factors explain the change.

| Factor | Diagnostic |
|--------|-----------|
| Product/offer changes | Did pricing change? Did a feature launch fail? Did the product page change? These affect conversion rate independent of traffic quality. |
| Seasonality | Is this a historically low period? Compare to same period last year, not just last week. |
| Competitive pressure | Did a competitor launch a major campaign, undercut your pricing, or enter your market? |
| Market conditions | Macroeconomic shifts, regulatory changes, or industry events can suppress demand across all channels simultaneously. |
| Site/landing page issues | Page speed degradation, form breaks, mobile rendering issues — these affect all traffic equally. |

**If Level 2 identifies a root cause:** Communicate it clearly. Do not let a landing page bug get "fixed" by increasing ad spend.

### Level 3: Where in the Funnel Is the Breakdown?

The measurement is sound. There are no external factors. Now locate where in the conversion path the problem occurs.

| Stage | Metrics | What Degradation Means |
|-------|---------|----------------------|
| Impression delivery | Impressions, impression share, reach | Budget or bid constraints, audience saturation, or policy issues |
| Click/engagement | CTR, engagement rate | Ad creative fatigue, audience mismatch, or competitive ad pressure |
| Landing page | Bounce rate, time on page, scroll depth | Message mismatch between ad and page, UX issues, load time |
| Conversion | Conversion rate, form completion rate | Form friction, trust deficit, offer misalignment |
| Post-conversion | Lead quality, SQL rate, close rate | Traffic quality issue manifesting downstream |

**Key insight:** If CTR is stable but conversion rate dropped, the problem is downstream of the ad. If CTR dropped but conversion rate is stable, the problem is in the ad creative or targeting. If both dropped, look at Level 2 factors first.

### Level 4: What Specific Media Levers Are Underperforming?

Only after confirming Levels 1-3 should you diagnose specific media variables.

| Dimension | What to Check |
|-----------|--------------|
| Campaign type | Which campaigns degraded? Brand vs non-brand? Prospecting vs retargeting? |
| Audience segments | Which audiences are underperforming? New vs returning? Lookalike vs interest-based? |
| Geographic | Any geographic segments dragging down the average? |
| Device | Mobile vs desktop performance divergence? |
| Daypart | Performance shifting by time of day or day of week? |
| Creative | Which creatives are fatiguing? What is the frequency? |
| Keyword/placement | Specific keywords or placements with degraded performance? |

## Why This Ordering Matters

Teams that start at Level 4 — the most common behavior — waste time optimizing the wrong thing. Real examples of misdiagnosis:

- "Creative fatigue" that was actually a broken conversion tag after a site deploy
- "Audience saturation" that was actually a seasonal demand dip visible in Google Trends
- "Rising CPAs" that were actually a platform attribution window change
- "Declining lead quality" that was actually a form field change that let more unqualified leads through

Each of these was initially addressed with media changes (new creative, new audiences, bid increases, budget cuts). None of those interventions helped because the root cause was not in the media.

## Channel-Specific Patterns

### Paid Search
- Performance drops concentrated in brand terms usually indicate a competitive or organic issue, not a paid search issue
- Rising CPCs with stable conversion rates may mean increased auction competition, not poor account management
- Mobile vs desktop CPA divergence often reflects landing page issues, not bid strategy problems

### Paid Social
- Frequency above 3-4 in a 7-day window is the leading indicator of creative fatigue
- CPM increases with stable CTR mean the audience is getting more expensive, not that ads are performing worse
- Post-iOS attribution gaps mean in-platform conversions will always undercount — use server-side events or conversion lift studies

### Display/Programmatic
- Viewability issues inflate impression counts without real exposure
- Domain-level analysis catches fraud patterns that aggregate metrics hide
- Attribution is weakest here — test incrementality before trusting platform-reported conversions

## Usage

```bash
# Run diagnostic on campaign data
python diagnose.py --csv campaign_data.csv

# Specify the date range for comparison
python diagnose.py --csv campaign_data.csv --current-period 2025-03-01:2025-03-31 --prior-period 2025-02-01:2025-02-28

# Check specific diagnostic level only
python diagnose.py --csv campaign_data.csv --level 3

# JSON output for integration
python diagnose.py --csv campaign_data.csv --json-output
```

## Expected CSV Format

| Column | Description |
|--------|-------------|
| `date` | Date of the data row |
| `campaign` | Campaign name |
| `impressions` | Impression count |
| `clicks` | Click count |
| `cost` | Spend amount |
| `conversions` | Conversion count |

Optional columns for deeper diagnostics: `device`, `geo`, `ad_group`, `bounce_rate`, `conversion_value`.
