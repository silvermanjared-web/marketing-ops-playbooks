"""
Negative Keyword Builder

Classifies search terms from paid search query reports by theme,
evaluates performance per theme, and recommends negative keywords
with appropriate match types and application levels.
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


# --- Default Theme Definitions ---
# Each theme has a name, keyword patterns, and a default negation level.

DEFAULT_THEMES = [
    {
        "name": "Job Seekers",
        "patterns": [
            r"\bjobs?\b", r"\bcareers?\b", r"\bhiring\b", r"\bsalary\b",
            r"\binterview\b", r"\bresume\b", r"\brecruit", r"\bemployment\b",
            r"\bglassdoor\b", r"\bindeed\b", r"\blinkedin\b",
        ],
        "level": "account",
        "match_type": "phrase",
    },
    {
        "name": "Free / DIY",
        "patterns": [
            r"\bfree\b", r"\bopen.?source\b", r"\bdiy\b", r"\btemplate\b",
            r"\bdownload\b", r"\bpdf\b", r"\btutorial\b",
        ],
        "level": "account",
        "match_type": "phrase",
    },
    {
        "name": "Educational / Informational",
        "patterns": [
            r"\bwhat is\b", r"\bhow to\b", r"\bdefinition\b", r"\bwiki\b",
            r"\bmeaning\b", r"\bexplain\b", r"\bexample\b", r"\bguide\b",
        ],
        "level": "campaign",
        "match_type": "phrase",
    },
    {
        "name": "Price Sensitive",
        "patterns": [
            r"\bcheap\b", r"\bdiscount\b", r"\bcoupon\b", r"\bfree shipping\b",
            r"\bbargain\b", r"\baffordable\b", r"\bbudget\b", r"\bdeal\b",
        ],
        "level": "campaign",
        "match_type": "phrase",
    },
    {
        "name": "Competitor Research",
        "patterns": [
            r"\bvs\.?\b", r"\balternative\b", r"\bcompare\b", r"\bcomparison\b",
            r"\breview\b", r"\brating\b", r"\bbetter than\b",
        ],
        "level": "review",
        "match_type": "exact",
    },
    {
        "name": "Wrong Intent",
        "patterns": [
            r"\blogin\b", r"\bsign in\b", r"\bcancel\b", r"\brefund\b",
            r"\bcustomer service\b", r"\bsupport\b", r"\bphone number\b",
        ],
        "level": "account",
        "match_type": "phrase",
    },
]


@dataclass
class TermRecord:
    search_term: str
    campaign: str
    ad_group: str
    impressions: int
    clicks: int
    cost: float
    conversions: float


@dataclass
class ThemeResult:
    name: str
    level: str
    match_type: str
    terms: list = field(default_factory=list)
    total_impressions: int = 0
    total_clicks: int = 0
    total_cost: float = 0
    total_conversions: float = 0

    @property
    def ctr(self) -> float:
        return self.total_clicks / self.total_impressions if self.total_impressions > 0 else 0

    @property
    def cvr(self) -> float:
        return self.total_conversions / self.total_clicks if self.total_clicks > 0 else 0

    @property
    def cpa(self) -> Optional[float]:
        return self.total_cost / self.total_conversions if self.total_conversions > 0 else None

    def add_term(self, record: TermRecord):
        self.terms.append(record)
        self.total_impressions += record.impressions
        self.total_clicks += record.clicks
        self.total_cost += record.cost
        self.total_conversions += record.conversions


def safe_int(value: str) -> int:
    try:
        return int(float(value.replace(",", "").strip()))
    except (ValueError, AttributeError):
        return 0


def safe_float(value: str) -> float:
    try:
        cleaned = value.replace(",", "").replace("$", "").strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0


def load_themes(rules_path: Optional[str]) -> list:
    """Load theme definitions from JSON or use defaults."""
    if rules_path:
        with open(rules_path, "r") as f:
            return json.load(f)
    return DEFAULT_THEMES


def read_search_terms(filepath: str) -> list:
    """Read search term report CSV."""
    records = []
    # Map common column name variations
    column_map = {
        "search_term": ["search_term", "search term", "query", "Search term"],
        "campaign": ["campaign", "Campaign", "campaign_name"],
        "ad_group": ["ad_group", "ad group", "Ad group", "ad_group_name"],
        "impressions": ["impressions", "Impressions", "impr"],
        "clicks": ["clicks", "Clicks"],
        "cost": ["cost", "Cost", "spend", "Spend"],
        "conversions": ["conversions", "Conversions", "conv"],
    }

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        # Resolve column names
        resolved = {}
        for standard, variants in column_map.items():
            for v in variants:
                if v in headers:
                    resolved[standard] = v
                    break

        missing = [k for k in column_map if k not in resolved]
        if missing:
            print(f"Warning: Could not find columns: {missing}")
            print(f"Available columns: {headers}")

        for row in reader:
            records.append(TermRecord(
                search_term=row.get(resolved.get("search_term", ""), "").strip().lower(),
                campaign=row.get(resolved.get("campaign", ""), ""),
                ad_group=row.get(resolved.get("ad_group", ""), ""),
                impressions=safe_int(row.get(resolved.get("impressions", ""), "0")),
                clicks=safe_int(row.get(resolved.get("clicks", ""), "0")),
                cost=safe_float(row.get(resolved.get("cost", ""), "0")),
                conversions=safe_float(row.get(resolved.get("conversions", ""), "0")),
            ))

    return records


def classify_terms(records: list, themes: list, min_spend: float, min_impressions: int) -> tuple:
    """Classify search terms by theme and return results + unclassified terms."""
    theme_results = {}
    for theme in themes:
        theme_results[theme["name"]] = ThemeResult(
            name=theme["name"],
            level=theme.get("level", "campaign"),
            match_type=theme.get("match_type", "phrase"),
        )

    classified_terms = set()
    unclassified = []

    for record in records:
        # Skip low-volume terms
        if record.cost < min_spend and record.impressions < min_impressions:
            continue

        matched = False
        for theme in themes:
            for pattern in theme["patterns"]:
                if re.search(pattern, record.search_term, re.IGNORECASE):
                    theme_results[theme["name"]].add_term(record)
                    classified_terms.add(record.search_term)
                    matched = True
                    break
            if matched:
                break

        if not matched:
            unclassified.append(record)

    return theme_results, unclassified


def extract_negative_keywords(theme_result: ThemeResult) -> list:
    """Extract the most impactful negative keyword candidates from a theme."""
    # Find common words/phrases across terms in this theme
    word_freq = defaultdict(lambda: {"count": 0, "cost": 0.0, "conversions": 0.0})

    for term in theme_result.terms:
        words = term.search_term.split()
        # Single words
        for w in words:
            if len(w) > 2:  # skip very short words
                word_freq[w]["count"] += 1
                word_freq[w]["cost"] += term.cost
                word_freq[w]["conversions"] += term.conversions
        # Bigrams
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i + 1]}"
            word_freq[bigram]["count"] += 1
            word_freq[bigram]["cost"] += term.cost
            word_freq[bigram]["conversions"] += term.conversions

    # Rank by spend on zero-conversion keywords first, then by frequency
    ranked = sorted(
        word_freq.items(),
        key=lambda x: (x[1]["conversions"] == 0, x[1]["cost"], x[1]["count"]),
        reverse=True,
    )

    # Return top keywords, preferring zero-conversion high-spend
    negatives = []
    for word, stats in ranked[:10]:
        negatives.append({
            "keyword": word,
            "match_type": theme_result.match_type,
            "frequency": stats["count"],
            "associated_cost": round(stats["cost"], 2),
            "associated_conversions": stats["conversions"],
        })

    return negatives


def determine_recommendation(theme_result: ThemeResult) -> str:
    """Determine whether to negate, review, or keep a theme."""
    if theme_result.total_conversions == 0 and theme_result.total_cost > 0:
        return "NEGATE"
    elif theme_result.total_conversions > 0 and theme_result.cpa and theme_result.cpa > 0:
        return "REVIEW"
    elif not theme_result.terms:
        return "NO DATA"
    else:
        return "KEEP"


def print_results(theme_results: dict, unclassified: list):
    """Print classification results."""
    print("=" * 70)
    print("NEGATIVE KEYWORD ANALYSIS")
    print("=" * 70)

    for name, result in theme_results.items():
        if not result.terms:
            continue

        recommendation = determine_recommendation(result)
        print(f"\nTHEME: {result.name}")
        print(f"  Queries matched: {len(result.terms)}")
        print(f"  Total spend: ${result.total_cost:,.2f}")
        print(f"  Total conversions: {result.total_conversions:,.1f}")
        if result.cpa:
            print(f"  CPA: ${result.cpa:,.2f}")
        print(f"  Recommended action: {recommendation}")

        if recommendation == "NEGATE":
            print(f"  Level: {result.level}")
            print(f"  Match type: {result.match_type}")
            negatives = extract_negative_keywords(result)
            if negatives:
                print("  Suggested negatives:")
                for neg in negatives:
                    print(f'    - "{neg["keyword"]}" ({neg["match_type"]}) '
                          f'[${neg["associated_cost"]:,.2f} spend, {neg["associated_conversions"]:.0f} conv]')
        elif recommendation == "REVIEW":
            print(f"  Note: Theme converts but may be inefficient. Manual review recommended.")

    # Unclassified high-spend terms
    high_spend_unclassified = sorted(unclassified, key=lambda x: x.cost, reverse=True)[:20]
    if high_spend_unclassified:
        print(f"\nUNCLASSIFIED HIGH-SPEND TERMS (top 20)")
        for term in high_spend_unclassified:
            conv_label = f"{term.conversions:.0f} conv" if term.conversions > 0 else "0 conv"
            print(f'  "${term.search_term}" — ${term.cost:,.2f} spend, {conv_label}')

    print(f"\n{'=' * 70}")


def export_negatives(theme_results: dict, filepath: str):
    """Export negative keyword recommendations as CSV for platform upload."""
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["keyword", "match_type", "level", "theme", "associated_cost", "associated_conversions"])
        for name, result in theme_results.items():
            recommendation = determine_recommendation(result)
            if recommendation == "NEGATE":
                negatives = extract_negative_keywords(result)
                for neg in negatives:
                    writer.writerow([
                        neg["keyword"],
                        neg["match_type"],
                        result.level,
                        result.name,
                        neg["associated_cost"],
                        neg["associated_conversions"],
                    ])
    print(f"Negatives exported to {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Classify search terms and build negative keyword lists.")
    parser.add_argument("--csv", required=True, help="Path to search term report CSV")
    parser.add_argument("--rules", help="Path to custom theme rules JSON")
    parser.add_argument("--min-spend", type=float, default=5.0, help="Minimum spend to evaluate a term (default: $5)")
    parser.add_argument("--min-impressions", type=int, default=10, help="Minimum impressions to evaluate (default: 10)")
    parser.add_argument("--export", help="Export negatives to CSV file")
    parser.add_argument("--json-output", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    themes = load_themes(args.rules)
    records = read_search_terms(args.csv)

    if not records:
        print("No search term records found.")
        sys.exit(1)

    theme_results, unclassified = classify_terms(records, themes, args.min_spend, args.min_impressions)

    if args.json_output:
        output = {}
        for name, result in theme_results.items():
            if not result.terms:
                continue
            output[name] = {
                "query_count": len(result.terms),
                "total_cost": round(result.total_cost, 2),
                "total_conversions": result.total_conversions,
                "cpa": round(result.cpa, 2) if result.cpa else None,
                "recommendation": determine_recommendation(result),
                "level": result.level,
                "negatives": extract_negative_keywords(result),
            }
        print(json.dumps(output, indent=2))
    else:
        print_results(theme_results, unclassified)

    if args.export:
        export_negatives(theme_results, args.export)


if __name__ == "__main__":
    main()
