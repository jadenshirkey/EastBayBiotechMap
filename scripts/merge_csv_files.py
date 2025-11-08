#!/usr/bin/env python3
"""
Merge CSV files to create the final companies dataset.

Strategy:
1. Use east_bay_biotech_v2.csv as base (172 companies, full Bay Area)
2. For overlapping companies, use better address from with_addresses.csv
3. Remove "Relevance to Profile" column (personal rankings, not universal)
4. Keep all other columns
5. Output to data/working/companies_merged.csv

This creates a clean base file ready for enrichment (descriptions, size, funding, etc.)
"""

import csv
from collections import defaultdict

def load_csv_to_dict(filename, key_field='Company Name'):
    """Load CSV into a dictionary keyed by company name"""
    companies = {}
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies[row[key_field]] = row
    return companies

def merge_csv_files():
    """Merge the CSV files"""

    print("Loading CSV files...")

    # Load both files
    v2_companies = load_csv_to_dict('../data/archive/east_bay_biotech_v2.csv')
    with_addr_companies = load_csv_to_dict('../data/archive/east_bay_biotech_with_addresses.csv')

    print(f"  v2.csv: {len(v2_companies)} companies")
    print(f"  with_addresses.csv: {len(with_addr_companies)} companies")

    # Find overlapping companies
    v2_names = set(v2_companies.keys())
    with_addr_names = set(with_addr_companies.keys())
    overlap = v2_names & with_addr_names
    only_v2 = v2_names - with_addr_names

    print(f"\nCompany overlap:")
    print(f"  Both files: {len(overlap)} companies")
    print(f"  Only in v2: {len(only_v2)} companies")

    # Merge strategy
    merged = []
    address_improvements = 0

    for company_name in sorted(v2_companies.keys()):
        company = v2_companies[company_name].copy()

        # If company is in both files, check if with_addresses has better address
        if company_name in with_addr_companies:
            v2_addr = company.get('Address', '').strip()
            with_addr = with_addr_companies[company_name].get('Address', '').strip()

            # Use with_addresses version if:
            # 1. v2 has no address but with_addresses does
            # 2. v2 has only "City, CA" but with_addresses has full address
            if not v2_addr and with_addr:
                company['Address'] = with_addr
                address_improvements += 1
            elif v2_addr and with_addr and len(with_addr) > len(v2_addr):
                # Check if with_addr looks more complete (has street number)
                if any(char.isdigit() for char in with_addr[:10]):  # Likely has street number
                    if not any(char.isdigit() for char in v2_addr[:10]):  # v2 doesn't
                        company['Address'] = with_addr
                        address_improvements += 1

        # Remove "Relevance to Profile" column (personal rankings)
        if 'Relevance to Profile' in company:
            del company['Relevance to Profile']

        merged.append(company)

    print(f"\nAddress improvements: {address_improvements} companies")

    # Define output columns (all columns except Relevance to Profile)
    output_columns = ['Company Name', 'Website', 'City', 'Address',
                      'Company Stage', 'Notes', 'Hiring']

    # Write merged file
    output_file = '../data/working/companies_merged.csv'
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(merged)

    print(f"\n✓ Created {output_file}")
    print(f"  Total companies: {len(merged)}")
    print(f"  Columns: {', '.join(output_columns)}")

    # Count address completeness
    addresses_filled = sum(1 for c in merged if c.get('Address', '').strip())
    print(f"  Addresses: {addresses_filled}/{len(merged)} ({100*addresses_filled/len(merged):.1f}%)")

    print(f"\nNext steps:")
    print(f"  1. Add Latitude and Longitude columns (geocoding)")
    print(f"  2. Add Description, Company Size, Funding Status, Technology Focus")
    print(f"  3. Add Careers Link column")
    print(f"  4. Save to data/final/companies.csv")

if __name__ == "__main__":
    merge_csv_files()
