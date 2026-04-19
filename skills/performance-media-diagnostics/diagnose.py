"""
Performance Media Diagnostics

Structured diagnostic framework for isolating paid media performance
issues. Follows a four-level diagnostic tree:
  1. Measurement integrity
  2. Non-media root causes
  3. Funnel stage breakdown
  4. Media lever analysis
"""

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CampaignRow:
    date: str
    campaign: str
    impressions: int
    clicks: int
    cost: float
    conversions: float
    device: str = ""
    geo: str = ""
    ad_group: str = ""
    bounce_rate: Optional[float] = None
    conversion_value: float = 0.0


@dataclass
class DiagnosticFinding:
    level: int
    check: str
    status: str  # OK, WARNING, ISSUE
    detail: str
    recommendation: str = ""


@dataclass
class DiagnosticReport:
    findings: list = field(default_factory=list)

    def add(self, level: int, check: str, status: str, detail: str, recommendation: str = ""):
        self.findings.append(DiagnosticFinding(level, check, status, detail, recommendation))

    @property
    def has_issues(self) -> bool:
        return any(f.status == "ISSUE" for f in self.findings)


def safe_int(value: str) -> int:
    try:
        return int(float(value.replace(",", "").strip()))
    except (ValueError, AttributeError):
        return 0


def safe_float(value: str) -> float:
    try:
        return float(value.replace(",", "").replace("$", "").strip())
    except (ValueError, AttributeError):
        return 0.0


def safe_float_or_none(value: str) -> Optional[float]:
    try:
        v = value.replace(",", "").replace("%", "").strip()
        return float(v) if v else None
    except (ValueError, AttributeError):
        return None


def parse_date(value: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def read_campaign_data(filepath: str) -> list:
    """Read campaign performance CSV."""
    rows = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        for row in reader:
            rows.append(CampaignRow(
                date=row.get("date", "").strip(),
                campaign=row.get("campaign", "").strip(),
                impressions=safe_int(row.get("impressions", "0")),
                clicks=safe_int(row.get("clicks", "0")),
                cost=safe_float(row.get("cost", "0")),
                conversions=safe_float(row.get("conversions", "0")),
                device=row.get("device", "").strip(),
                geo=row.get("geo", "").strip(),
                ad_group=row.get("ad_group", "").strip(),
                bounce_rate=safe_float_or_none(row.get("bounce_rate", "")),
                conversion_value=safe_float(row.get("conversion_value", "0")),
            ))
    return rows


def split_periods(rows: list, current_spec: Optional[str], prior_spec: Optional[str]) -> tuple:
    """Split rows into current and prior periods for comparison."""
    if current_spec and prior_spec:
        curr_start, curr_end = current_spec.split(":")
        prior_start, prior_end = prior_spec.split(":")
        cs, ce = parse_date(curr_start), parse_date(curr_end)
        ps, pe = parse_date(prior_start), parse_date(prior_end)

        current = [r for r in rows if cs and ce and cs <= (parse_date(r.date) or datetime.min) <= ce]
        prior = [r for r in rows if ps and pe and ps <= (parse_date(r.date) or datetime.min) <= pe]
    else:
        # Auto-split: sort by date, split in half
        dated_rows = [(parse_date(r.date), r) for r in rows if parse_date(r.date)]
        dated_rows.sort(key=lambda x: x[0])
        mid = len(dated_rows) // 2
        prior = [r for _, r in dated_rows[:mid]]
        current = [r for _, r in dated_rows[mid:]]

    return current, prior


def aggregate(rows: list) -> dict:
    """Aggregate metrics for a set of rows."""
    if not rows:
        return {"impressions": 0, "clicks": 0, "cost": 0, "conversions": 0, "days": 0}

    dates = set(r.date for r in rows)
    return {
        "impressions": sum(r.impressions for r in rows),
        "clicks": sum(r.clicks for r in rows),
        "cost": sum(r.cost for r in rows),
        "conversions": sum(r.conversions for r in rows),
        "days": len(dates),
        "ctr": sum(r.clicks for r in rows) / max(sum(r.impressions for r in rows), 1),
        "cvr": sum(r.conversions for r in rows) / max(sum(r.clicks for r in rows), 1),
        "cpa": sum(r.cost for r in rows) / max(sum(r.conversions for r in rows), 0.001),
        "cpc": sum(r.cost for r in rows) / max(sum(r.clicks for r in rows), 1),
    }


def pct_change(current: float, prior: float) -> Optional[float]:
    """Calculate percentage change."""
    if prior == 0:
        return None
    return (current - prior) / prior


def run_level_1(current: list, prior: list, report: DiagnosticReport):
    """Level 1: Measurement integrity checks."""

    # Check for conversion lag — are the last few days systematically lower?
    daily_conv = defaultdict(float)
    for r in current:
        daily_conv[r.date] += r.conversions

    if len(daily_conv) >= 5:
        sorted_dates = sorted(daily_conv.keys())
        last_3 = [daily_conv[d] for d in sorted_dates[-3:]]
        prior_days = [daily_conv[d] for d in sorted_dates[:-3]]
        if prior_days:
            avg_recent = sum(last_3) / len(last_3)
            avg_prior = sum(prior_days) / len(prior_days)
            if avg_prior > 0 and avg_recent / avg_prior < 0.5:
                report.add(1, "Conversion lag",  "ISSUE",
                    f"Last 3 days average {avg_recent:.1f} conversions vs "
                    f"prior average {avg_prior:.1f} — likely conversion lag",
                    "Wait 3-7 days before concluding performance dropped. "
                    "Check platform conversion lag settings.")
            else:
                report.add(1, "Conversion lag", "OK", "No systematic recency drop detected")
    else:
        report.add(1, "Conversion lag", "OK", "Insufficient data for lag check")

    # Check for tracking gaps — days with impressions but zero conversions
    zero_conv_days = []
    for date, conv in daily_conv.items():
        day_impr = sum(r.impressions for r in current if r.date == date)
        if day_impr > 100 and conv == 0:
            zero_conv_days.append(date)

    if zero_conv_days:
        report.add(1, "Tracking gaps", "ISSUE",
            f"{len(zero_conv_days)} days with significant impressions but zero conversions: "
            f"{zero_conv_days[:5]}",
            "Investigate conversion tag implementation. Check for site deploys on these dates.")
    else:
        report.add(1, "Tracking gaps", "OK", "No days with suspicious zero-conversion patterns")

    # Check for sudden volume changes (possible bot traffic)
    daily_clicks = defaultdict(int)
    for r in current:
        daily_clicks[r.date] += r.clicks

    if len(daily_clicks) >= 4:
        values = list(daily_clicks.values())
        if len(values) >= 4:
            mean_clicks = statistics.mean(values)
            stdev_clicks = statistics.stdev(values) if len(values) > 1 else 0
            if stdev_clicks > 0:
                spikes = [d for d, v in daily_clicks.items() if v > mean_clicks + 3 * stdev_clicks]
                if spikes:
                    report.add(1, "Traffic anomaly", "WARNING",
                        f"Click volume spikes detected on {spikes[:3]} "
                        f"(>{3}σ above mean of {mean_clicks:.0f})",
                        "Check for bot traffic or click fraud. Review source/placement reports.")
                else:
                    report.add(1, "Traffic anomaly", "OK", "No unusual click volume spikes")


def run_level_2(current: list, prior: list, report: DiagnosticReport):
    """Level 2: Non-media root causes."""
    curr_agg = aggregate(current)
    prior_agg = aggregate(prior)

    # Check if all campaigns are affected equally (suggests external cause)
    campaign_changes = {}
    for campaign in set(r.campaign for r in current):
        curr_camp = [r for r in current if r.campaign == campaign]
        prior_camp = [r for r in prior if r.campaign == campaign]
        if prior_camp:
            curr_cvr = sum(r.conversions for r in curr_camp) / max(sum(r.clicks for r in curr_camp), 1)
            prior_cvr = sum(r.conversions for r in prior_camp) / max(sum(r.clicks for r in prior_camp), 1)
            if prior_cvr > 0:
                campaign_changes[campaign] = (curr_cvr - prior_cvr) / prior_cvr

    if campaign_changes:
        all_negative = all(v < -0.1 for v in campaign_changes.values())
        if all_negative:
            avg_decline = statistics.mean(campaign_changes.values())
            report.add(2, "Uniform decline", "ISSUE",
                f"All campaigns show CVR decline (avg {avg_decline:.1%}). "
                "This pattern suggests a non-media root cause.",
                "Check: landing page changes, site speed, competitive moves, "
                "seasonal patterns, product/pricing changes.")
        else:
            declining = [k for k, v in campaign_changes.items() if v < -0.1]
            improving = [k for k, v in campaign_changes.items() if v > 0.1]
            report.add(2, "Campaign variation", "OK",
                f"Mixed performance: {len(declining)} declining, {len(improving)} improving. "
                "Suggests campaign-specific issues, not external factors.")

    # Seasonality indicator — compare day-of-week patterns
    dow_current = defaultdict(list)
    dow_prior = defaultdict(list)
    for r in current:
        d = parse_date(r.date)
        if d:
            dow_current[d.strftime("%A")].append(r.conversions)
    for r in prior:
        d = parse_date(r.date)
        if d:
            dow_prior[d.strftime("%A")].append(r.conversions)

    if dow_current and dow_prior:
        report.add(2, "Day-of-week pattern", "OK",
            "Day-of-week data available for manual seasonality review")


def run_level_3(current: list, prior: list, report: DiagnosticReport):
    """Level 3: Funnel stage breakdown."""
    curr_agg = aggregate(current)
    prior_agg = aggregate(prior)

    # Impression delivery
    impr_change = pct_change(curr_agg["impressions"], prior_agg["impressions"])
    if impr_change is not None:
        if impr_change < -0.2:
            report.add(3, "Impression delivery", "ISSUE",
                f"Impressions down {impr_change:.1%} period-over-period",
                "Check budget pacing, bid constraints, audience size, and policy issues.")
        elif impr_change < -0.05:
            report.add(3, "Impression delivery", "WARNING",
                f"Impressions down {impr_change:.1%}", "Monitor for continued decline.")
        else:
            report.add(3, "Impression delivery", "OK",
                f"Impressions {'up' if impr_change >= 0 else 'down'} {abs(impr_change):.1%}")

    # CTR (click-through)
    ctr_change = pct_change(curr_agg["ctr"], prior_agg["ctr"])
    if ctr_change is not None:
        if ctr_change < -0.15:
            report.add(3, "Click-through rate", "ISSUE",
                f"CTR down {ctr_change:.1%} ({prior_agg['ctr']:.2%} -> {curr_agg['ctr']:.2%})",
                "Investigate ad creative fatigue, audience mismatch, or increased competitive ad pressure.")
        else:
            report.add(3, "Click-through rate", "OK",
                f"CTR {'up' if ctr_change >= 0 else 'down'} {abs(ctr_change):.1%} "
                f"({curr_agg['ctr']:.2%})")

    # Conversion rate
    cvr_change = pct_change(curr_agg["cvr"], prior_agg["cvr"])
    if cvr_change is not None:
        if cvr_change < -0.15:
            report.add(3, "Conversion rate", "ISSUE",
                f"CVR down {cvr_change:.1%} ({prior_agg['cvr']:.2%} -> {curr_agg['cvr']:.2%})",
                "Check landing page changes, form functionality, offer alignment, and page speed.")
        else:
            report.add(3, "Conversion rate", "OK",
                f"CVR {'up' if cvr_change >= 0 else 'down'} {abs(cvr_change):.1%} "
                f"({curr_agg['cvr']:.2%})")

    # CPA
    cpa_change = pct_change(curr_agg["cpa"], prior_agg["cpa"])
    if cpa_change is not None:
        if cpa_change > 0.2:
            report.add(3, "Cost per acquisition", "ISSUE",
                f"CPA up {cpa_change:.1%} (${prior_agg['cpa']:,.2f} -> ${curr_agg['cpa']:,.2f})",
                "Determine if driven by CTR decline (creative), CVR decline (landing page), "
                "or CPC increase (auction competition).")
        else:
            report.add(3, "Cost per acquisition", "OK",
                f"CPA {'up' if cpa_change >= 0 else 'down'} {abs(cpa_change):.1%} "
                f"(${curr_agg['cpa']:,.2f})")

    # Diagnostic pattern identification
    if ctr_change is not None and cvr_change is not None:
        if ctr_change < -0.1 and cvr_change > -0.05:
            report.add(3, "Pattern", "WARNING",
                "CTR declining while CVR is stable — problem is in the ad, not the landing page.",
                "Focus on creative refresh and audience targeting.")
        elif ctr_change > -0.05 and cvr_change < -0.1:
            report.add(3, "Pattern", "WARNING",
                "CTR stable while CVR is declining — problem is downstream of the ad.",
                "Focus on landing page, form, offer, and page speed.")
        elif ctr_change < -0.1 and cvr_change < -0.1:
            report.add(3, "Pattern", "WARNING",
                "Both CTR and CVR declining — likely a systemic issue.",
                "Revisit Level 2: check for non-media root causes before optimizing media.")


def run_level_4(current: list, prior: list, report: DiagnosticReport):
    """Level 4: Specific media lever analysis."""

    # Campaign-level breakdown
    campaign_metrics = defaultdict(lambda: {"curr": [], "prior": []})
    for r in current:
        campaign_metrics[r.campaign]["curr"].append(r)
    for r in prior:
        campaign_metrics[r.campaign]["prior"].append(r)

    underperformers = []
    for campaign, data in campaign_metrics.items():
        if data["curr"] and data["prior"]:
            curr_cpa = sum(r.cost for r in data["curr"]) / max(sum(r.conversions for r in data["curr"]), 0.001)
            prior_cpa = sum(r.cost for r in data["prior"]) / max(sum(r.conversions for r in data["prior"]), 0.001)
            change = pct_change(curr_cpa, prior_cpa)
            if change and change > 0.25:
                underperformers.append((campaign, change, curr_cpa))

    if underperformers:
        underperformers.sort(key=lambda x: x[1], reverse=True)
        top_3 = underperformers[:3]
        detail = "; ".join([f"'{c}' CPA up {ch:.0%} (${cpa:,.2f})" for c, ch, cpa in top_3])
        report.add(4, "Campaign breakdown", "ISSUE", f"Top underperformers: {detail}",
            "Drill into these campaigns for creative, audience, and bid diagnostics.")
    else:
        report.add(4, "Campaign breakdown", "OK", "No campaigns with CPA increase >25%")

    # Device breakdown (if available)
    devices = set(r.device for r in current if r.device)
    if devices:
        for device in devices:
            curr_dev = [r for r in current if r.device == device]
            prior_dev = [r for r in prior if r.device == device]
            if curr_dev and prior_dev:
                curr_cvr = sum(r.conversions for r in curr_dev) / max(sum(r.clicks for r in curr_dev), 1)
                prior_cvr = sum(r.conversions for r in prior_dev) / max(sum(r.clicks for r in prior_dev), 1)
                change = pct_change(curr_cvr, prior_cvr)
                if change and change < -0.2:
                    report.add(4, f"Device: {device}", "WARNING",
                        f"CVR down {change:.1%} on {device}",
                        f"Check {device}-specific landing page experience.")

    # Geographic breakdown (if available)
    geos = set(r.geo for r in current if r.geo)
    if len(geos) > 1:
        geo_issues = []
        for geo in geos:
            curr_geo = [r for r in current if r.geo == geo]
            prior_geo = [r for r in prior if r.geo == geo]
            if curr_geo and prior_geo:
                curr_cpa = sum(r.cost for r in curr_geo) / max(sum(r.conversions for r in curr_geo), 0.001)
                prior_cpa = sum(r.cost for r in prior_geo) / max(sum(r.conversions for r in prior_geo), 0.001)
                change = pct_change(curr_cpa, prior_cpa)
                if change and change > 0.3:
                    geo_issues.append((geo, change))

        if geo_issues:
            detail = ", ".join([f"{g} (CPA +{c:.0%})" for g, c in sorted(geo_issues, key=lambda x: x[1], reverse=True)[:3]])
            report.add(4, "Geographic breakdown", "WARNING",
                f"Underperforming geos: {detail}",
                "Consider geo-specific bid adjustments or exclusions.")


def print_report(report: DiagnosticReport):
    """Print the diagnostic report."""
    print("=" * 70)
    print("PERFORMANCE MEDIA DIAGNOSTIC REPORT")
    print("=" * 70)

    for level in [1, 2, 3, 4]:
        level_findings = [f for f in report.findings if f.level == level]
        if not level_findings:
            continue

        labels = {
            1: "Measurement Integrity",
            2: "Non-Media Root Causes",
            3: "Funnel Stage Breakdown",
            4: "Media Lever Analysis",
        }
        print(f"\nLEVEL {level}: {labels[level]}")
        print("-" * 50)

        for f in level_findings:
            icon = {"OK": "  [OK]", "WARNING": "  [!!]", "ISSUE": "  [XX]"}[f.status]
            print(f"{icon} {f.check}: {f.detail}")
            if f.recommendation and f.status != "OK":
                print(f"       -> {f.recommendation}")

    # Summary
    issues = [f for f in report.findings if f.status == "ISSUE"]
    warnings = [f for f in report.findings if f.status == "WARNING"]
    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {len(issues)} issues, {len(warnings)} warnings")

    if issues:
        # Find the highest-priority level with issues
        issue_levels = sorted(set(f.level for f in issues))
        top_level = issue_levels[0]
        print(f"\nPrimary diagnosis at Level {top_level}. "
              f"{'Resolve measurement issues before optimizing media.' if top_level == 1 else ''}"
              f"{'Address root causes before adjusting campaigns.' if top_level == 2 else ''}"
              f"{'Focus optimization on the identified funnel stage.' if top_level == 3 else ''}"
              f"{'Optimize specific underperforming segments.' if top_level == 4 else ''}")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Performance media diagnostic framework.")
    parser.add_argument("--csv", required=True, help="Path to campaign performance CSV")
    parser.add_argument("--current-period", help="Current period as YYYY-MM-DD:YYYY-MM-DD")
    parser.add_argument("--prior-period", help="Prior period as YYYY-MM-DD:YYYY-MM-DD")
    parser.add_argument("--level", type=int, choices=[1, 2, 3, 4], help="Run specific diagnostic level only")
    parser.add_argument("--json-output", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    rows = read_campaign_data(args.csv)
    if not rows:
        print("No data found in CSV.")
        sys.exit(1)

    current, prior = split_periods(rows, args.current_period, args.prior_period)

    if not current:
        print("Error: No rows in current period.")
        sys.exit(1)
    if not prior:
        print("Warning: No prior period data — some comparisons will be skipped.")

    report = DiagnosticReport()

    levels_to_run = [args.level] if args.level else [1, 2, 3, 4]

    level_funcs = {
        1: run_level_1,
        2: run_level_2,
        3: run_level_3,
        4: run_level_4,
    }

    for level in levels_to_run:
        level_funcs[level](current, prior, report)

    if args.json_output:
        output = {
            "current_period_rows": len(current),
            "prior_period_rows": len(prior),
            "findings": [
                {
                    "level": f.level,
                    "check": f.check,
                    "status": f.status,
                    "detail": f.detail,
                    "recommendation": f.recommendation,
                }
                for f in report.findings
            ],
            "issue_count": sum(1 for f in report.findings if f.status == "ISSUE"),
            "warning_count": sum(1 for f in report.findings if f.status == "WARNING"),
        }
        print(json.dumps(output, indent=2))
    else:
        print_report(report)

    if report.has_issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
