#!/usr/bin/env python3
"""
Merge Path A and Path B enrichment outputs.

This script merges companies_enriched_path_a.csv and companies_enriched_path_b.csv
into a single companies_enriched.csv file for downstream processing.

Part of Phase 3 (Issue #19) from V4.3 work plan.

Usage:
    python3 merge_enrichment_outputs.py

Author: Bay Area Biotech Map V4.3
Date: 2025-11-16
"""

import csv
import sys
from pathlib import Path
from collections import OrderedDict

# ============================================================================
# Configuration
# ============================================================================

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
WORKING_DIR = DATA_DIR / "working"

PATH_A_FILE = WORKING_DIR / "companies_enriched_path_a.csv"
PATH_B_FILE = WORKING_DIR / "companies_enriched_path_b.csv"
OUTPUT_FILE = WORKING_DIR / "companies_enriched.csv"


# ============================================================================
# Merge Logic
# ============================================================================

def load_csv(file_path: Path) -> list:
    """
    Load CSV file into list of dicts.

    Args:
        file_path: Path to CSV file

    Returns:
        List of row dicts
    """
    if not file_path.exists():
        return []

    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows


def deduplicate_companies(companies: list) -> list:
    """
    Deduplicate companies by Company Name.

    If duplicates exist, prefer:
    1. Row with higher Confidence
    2. Row with more complete data (non-empty fields)
    3. First occurrence

    Args:
        companies: List of company dicts

    Returns:
        Deduplicated list
    """
    # Group by company name (case-insensitive)
    by_name = {}

    for company in companies:
        name = company.get('Company Name', '').strip()
        if not name:
            continue

        name_key = name.lower()

        if name_key not in by_name:
            by_name[name_key] = company
        else:
            # Compare with existing
            existing = by_name[name_key]

            # Prefer higher confidence (check both Confidence and Confidence_Det)
            existing_conf = float(existing.get('Confidence', existing.get('Confidence_Det', '0.0')) or '0.0')
            new_conf = float(company.get('Confidence', company.get('Confidence_Det', '0.0')) or '0.0')

            if new_conf > existing_conf:
                by_name[name_key] = company
            elif new_conf == existing_conf:
                # Prefer more complete data
                existing_fields = sum(1 for v in existing.values() if v and v.strip())
                new_fields = sum(1 for v in company.values() if v and v.strip())

                if new_fields > existing_fields:
                    by_name[name_key] = company

    # Return deduplicated list (preserve original order as much as possible)
    seen_names = set()
    deduplicated = []

    for company in companies:
        name = company.get('Company Name', '').strip()
        if not name:
            continue

        name_key = name.lower()
        if name_key not in seen_names:
            deduplicated.append(by_name[name_key])
            seen_names.add(name_key)

    return deduplicated


def normalize_fields(companies: list) -> list:
    """
    Normalize field names and ensure all companies have same schema.

    Standard fields:
    - Company Name
    - Website
    - City
    - Address
    - Company Stage (empty for now)
    - Focus Areas (empty for now)
    - Validation_Source (PathA or PathB)
    - Place_ID
    - Confidence (or Confidence_Det)
    - Validation_Reason (PathA) or Validation_JSON (PathB)

    Args:
        companies: List of company dicts

    Returns:
        Normalized list
    """
    normalized = []

    for company in companies:
        # Map Confidence_Det to Confidence if needed
        confidence = company.get('Confidence', company.get('Confidence_Det', ''))

        # Map Validation_Reason to notes if PathA
        validation_source = company.get('Validation_Source', '')
        if validation_source == 'PathA':
            validation_notes = company.get('Validation_Reason', '')
        else:
            validation_notes = company.get('Validation_JSON', '')

        normalized_row = OrderedDict([
            ('Company Name', company.get('Company Name', '')),
            ('Website', company.get('Website', '')),
            ('City', company.get('City', '')),
            ('Address', company.get('Address', '')),
            ('Company Stage', company.get('Company Stage', '')),
            ('Focus Areas', company.get('Focus Areas', '')),
            ('Validation_Source', validation_source),
            ('Place_ID', company.get('Place_ID', '')),
            ('Confidence', confidence),
            ('Validation_Notes', validation_notes)
        ])

        normalized.append(normalized_row)

    return normalized


# ============================================================================
# Main
# ============================================================================

def main():
    """Main merge workflow."""
    print("=" * 70)
    print("Merge Path A and Path B Enrichment Outputs")
    print("=" * 70)
    print()

    # Load Path A
    print(f"Loading Path A from: {PATH_A_FILE}")
    path_a_companies = load_csv(PATH_A_FILE)
    print(f"  Loaded {len(path_a_companies)} Path A companies")

    # Load Path B
    print(f"Loading Path B from: {PATH_B_FILE}")
    path_b_companies = load_csv(PATH_B_FILE)
    print(f"  Loaded {len(path_b_companies)} Path B companies")

    if not path_a_companies and not path_b_companies:
        print()
        print("Error: No companies found in either Path A or Path B outputs")
        print("Run enrich_with_google_maps.py and path_b_enrichment.py first")
        sys.exit(1)

    print()

    # Combine
    all_companies = path_a_companies + path_b_companies
    print(f"Combined: {len(all_companies)} total companies")

    # Deduplicate
    print("Deduplicating by Company Name...")
    deduplicated = deduplicate_companies(all_companies)
    duplicates_removed = len(all_companies) - len(deduplicated)
    print(f"  Removed {duplicates_removed} duplicates")
    print(f"  Remaining: {len(deduplicated)} unique companies")

    # Normalize
    print("Normalizing fields...")
    normalized = normalize_fields(deduplicated)
    print(f"  Normalized {len(normalized)} companies")

    print()

    # Write output
    WORKING_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = list(normalized[0].keys()) if normalized else []

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized)

    print(f"✓ Wrote {len(normalized)} companies to: {OUTPUT_FILE}")
    print()

    # Print summary
    print("=" * 70)
    print("MERGE SUMMARY")
    print("=" * 70)
    print(f"Path A companies: {len(path_a_companies)}")
    print(f"Path B companies: {len(path_b_companies)}")
    print(f"Total before dedup: {len(all_companies)}")
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"Final unique companies: {len(normalized)}")

    # Breakdown by source
    path_a_count = sum(1 for c in normalized if c.get('Validation_Source') == 'PathA')
    path_b_count = sum(1 for c in normalized if c.get('Validation_Source') == 'PathB')

    print()
    print("By Source:")
    print(f"  Path A: {path_a_count} ({100*path_a_count/len(normalized):.1f}%)")
    print(f"  Path B: {path_b_count} ({100*path_b_count/len(normalized):.1f}%)")
    print()


if __name__ == '__main__':
    main()
