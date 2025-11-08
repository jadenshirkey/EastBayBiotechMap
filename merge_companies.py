#!/usr/bin/env python3
"""
Merge biotech company datasets and perform address lookups.

This script:
1. Merges existing companies.csv with NEW_COMPANIES_TO_ADD.csv
2. Uses Focus Area data from biotech_companies_A.txt
3. Identifies companies needing address lookups
4. Outputs merged dataset to companies.csv
"""

import csv
import json
from pathlib import Path
from collections import OrderedDict

# File paths
BASE_DIR = Path("/home/user/EastBayBiotechMap")
EXISTING_CSV = BASE_DIR / "data/final/companies.csv"
NEW_CSV = BASE_DIR / "data/working/NEW_COMPANIES_TO_ADD.csv"
FOCUS_AREAS_TXT = BASE_DIR / "data/working/biotech_companies_A.txt"
OUTPUT_CSV = BASE_DIR / "data/final/companies.csv"
COMPANIES_NEEDING_ADDRESSES = BASE_DIR / "companies_needing_addresses.json"

def read_csv(filepath):
    """Read CSV file and return list of dictionaries."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_csv(filepath, data, fieldnames):
    """Write data to CSV file."""
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_data():
    """Load all three data files."""
    # Load existing companies
    existing = read_csv(EXISTING_CSV)
    print(f"Loaded {len(existing)} existing companies")

    # Load new companies
    new_companies = read_csv(NEW_CSV)
    print(f"Loaded {len(new_companies)} new companies to add")

    # Load focus areas
    focus_areas = read_csv(FOCUS_AREAS_TXT)
    print(f"Loaded {len(focus_areas)} companies with focus area data")

    return existing, new_companies, focus_areas

def create_focus_area_map(focus_areas):
    """Create a dictionary mapping company names to focus areas."""
    focus_dict = {}
    for row in focus_areas:
        company_name = row.get('Company Name', '').strip()
        focus_area = row.get('Focus Area', '').strip()
        if company_name and focus_area:
            focus_dict[company_name] = focus_area
    return focus_dict

def standardize_row(row, focus_dict, is_existing=True):
    """Standardize a row to the target format."""
    company_name = row.get('Company Name', '').strip()

    standardized = OrderedDict([
        ('Company Name', company_name),
        ('Website', row.get('Website', '').strip()),
        ('City', row.get('City', '').strip()),
        ('Address', row.get('Address', '').strip()),
        ('Company Stage', row.get('Company Stage', '').strip()),
        ('Focus Areas', '')
    ])

    # Handle Focus Areas
    if is_existing:
        # Existing data has "Notes" column
        standardized['Focus Areas'] = row.get('Notes', '').strip()
    else:
        # New data might have "Focus Area" or get it from focus_dict
        focus_area = row.get('Focus Area', '').strip()
        if not focus_area and company_name in focus_dict:
            focus_area = focus_dict[company_name]
        standardized['Focus Areas'] = focus_area

    return standardized

def main():
    print("=" * 70)
    print("MERGING BIOTECH COMPANY DATASETS")
    print("=" * 70)
    print()

    # Load data
    existing, new_companies, focus_areas = load_data()
    print()

    # Create focus area mapping
    print("Creating focus area mapping...")
    focus_dict = create_focus_area_map(focus_areas)
    print(f"Mapped {len(focus_dict)} company focus areas")
    print()

    # Standardize existing companies
    print("Standardizing existing companies...")
    standardized_existing = []
    existing_names = set()
    for row in existing:
        standardized = standardize_row(row, focus_dict, is_existing=True)
        standardized_existing.append(standardized)
        existing_names.add(standardized['Company Name'])
    print()

    # Standardize new companies (skip duplicates)
    print("Standardizing new companies...")
    standardized_new = []
    skipped = 0
    for row in new_companies:
        company_name = row.get('Company Name', '').strip()
        if company_name in existing_names:
            skipped += 1
            continue
        standardized = standardize_row(row, focus_dict, is_existing=False)
        standardized_new.append(standardized)

    print(f"Added {len(standardized_new)} new companies (skipped {skipped} duplicates)")
    print()

    # Merge datasets
    print("Merging datasets...")
    merged = standardized_existing + standardized_new
    print(f"Total companies after merge: {len(merged)}")
    print()

    # Identify companies needing addresses (only from new companies)
    print("Identifying NEW companies needing address lookups...")
    companies_needing_addresses = []
    for row in standardized_new:
        if not row['Address']:
            companies_needing_addresses.append({
                'company_name': row['Company Name'],
                'city': row['City'],
                'website': row['Website']
            })

    print(f"Found {len(companies_needing_addresses)} NEW companies without addresses")

    # Save list for address lookup
    with open(COMPANIES_NEEDING_ADDRESSES, 'w') as f:
        json.dump(companies_needing_addresses, f, indent=2)
    print(f"Saved list to: {COMPANIES_NEEDING_ADDRESSES}")
    print()

    # Save merged dataset (before address lookups)
    fieldnames = ['Company Name', 'Website', 'City', 'Address', 'Company Stage', 'Focus Areas']
    print(f"Saving preliminary merged dataset to: {OUTPUT_CSV}")
    write_csv(OUTPUT_CSV, merged, fieldnames)

    print()
    print("=" * 70)
    print("MERGE COMPLETE - READY FOR ADDRESS LOOKUPS")
    print("=" * 70)
    print()
    print(f"Summary:")
    print(f"  - Existing companies: {len(standardized_existing)}")
    print(f"  - New companies added: {len(standardized_new)}")
    print(f"  - Total companies: {len(merged)}")
    print(f"  - Companies needing addresses: {len(companies_needing_addresses)}")
    print()
    print(f"Next step: Perform address lookups for {len(companies_needing_addresses)} companies")

    return merged, companies_needing_addresses

if __name__ == "__main__":
    merged_df, companies_needing_addresses = main()
