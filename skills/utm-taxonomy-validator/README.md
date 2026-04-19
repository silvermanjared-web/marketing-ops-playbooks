# UTM Taxonomy Validator

## Why This Matters

UTM parameters are the connective tissue between marketing spend and analytics. When they break — and they break constantly — you lose attribution, your channel reports diverge from reality, and every downstream decision inherits that error.

The root cause is almost never technical. It is organizational. Thirty people across five teams tagging URLs with no shared vocabulary. `google` vs `Google` vs `adwords` vs `google-ads`. `cpc` vs `paid` vs `ppc`. Every variation is a new "source" in your analytics, fragmenting data that should be unified.

A controlled vocabulary enforced at the point of URL creation is the only reliable fix. This validator implements that enforcement.

## The Five UTM Parameters

| Parameter | Controls | Example |
|-----------|----------|---------|
| `utm_source` | Where traffic comes from — the platform or property | `google`, `facebook`, `newsletter` |
| `utm_medium` | How it gets to you — the marketing channel | `cpc`, `email`, `organic-social` |
| `utm_campaign` | Why you are sending it — the initiative or offer | `spring-sale-2025`, `brand-awareness-q1` |
| `utm_term` | What keyword triggered it (primarily paid search) | `running+shoes`, `project+management+software` |
| `utm_content` | Which creative variant (for A/B testing) | `hero-banner-v2`, `sidebar-cta` |

`utm_source` and `utm_medium` are the most critical. If these are inconsistent, your channel-level reporting is unreliable. `utm_campaign` is the next priority — it ties spend to outcomes.

## Controlled Vocabulary

The validator checks UTM parameters against a defined set of allowed values. This is the core concept: rather than validating format alone, you maintain a canonical list of what each parameter can be.

**Example vocabulary:**

```yaml
source:
  - google
  - facebook
  - linkedin
  - bing
  - newsletter
  - partner-site

medium:
  - cpc
  - cpm
  - email
  - organic-social
  - paid-social
  - referral
  - display
  - affiliate

campaign_pattern: "^[a-z0-9]+(-[a-z0-9]+)*$"
```

Sources and mediums are enumerated. Campaign names follow a pattern (lowercase, hyphen-separated). This prevents the entropy that accumulates when naming is discretionary.

## Common Failure Modes

**Inconsistent casing.** `Google` vs `google` vs `GOOGLE`. Analytics platforms treat these as three different sources. The validator normalizes to lowercase and flags the original.

**Ad-hoc naming.** Someone creates `utm_medium=social` instead of the canonical `paid-social` or `organic-social`. Now "social" is a phantom channel in your reports that cannot be tied to spend.

**URL encoding artifacts.** Spaces become `+` or `%20`. Pipes, ampersands, and special characters in campaign names break URL parsing entirely. The validator checks for characters that will cause downstream issues.

**Missing required parameters.** A URL tagged with `utm_source` but no `utm_medium` will attribute to the right source but the wrong channel. The validator enforces which parameters are required together.

**Parameter pollution.** Multiple `utm_source` values in the same URL (from redirect chains or incorrect tagging) produce unpredictable analytics behavior. The validator catches duplicate parameters.

## How the Validator Works

1. **Parse** — Extract UTM parameters from the URL query string
2. **Required fields** — Confirm all mandatory parameters are present (`source`, `medium`, `campaign` at minimum)
3. **Vocabulary check** — Compare each parameter value against the allowed list
4. **Format validation** — Check for encoding issues, invalid characters, excessive length
5. **Duplicate detection** — Flag URLs with repeated UTM parameters

### Output

Each URL receives a verdict:

- **PASS** — All parameters present, all values in vocabulary, no format issues
- **FAIL** — Missing required parameters or values outside the controlled vocabulary
- **WARNING** — Parameters present and valid, but with minor issues (unusual length, uncommon but allowed values)

## Usage

```bash
# Validate a single URL
python validate.py --url "https://example.com?utm_source=google&utm_medium=cpc&utm_campaign=spring-sale"

# Validate a CSV of URLs
python validate.py --csv urls.csv --url-column "landing_page_url"

# Use a custom taxonomy
python validate.py --csv urls.csv --taxonomy my_taxonomy.yaml
```

## When to Run This

- **Before launch** — Validate every URL in a campaign brief before it goes live
- **Weekly audit** — Pull tagged URLs from your ad platforms and validate retroactively
- **In CI/CD** — If your team generates landing pages or redirect rules programmatically, run this as a check
- **After migrations** — Platform migrations and CMS changes frequently break UTM persistence
