"""
Data Sanity Checker

Pre-flight data quality checks for marketing datasets. Catches nulls,
duplicates, type inconsistencies, temporal gaps, metric outliers, and
cross-source anomalies before data reaches analysis or reporting.
"""

import argparse
import csv
import json
import statistics
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


class Severity:
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Finding:
    category: str
    check: str
    severity: str
    detail: str


@dataclass
class Report:
    filename: str
    findings: list = field(default_factory=list)
    row_count: int = 0
    column_count: int = 0

    def add(self, category: str, check: str, severity: str, detail: str):
        self.findings.append(Finding(category, check, severity, detail))

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.WARNING)


def read_data(filepath: str) -> tuple:
    """Read CSV file, return (headers, rows, error)."""
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            rows = list(reader)
        return headers, rows, None
    except UnicodeDecodeError:
        try:
            with open(filepath, "r", encoding="latin-1") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                rows = list(reader)
            return headers, rows, "latin-1"
        except Exception as e:
            return [], [], str(e)
    except Exception as e:
        return [], [], str(e)


def is_numeric(value: str) -> bool:
    """Check if a string value is numeric."""
    try:
        float(value.replace(",", "").strip())
        return True
    except (ValueError, AttributeError):
        return False


def to_float(value: str) -> Optional[float]:
    """Convert to float or return None."""
    try:
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def parse_date(value: str) -> Optional[datetime]:
    """Try common date formats."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def run_structural_checks(
    headers: list, rows: list, report: Report, null_threshold: float, encoding_issue: Optional[str]
):
    """Category 1: Structural checks."""
    cat = "Structural"

    if encoding_issue:
        report.add(cat, "Encoding", Severity.WARNING, f"File encoded as {encoding_issue}, not UTF-8")
    else:
        report.add(cat, "Encoding", Severity.INFO, "UTF-8")

    report.row_count = len(rows)
    report.column_count = len(headers)
    report.add(cat, "Shape", Severity.INFO, f"{len(rows)} rows x {len(headers)} columns")

    if not rows:
        report.add(cat, "Empty dataset", Severity.CRITICAL, "No data rows found")
        return

    # Null rates
    for col in headers:
        values = [r.get(col, "") for r in rows]
        null_count = sum(1 for v in values if not v or v.strip() == "")
        null_rate = null_count / len(rows) if rows else 0
        if null_rate > null_threshold:
            report.add(
                cat, f"Null rate ({col})", Severity.CRITICAL,
                f"{null_rate:.1%} null ({null_count}/{len(rows)})"
            )
        elif null_count > 0:
            report.add(
                cat, f"Null rate ({col})", Severity.INFO,
                f"{null_rate:.1%} null ({null_count}/{len(rows)})"
            )

    # Duplicate rows
    row_tuples = [tuple(sorted(r.items())) for r in rows]
    counts = Counter(row_tuples)
    dupes = sum(v - 1 for v in counts.values() if v > 1)
    if dupes > 0:
        report.add(cat, "Duplicate rows", Severity.CRITICAL, f"{dupes} exact duplicates")
    else:
        report.add(cat, "Duplicate rows", Severity.INFO, "None")

    # Data type consistency per column
    for col in headers:
        values = [r.get(col, "").strip() for r in rows if r.get(col, "").strip()]
        if not values:
            continue
        numeric_count = sum(1 for v in values if is_numeric(v))
        numeric_rate = numeric_count / len(values)
        # If a column is mostly numeric but has some non-numeric values, flag it
        if 0.5 < numeric_rate < 1.0:
            non_numeric = len(values) - numeric_count
            report.add(
                cat, f"Type consistency ({col})", Severity.WARNING,
                f"Column is {numeric_rate:.0%} numeric with {non_numeric} non-numeric values"
            )


def run_temporal_checks(headers: list, rows: list, report: Report):
    """Category 2: Temporal checks."""
    cat = "Temporal"

    # Find date column
    date_col = None
    for candidate in ["date", "Date", "DATE", "day", "report_date"]:
        if candidate in headers:
            date_col = candidate
            break

    if date_col is None:
        report.add(cat, "Date column", Severity.INFO, "No date column detected — skipping temporal checks")
        return

    # Parse dates
    dates = []
    bad_dates = 0
    for r in rows:
        d = parse_date(r.get(date_col, ""))
        if d:
            dates.append(d)
        else:
            bad_dates += 1

    if bad_dates > 0:
        report.add(cat, "Unparseable dates", Severity.WARNING, f"{bad_dates} rows with unparseable dates")

    if len(dates) < 2:
        report.add(cat, "Date range", Severity.INFO, "Insufficient dates for temporal analysis")
        return

    dates_sorted = sorted(set(dates))
    report.add(
        cat, "Date range", Severity.INFO,
        f"{dates_sorted[0].strftime('%Y-%m-%d')} to {dates_sorted[-1].strftime('%Y-%m-%d')} ({len(dates_sorted)} unique dates)"
    )

    # Gap detection (assuming daily data)
    expected_dates = set()
    d = dates_sorted[0]
    while d <= dates_sorted[-1]:
        expected_dates.add(d)
        d += timedelta(days=1)

    actual_dates = set(dates_sorted)
    missing = expected_dates - actual_dates
    if missing:
        # Filter out weekends for a softer check
        weekday_missing = [d for d in missing if d.weekday() < 5]
        if weekday_missing:
            report.add(
                cat, "Date gaps", Severity.WARNING,
                f"{len(weekday_missing)} missing weekday dates (total gaps including weekends: {len(missing)})"
            )
        else:
            report.add(cat, "Date gaps", Severity.INFO, f"{len(missing)} weekend-only gaps")
    else:
        report.add(cat, "Date gaps", Severity.INFO, "No gaps")

    # Recency check
    most_recent = dates_sorted[-1]
    now = datetime.now()
    days_old = (now - most_recent).days
    if days_old > 7:
        report.add(cat, "Recency", Severity.WARNING, f"Most recent data is {days_old} days old")
    else:
        report.add(cat, "Recency", Severity.INFO, f"Most recent: {most_recent.strftime('%Y-%m-%d')}")


def run_metric_checks(headers: list, rows: list, report: Report, outlier_sigma: float):
    """Category 3: Metric checks."""
    cat = "Metric"

    # Identify numeric columns
    numeric_cols = []
    for col in headers:
        values = [r.get(col, "").strip() for r in rows if r.get(col, "").strip()]
        if values and sum(1 for v in values if is_numeric(v)) / len(values) > 0.9:
            numeric_cols.append(col)

    if not numeric_cols:
        report.add(cat, "Numeric columns", Severity.INFO, "No numeric columns detected")
        return

    for col in numeric_cols:
        values = [to_float(r.get(col, "")) for r in rows]
        values = [v for v in values if v is not None]
        if not values:
            continue

        # Negative values
        neg_count = sum(1 for v in values if v < 0)
        if neg_count > 0:
            report.add(cat, f"Negative values ({col})", Severity.WARNING, f"{neg_count} negative values")

        # Zero prevalence
        zero_count = sum(1 for v in values if v == 0)
        zero_rate = zero_count / len(values)
        if zero_rate > 0.8:
            report.add(
                cat, f"Zero prevalence ({col})", Severity.WARNING,
                f"{zero_rate:.0%} of values are zero"
            )

        # Outlier detection
        if len(values) >= 10:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
            if stdev > 0:
                outliers = [v for v in values if abs(v - mean) > outlier_sigma * stdev]
                if outliers:
                    report.add(
                        cat, f"Outliers ({col})", Severity.WARNING,
                        f"{len(outliers)} values beyond {outlier_sigma} sigma "
                        f"(mean={mean:,.2f}, stdev={stdev:,.2f}, max outlier={max(outliers, key=lambda x: abs(x - mean)):,.2f})"
                    )

        # Range check for rate-like columns
        col_lower = col.lower()
        if any(kw in col_lower for kw in ["rate", "ctr", "cvr", "conversion_rate"]):
            over_100 = [v for v in values if v > 1.0]
            if over_100:
                report.add(
                    cat, f"Rate bounds ({col})", Severity.CRITICAL,
                    f"{len(over_100)} values > 100% (assuming decimal format)"
                )


def print_report(report: Report):
    """Print findings grouped by category."""
    categories = []
    seen = set()
    for f in report.findings:
        if f.category not in seen:
            categories.append(f.category)
            seen.add(f.category)

    for cat in categories:
        print(f"\n{cat.upper()} CHECKS")
        for f in report.findings:
            if f.category == cat:
                print(f"  [{f.severity}] {f.check}: {f.detail}")

    print(f"\n{'=' * 60}")
    if report.critical_count > 0:
        print(f"VERDICT: FAIL ({report.critical_count} critical, {report.warning_count} warnings)")
    elif report.warning_count > 0:
        print(f"VERDICT: REVIEW NEEDED ({report.warning_count} warnings)")
    else:
        print("VERDICT: CLEAN")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Pre-flight data sanity checks.")
    parser.add_argument("--file", required=True, help="Path to CSV file")
    parser.add_argument("--null-threshold", type=float, default=0.05, help="Null rate threshold for critical flag (default: 0.05)")
    parser.add_argument("--outlier-sigma", type=float, default=3.0, help="Sigma threshold for outlier detection (default: 3.0)")
    parser.add_argument("--json-output", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    headers, rows, read_error = read_data(args.file)

    if not headers and read_error and read_error not in ("latin-1",):
        print(f"FATAL: Cannot read file — {read_error}")
        sys.exit(1)

    encoding_issue = read_error if read_error == "latin-1" else None

    report = Report(filename=args.file)

    run_structural_checks(headers, rows, report, args.null_threshold, encoding_issue)
    if rows:
        run_temporal_checks(headers, rows, report)
        run_metric_checks(headers, rows, report, args.outlier_sigma)

    if args.json_output:
        output = {
            "file": report.filename,
            "rows": report.row_count,
            "columns": report.column_count,
            "critical_count": report.critical_count,
            "warning_count": report.warning_count,
            "findings": [
                {
                    "category": f.category,
                    "check": f.check,
                    "severity": f.severity,
                    "detail": f.detail,
                }
                for f in report.findings
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print_report(report)

    if report.critical_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
