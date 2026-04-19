"""
Funnel Data Validator

Three-tier validation of conversion funnel data:
  Tier 1 — Structural integrity (encoding, columns, nulls, duplicates)
  Tier 2 — Schema and funnel logic (stage ordering, rate bounds, plausibility)
  Tier 3 — Cross-source integrity (attribution sums, conversion lag)
"""

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Verdict(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


@dataclass
class Check:
    name: str
    verdict: Verdict
    detail: str


@dataclass
class TierResult:
    tier: int
    label: str
    checks: list = field(default_factory=list)

    @property
    def verdict(self) -> Verdict:
        if any(c.verdict == Verdict.FAIL for c in self.checks):
            return Verdict.FAIL
        if any(c.verdict == Verdict.WARNING for c in self.checks):
            return Verdict.WARNING
        if all(c.verdict == Verdict.SKIPPED for c in self.checks):
            return Verdict.SKIPPED
        return Verdict.PASS


# --- Default Configuration ---

DEFAULT_STAGES = ["impressions", "clicks", "leads", "qualified", "opportunities", "closed"]
REQUIRED_COLUMNS = ["date"]  # stages are added dynamically
CONVERSION_RATE_FLOOR = 0.001  # 0.1% — below this is suspicious
CONVERSION_RATE_CEILING = 0.95  # 95% — above this is suspicious
TEMPORAL_SPIKE_THRESHOLD = 5.0  # 5x day-over-day is flagged
NULL_RATE_THRESHOLD = 0.05  # more than 5% nulls in a column is a problem


def read_csv(filepath: str) -> tuple:
    """Read CSV and return (headers, rows). Handles BOM."""
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            rows = list(reader)
        return headers, rows, None
    except UnicodeDecodeError:
        # Try latin-1 fallback
        try:
            with open(filepath, "r", encoding="latin-1") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                rows = list(reader)
            return headers, rows, "WARNING: File is Latin-1 encoded, not UTF-8"
        except Exception as e:
            return [], [], f"Cannot read file: {e}"
    except Exception as e:
        return [], [], f"Cannot read file: {e}"


def run_tier_1(headers: list, rows: list, stages: list, encoding_note: str) -> TierResult:
    """Tier 1: Structural integrity checks."""
    tier = TierResult(tier=1, label="Structural Integrity")

    # Encoding check
    if encoding_note and "WARNING" in encoding_note:
        tier.checks.append(Check("File encoding", Verdict.WARNING, encoding_note))
    elif encoding_note:
        tier.checks.append(Check("File encoding", Verdict.FAIL, encoding_note))
    else:
        tier.checks.append(Check("File encoding", Verdict.PASS, "UTF-8"))

    # Required columns
    required = REQUIRED_COLUMNS + stages
    missing = [c for c in required if c not in headers]
    if missing:
        tier.checks.append(Check(
            "Required columns", Verdict.FAIL,
            f"Missing columns: {missing}. Available: {headers}"
        ))
    else:
        tier.checks.append(Check("Required columns", Verdict.PASS, "All present"))

    # Empty dataset
    if not rows:
        tier.checks.append(Check("Row count", Verdict.FAIL, "No data rows found"))
        return tier
    else:
        tier.checks.append(Check("Row count", Verdict.PASS, f"{len(rows)} rows"))

    # Null checks per stage column
    for col in stages:
        if col not in headers:
            continue
        null_count = sum(1 for r in rows if not r.get(col) or r[col].strip() == "")
        null_rate = null_count / len(rows)
        if null_rate > NULL_RATE_THRESHOLD:
            tier.checks.append(Check(
                f"Null rate ({col})", Verdict.FAIL,
                f"{null_rate:.1%} null ({null_count}/{len(rows)})"
            ))
        elif null_count > 0:
            tier.checks.append(Check(
                f"Null rate ({col})", Verdict.WARNING,
                f"{null_rate:.1%} null ({null_count}/{len(rows)})"
            ))

    # Duplicate detection
    row_tuples = [tuple(sorted(r.items())) for r in rows]
    counts = Counter(row_tuples)
    duplicates = sum(v - 1 for v in counts.values() if v > 1)
    if duplicates > 0:
        tier.checks.append(Check(
            "Duplicate rows", Verdict.FAIL,
            f"{duplicates} exact duplicate rows found"
        ))
    else:
        tier.checks.append(Check("Duplicate rows", Verdict.PASS, "No duplicates"))

    # Date parsing
    date_col = "date"
    if date_col in headers:
        bad_dates = 0
        for r in rows:
            val = r.get(date_col, "").strip()
            parsed = False
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d", "%d-%m-%Y"):
                try:
                    datetime.strptime(val, fmt)
                    parsed = True
                    break
                except ValueError:
                    continue
            if not parsed:
                bad_dates += 1
        if bad_dates > 0:
            tier.checks.append(Check(
                "Date parsing", Verdict.FAIL,
                f"{bad_dates} rows with unparseable dates"
            ))
        else:
            tier.checks.append(Check("Date parsing", Verdict.PASS, "All dates parseable"))

    return tier


def safe_float(value: str) -> Optional[float]:
    """Convert string to float, return None on failure."""
    try:
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def run_tier_2(rows: list, stages: list) -> TierResult:
    """Tier 2: Schema and funnel logic checks."""
    tier = TierResult(tier=2, label="Schema & Funnel Logic")

    # Stage ordering — aggregate totals, each stage should be <= previous
    stage_totals = {}
    for stage in stages:
        values = [safe_float(r.get(stage, "")) for r in rows]
        values = [v for v in values if v is not None]
        stage_totals[stage] = sum(values)

    ordering_ok = True
    for i in range(1, len(stages)):
        prev_stage = stages[i - 1]
        curr_stage = stages[i]
        if stage_totals.get(curr_stage, 0) > stage_totals.get(prev_stage, 0):
            tier.checks.append(Check(
                "Stage ordering", Verdict.FAIL,
                f"'{curr_stage}' ({stage_totals[curr_stage]:,.0f}) > "
                f"'{prev_stage}' ({stage_totals[prev_stage]:,.0f})"
            ))
            ordering_ok = False

    if ordering_ok:
        tier.checks.append(Check("Stage ordering", Verdict.PASS, "Monotonically decreasing"))

    # Conversion rate bounds
    for i in range(1, len(stages)):
        prev_total = stage_totals.get(stages[i - 1], 0)
        curr_total = stage_totals.get(stages[i], 0)
        if prev_total > 0:
            rate = curr_total / prev_total
            label = f"{stages[i - 1]} -> {stages[i]}"
            if rate > 1.0:
                tier.checks.append(Check(
                    f"Conversion rate ({label})", Verdict.FAIL,
                    f"Rate is {rate:.1%} (> 100%)"
                ))
            elif rate > CONVERSION_RATE_CEILING:
                tier.checks.append(Check(
                    f"Conversion rate ({label})", Verdict.WARNING,
                    f"Unusually high rate: {rate:.1%}"
                ))
            elif rate < CONVERSION_RATE_FLOOR:
                tier.checks.append(Check(
                    f"Conversion rate ({label})", Verdict.WARNING,
                    f"Unusually low rate: {rate:.2%}"
                ))

    # Negative values
    negative_found = False
    for stage in stages:
        for r in rows:
            val = safe_float(r.get(stage, ""))
            if val is not None and val < 0:
                if not negative_found:
                    tier.checks.append(Check(
                        "Negative values", Verdict.FAIL,
                        f"Negative value found in '{stage}' (row date: {r.get('date', '?')})"
                    ))
                    negative_found = True

    if not negative_found:
        tier.checks.append(Check("Negative values", Verdict.PASS, "No negative values"))

    # Temporal spikes (day-over-day for top-of-funnel)
    top_stage = stages[0]
    daily_values = []
    for r in rows:
        val = safe_float(r.get(top_stage, ""))
        if val is not None:
            daily_values.append(val)

    spike_found = False
    for i in range(1, len(daily_values)):
        if daily_values[i - 1] > 0:
            ratio = daily_values[i] / daily_values[i - 1]
            if ratio > TEMPORAL_SPIKE_THRESHOLD or (ratio > 0 and 1 / ratio > TEMPORAL_SPIKE_THRESHOLD):
                tier.checks.append(Check(
                    "Temporal consistency", Verdict.WARNING,
                    f"Day-over-day spike of {ratio:.1f}x in '{top_stage}' at row {i + 1}"
                ))
                spike_found = True
                break

    if not spike_found:
        tier.checks.append(Check("Temporal consistency", Verdict.PASS, "No anomalous spikes"))

    return tier


def run_tier_3(rows: list, stages: list) -> TierResult:
    """Tier 3: Cross-source integrity checks."""
    tier = TierResult(tier=3, label="Cross-Source Integrity")

    has_source = "source" in (rows[0].keys() if rows else [])

    if not has_source:
        tier.checks.append(Check(
            "Attribution check", Verdict.SKIPPED,
            "No 'source' column found — cannot check attribution"
        ))
        return tier

    # Attribution sum check — do source subtotals match the total?
    for stage in stages:
        source_totals = {}
        grand_total = 0
        for r in rows:
            val = safe_float(r.get(stage, ""))
            if val is None:
                continue
            source = r.get("source", "unknown")
            source_totals[source] = source_totals.get(source, 0) + val
            grand_total += val

        source_sum = sum(source_totals.values())
        if grand_total > 0:
            ratio = source_sum / grand_total
            if abs(ratio - 1.0) > 0.01:
                tier.checks.append(Check(
                    f"Attribution sum ({stage})", Verdict.WARNING,
                    f"Source sum is {ratio:.1%} of grand total "
                    f"({source_sum:,.0f} vs {grand_total:,.0f})"
                ))

    # Conversion lag detection — are the last 3 dates systematically lower?
    date_values = {}
    top_stage = stages[0]
    for r in rows:
        date_str = r.get("date", "")
        val = safe_float(r.get(top_stage, ""))
        if val is not None and date_str:
            date_values[date_str] = date_values.get(date_str, 0) + val

    if len(date_values) >= 7:
        sorted_dates = sorted(date_values.keys())
        recent_3 = [date_values[d] for d in sorted_dates[-3:]]
        prior_4 = [date_values[d] for d in sorted_dates[-7:-3]]
        avg_recent = sum(recent_3) / len(recent_3) if recent_3 else 0
        avg_prior = sum(prior_4) / len(prior_4) if prior_4 else 0
        if avg_prior > 0 and avg_recent / avg_prior < 0.5:
            tier.checks.append(Check(
                "Conversion lag", Verdict.WARNING,
                f"Last 3 dates average {avg_recent:,.0f} vs prior 4 dates average "
                f"{avg_prior:,.0f} — possible conversion lag"
            ))
        else:
            tier.checks.append(Check("Conversion lag", Verdict.PASS, "No lag detected"))
    else:
        tier.checks.append(Check(
            "Conversion lag", Verdict.SKIPPED,
            "Insufficient date range for lag detection (need 7+ dates)"
        ))

    if not any(c.verdict != Verdict.SKIPPED for c in tier.checks):
        tier.checks.append(Check("Cross-source", Verdict.PASS, "No issues found"))

    return tier


def print_report(tiers: list):
    """Print the full validation report."""
    for tier_result in tiers:
        print(f"\nTIER {tier_result.tier} — {tier_result.label}")
        if tier_result.verdict == Verdict.SKIPPED and not tier_result.checks:
            print("  (skipped — prior tier failures must be resolved first)")
            continue
        for check in tier_result.checks:
            print(f"  [{check.verdict.value}] {check.name}: {check.detail}")

    # Overall verdict
    all_verdicts = [t.verdict for t in tiers if t.verdict != Verdict.SKIPPED]
    if Verdict.FAIL in all_verdicts:
        overall = "FAIL"
    elif Verdict.WARNING in all_verdicts:
        overall = "PASS WITH CAVEATS"
    else:
        overall = "PASS"

    print(f"\n{'=' * 60}")
    print(f"VERDICT: {overall}")

    # Collect caveats
    if overall == "PASS WITH CAVEATS":
        warnings = [
            c for t in tiers for c in t.checks if c.verdict == Verdict.WARNING
        ]
        if warnings:
            print("Caveats:")
            for w in warnings:
                print(f"  - {w.name}: {w.detail}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Three-tier funnel data validation.")
    parser.add_argument("--csv", required=True, help="Path to funnel data CSV")
    parser.add_argument(
        "--stages",
        default=",".join(DEFAULT_STAGES),
        help="Comma-separated funnel stages in order (default: impressions,clicks,leads,qualified,opportunities,closed)",
    )
    parser.add_argument("--json-output", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    stages = [s.strip() for s in args.stages.split(",")]

    # Read data
    headers, rows, encoding_note = read_csv(args.csv)
    if not headers and encoding_note:
        print(f"FATAL: {encoding_note}")
        sys.exit(1)

    # Run tiers sequentially — each depends on the previous passing
    tier1 = run_tier_1(headers, rows, stages, encoding_note)
    tiers = [tier1]

    if tier1.verdict == Verdict.FAIL:
        # Create skipped placeholders for tier 2 and 3
        tier2 = TierResult(tier=2, label="Schema & Funnel Logic")
        tier3 = TierResult(tier=3, label="Cross-Source Integrity")
        tiers.extend([tier2, tier3])
    else:
        tier2 = run_tier_2(rows, stages)
        tiers.append(tier2)

        if tier2.verdict == Verdict.FAIL:
            tier3 = TierResult(tier=3, label="Cross-Source Integrity")
            tiers.append(tier3)
        else:
            tier3 = run_tier_3(rows, stages)
            tiers.append(tier3)

    if args.json_output:
        output = []
        for t in tiers:
            output.append({
                "tier": t.tier,
                "label": t.label,
                "verdict": t.verdict.value,
                "checks": [
                    {"name": c.name, "verdict": c.verdict.value, "detail": c.detail}
                    for c in t.checks
                ],
            })
        print(json.dumps(output, indent=2))
    else:
        print_report(tiers)

    if any(t.verdict == Verdict.FAIL for t in tiers):
        sys.exit(1)


if __name__ == "__main__":
    main()
