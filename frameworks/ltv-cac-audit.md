# LTV/CAC Audit Methodology

A structured approach to auditing unit economics models. LTV/CAC is the most important ratio in growth marketing — and the most commonly miscalculated. This methodology catches the errors before they reach a board deck or budget decision.

## Why This Audit Exists

Most LTV/CAC models are built in spreadsheets. Spreadsheets are powerful and fragile. A single broken formula, a hardcoded assumption that someone forgot to update, or a data pull that silently returned partial results can make the ratio look healthy when it is not — or alarming when the business is fine.

The audit is not about questioning the business. It is about questioning the math.

---

## Audit Structure

### 1. Formula Integrity

Start with the formulas themselves. Do they compute what they claim to compute?

**LTV formula check:**

| Component | What to Verify |
|-----------|---------------|
| Average revenue per user | Is this calculated from the correct revenue field? Does it include or exclude discounts, refunds, and credits consistently? |
| Gross margin | Is the margin applied to LTV or just to revenue? Many models calculate LTV on revenue then compare to fully-loaded CAC. This overstates the ratio. |
| Retention/churn rate | Is churn calculated as a cohort-based rate or a blended rate? Blended rates mask cohort-level deterioration. |
| Discount rate | Is future revenue discounted to present value? For long LTV windows (3+ years), this matters significantly. |
| Time horizon | Is LTV calculated to infinity (1/churn) or capped at a realistic horizon? Infinite LTV calculations are theoretically valid but practically misleading for businesses with evolving retention curves. |

**CAC formula check:**

| Component | What to Verify |
|-----------|---------------|
| Spend numerator | Does it include all acquisition costs? Media spend, agency fees, creative production, landing page development, sales team allocation? |
| Customer denominator | Is the denominator new customers only, or does it include reactivations and expansions? Mixing these deflates CAC artificially. |
| Time alignment | Is spend from the same period as the customers it generated? A January campaign that converts customers in March should not have its cost attributed to March acquisitions. |
| Channel allocation | If calculating channel-level CAC, is overhead allocated or excluded? Either is valid, but it must be consistent. |

**Common spreadsheet errors:**

| Error | How It Manifests |
|-------|-----------------|
| IFERROR hiding problems | `IFERROR(A/B, 0)` silently returns 0 when B is zero instead of surfacing a division error. This makes the model look clean while hiding missing data. |
| Hardcoded values | A cell that should reference a data source but instead contains a typed number from three quarters ago. |
| Circular references | Retention rate depends on LTV, and LTV depends on retention rate. Excel may "resolve" this with iterative calculation, producing unstable results. |
| Mixed periodicity | Monthly churn rate used in a formula that expects annual churn. A 5% monthly churn rate is not 60% annual — it is 46%. |
| Incorrect absolute/relative references | A formula that works in row 2 but breaks when dragged to row 50 because a reference was not anchored. |

---

### 2. Data Completeness

The formulas are correct. Now check whether they are operating on complete data.

**Revenue data:**
- Are all revenue sources included? Subscription revenue is obvious; implementation fees, upsells, and expansion revenue are often in separate systems.
- Are refunds and chargebacks netted out?
- Is revenue recognized at booking or at payment? The choice matters for LTV calculation.

**Cost data:**
- Is spend data pulled from the source of truth (ad platform, finance system) or from a secondary report?
- Are all channels represented? A "total CAC" that excludes organic acquisition costs is a "paid CAC" — label it accordingly.
- Are there time gaps? A missing month of spend data will make that month's CAC look zero.

**Customer data:**
- Is the customer count deduplicated? CRM duplicates inflate the denominator and deflate CAC.
- Are trial/freemium users excluded from the paying customer count (or included intentionally)?
- Is the customer creation date accurate? CRM migration artifacts often set all historical customers to the migration date.

---

### 3. Anomaly Detection

The formulas are correct, the data is complete. Now look for values that do not make sense.

**Red flags in LTV:**
- LTV that increased quarter-over-quarter while churn also increased. These cannot both be true unless ARPU increased enough to offset churn — verify.
- LTV/CAC ratio above 5:1. This is either a very efficient business or a model error. At ratios this high, you should be spending more on acquisition.
- Negative LTV. This means the customer costs more to serve than they pay. Possible, but worth verifying the margin calculation.
- LTV that is exactly the same across all cohorts. Real cohorts have variance. Identical LTV suggests a hardcoded value or a formula that does not vary by cohort.

**Red flags in CAC:**
- CAC of zero for any channel. This means either no spend (possible for organic) or missing data.
- CAC that drops sharply in a single month. Usually indicates a data pull issue, not a real efficiency gain.
- Blended CAC that is lower than every individual channel CAC. Mathematically impossible — check the weighting.
- Paid CAC that is lower than blended CAC. This means organic acquisition is being counted in the denominator but organic costs are not in the numerator.

**Red flags in the ratio:**
- LTV/CAC improving while absolute customer count is declining. This often means you are acquiring fewer but "better" customers — which may be a sign of market contraction, not efficiency.
- Dramatic period-over-period swings (e.g., 2.5 to 4.0 in one quarter). Stable businesses do not see this. Check for data issues before celebrating.

---

### 4. Cohort-Level Validation

Aggregate LTV/CAC masks cohort-level problems. Always check cohorts.

| Check | What It Catches |
|-------|----------------|
| Cohort maturity | Are you comparing a 12-month-old cohort's LTV to a 3-month-old cohort's projected LTV? The projection adds uncertainty. |
| Retention curve shape | Is the retention curve flattening (good) or still declining steeply (the LTV estimate is premature)? |
| Cohort-over-cohort trend | Are newer cohorts retaining better or worse than older ones? A deteriorating trend means your aggregate LTV is overstated because it includes legacy cohorts with better retention. |
| Channel-level cohorts | Does LTV vary by acquisition channel? It almost always does. A blended LTV applied to channel-specific CAC produces misleading channel-level ratios. |

---

### 5. Remediation Priority

When the audit surfaces issues, prioritize fixes by impact on the ratio.

| Priority | Issue Type | Action |
|----------|-----------|--------|
| P0 | Formula errors that change the ratio by >20% | Fix immediately. Communicate the corrected ratio to stakeholders before the next use. |
| P1 | Data completeness gaps that affect numerator or denominator | Identify the missing data source, establish a pull, and recalculate. |
| P2 | Methodology inconsistencies (e.g., mixing blended and channel-level) | Standardize the methodology and document the definitions. Recalculate historical periods for comparability. |
| P3 | Anomalies that require investigation but may be legitimate | Flag for review. Do not change the model until the anomaly is understood. |

---

## Audit Checklist

Use this as a pre-flight check before presenting LTV/CAC to stakeholders.

- [ ] LTV formula references live data, not hardcoded values
- [ ] Churn rate is cohort-based, not blended (or blended is explicitly labeled)
- [ ] Gross margin is applied consistently (to LTV, not just revenue)
- [ ] CAC includes all acquisition costs (media, agency, creative, sales allocation)
- [ ] CAC denominator is new customers only (or expansion is explicitly labeled)
- [ ] Spend and customer counts are time-aligned
- [ ] No IFERROR wrappers hiding division-by-zero on critical calculations
- [ ] Cohort-level view shows consistent or improving trends
- [ ] Ratio is within plausible bounds for the industry (typically 3:1 to 5:1 for healthy SaaS)
- [ ] Model has been recalculated with current data within the last 30 days

---

## Common Pitfalls

**"Our LTV/CAC is 8:1, we should spend more."** Maybe. But first check whether LTV is calculated on a 5-year horizon with a generous retention assumption, and CAC excludes brand spend. The real ratio may be closer to 3:1.

**"Channel X has the best CAC."** Channel X may also have the worst LTV. Always look at channel-level LTV/CAC, not just CAC in isolation.

**"LTV/CAC improved this quarter."** Did LTV increase (good) or did CAC decrease because you pulled back spend (potentially bad — you may be under-investing in growth)?

**"We do not need to audit this — the model has not changed."** The model has not changed, but the data feeding it has. Every quarter, data sources shift, definitions drift, and new edge cases appear. Audit the inputs even when the formula is stable.
