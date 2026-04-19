"""
UTM Taxonomy Validator

Validates UTM-tagged URLs against a controlled vocabulary to enforce
consistent marketing attribution across teams and platforms.
"""

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from urllib.parse import parse_qs, urlparse

# --- Default Taxonomy ---
# Override with --taxonomy flag pointing to a JSON file.

DEFAULT_TAXONOMY = {
    "required_params": ["utm_source", "utm_medium", "utm_campaign"],
    "allowed_values": {
        "utm_source": [
            "google",
            "facebook",
            "linkedin",
            "bing",
            "twitter",
            "instagram",
            "newsletter",
            "partner-site",
            "tiktok",
            "reddit",
            "email",
        ],
        "utm_medium": [
            "cpc",
            "cpm",
            "email",
            "organic-social",
            "paid-social",
            "referral",
            "display",
            "affiliate",
            "video",
            "retargeting",
        ],
    },
    "campaign_pattern": r"^[a-z0-9]+(-[a-z0-9]+)*$",
    "max_param_length": 100,
    "forbidden_characters": [" ", "|", ";", "{", "}", "<", ">"],
}


class Verdict(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


@dataclass
class ValidationIssue:
    parameter: str
    message: str
    severity: Verdict


@dataclass
class ValidationResult:
    url: str
    verdict: Verdict = Verdict.PASS
    issues: list = field(default_factory=list)

    def add_issue(self, param: str, message: str, severity: Verdict):
        self.issues.append(ValidationIssue(param, message, severity))
        if severity == Verdict.FAIL:
            self.verdict = Verdict.FAIL
        elif severity == Verdict.WARNING and self.verdict != Verdict.FAIL:
            self.verdict = Verdict.WARNING


def load_taxonomy(path: Optional[str]) -> dict:
    """Load taxonomy from JSON file or return default."""
    if path is None:
        return DEFAULT_TAXONOMY
    with open(path, "r") as f:
        return json.load(f)


def extract_utm_params(url: str) -> dict:
    """Parse URL and extract UTM parameters."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    return {k: v for k, v in query_params.items() if k.startswith("utm_")}


def validate_url(url: str, taxonomy: dict) -> ValidationResult:
    """Validate a single URL against the taxonomy."""
    result = ValidationResult(url=url)

    # Parse URL
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            result.add_issue("url", "Malformed URL: missing scheme or host", Verdict.FAIL)
            return result
    except Exception:
        result.add_issue("url", "Could not parse URL", Verdict.FAIL)
        return result

    utm_params = extract_utm_params(url)

    # Check for duplicate parameters (multiple values for same key)
    for param, values in utm_params.items():
        if len(values) > 1:
            result.add_issue(
                param,
                f"Duplicate parameter found ({len(values)} values: {values})",
                Verdict.FAIL,
            )

    # Flatten to single values for remaining checks
    flat_params = {k: v[0] for k, v in utm_params.items()}

    # Check required parameters
    for required in taxonomy.get("required_params", []):
        if required not in flat_params:
            result.add_issue(required, "Required parameter missing", Verdict.FAIL)
        elif not flat_params[required]:
            result.add_issue(required, "Parameter present but empty", Verdict.FAIL)

    # Validate each parameter
    allowed = taxonomy.get("allowed_values", {})
    campaign_pattern = taxonomy.get("campaign_pattern")
    max_length = taxonomy.get("max_param_length", 100)
    forbidden = taxonomy.get("forbidden_characters", [])

    for param, value in flat_params.items():
        if not value:
            continue

        # Case check — all values should be lowercase
        if value != value.lower():
            result.add_issue(
                param,
                f"Value '{value}' contains uppercase characters (should be '{value.lower()}')",
                Verdict.FAIL,
            )

        normalized = value.lower()

        # Vocabulary check for enumerated parameters
        if param in allowed:
            if normalized not in allowed[param]:
                result.add_issue(
                    param,
                    f"Value '{normalized}' not in allowed vocabulary: {allowed[param]}",
                    Verdict.FAIL,
                )

        # Campaign pattern check
        if param == "utm_campaign" and campaign_pattern:
            if not re.match(campaign_pattern, normalized):
                result.add_issue(
                    param,
                    f"Value '{normalized}' does not match campaign pattern: {campaign_pattern}",
                    Verdict.FAIL,
                )

        # Length check
        if len(value) > max_length:
            result.add_issue(
                param,
                f"Value length ({len(value)}) exceeds maximum ({max_length})",
                Verdict.WARNING,
            )

        # Forbidden character check
        for char in forbidden:
            if char in value:
                result.add_issue(
                    param,
                    f"Value contains forbidden character: '{char}'",
                    Verdict.FAIL,
                )

    return result


def validate_csv(filepath: str, url_column: str, taxonomy: dict) -> list:
    """Validate all URLs in a CSV file."""
    results = []
    with open(filepath, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if url_column not in reader.fieldnames:
            print(f"Error: Column '{url_column}' not found. Available: {reader.fieldnames}")
            sys.exit(1)
        for row in reader:
            url = row[url_column].strip()
            if url:
                results.append(validate_url(url, taxonomy))
    return results


def print_results(results: list):
    """Print validation results in a readable format."""
    counts = {Verdict.PASS: 0, Verdict.FAIL: 0, Verdict.WARNING: 0}

    for r in results:
        counts[r.verdict] += 1
        status = r.verdict.value
        print(f"\n[{status}] {r.url}")
        for issue in r.issues:
            marker = "  !!" if issue.severity == Verdict.FAIL else "  --"
            print(f"{marker} {issue.parameter}: {issue.message}")

    print("\n" + "=" * 60)
    print(f"Total: {len(results)}  |  "
          f"PASS: {counts[Verdict.PASS]}  |  "
          f"FAIL: {counts[Verdict.FAIL]}  |  "
          f"WARNING: {counts[Verdict.WARNING]}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Validate UTM parameters against a controlled taxonomy.")
    parser.add_argument("--url", help="Single URL to validate")
    parser.add_argument("--csv", help="Path to CSV file containing URLs")
    parser.add_argument("--url-column", default="url", help="Column name containing URLs (default: 'url')")
    parser.add_argument("--taxonomy", help="Path to taxonomy JSON file (uses default if omitted)")
    parser.add_argument("--json-output", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    if not args.url and not args.csv:
        parser.print_help()
        print("\nError: Provide either --url or --csv")
        sys.exit(1)

    taxonomy = load_taxonomy(args.taxonomy)

    if args.url:
        results = [validate_url(args.url, taxonomy)]
    else:
        results = validate_csv(args.csv, args.url_column, taxonomy)

    if args.json_output:
        output = []
        for r in results:
            output.append({
                "url": r.url,
                "verdict": r.verdict.value,
                "issues": [
                    {"parameter": i.parameter, "message": i.message, "severity": i.severity.value}
                    for i in r.issues
                ],
            })
        print(json.dumps(output, indent=2))
    else:
        print_results(results)

    # Exit with non-zero if any failures
    if any(r.verdict == Verdict.FAIL for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
