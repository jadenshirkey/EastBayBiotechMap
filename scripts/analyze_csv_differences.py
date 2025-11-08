#!/usr/bin/env python3
"""
Analyze differences between the three main CSV files to prepare for merging.

This script compares:
- east_bay_biotech_v2.csv (172 companies, broader Bay Area)
- east_bay_biotech_with_addresses.csv (74 companies, East Bay focused, "Tier" format)
- east_bay_biotech_pseudofinal.csv (73 companies, East Bay focused, numeric format)

Output: Analysis report and recommendations for merge strategy
"""

import pandas as pd
import sys

def analyze_csv_files():
    """Compare the three main CSV files"""

    # Load the three files
    print("Loading CSV files...")
    try:
        v2 = pd.read_csv('../data/archive/east_bay_biotech_v2.csv')
        with_addr = pd.read_csv('../data/archive/east_bay_biotech_with_addresses.csv')
        pseudo = pd.read_csv('../data/archive/east_bay_biotech_pseudofinal.csv')
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure you're running this from the scripts/ directory")
        sys.exit(1)

    print("\n" + "="*70)
    print("CSV FILE COMPARISON")
    print("="*70)

    # Basic stats
    print(f"\nFile sizes:")
    print(f"  v2.csv:              {len(v2):3d} companies")
    print(f"  with_addresses.csv:  {len(with_addr):3d} companies")
    print(f"  pseudofinal.csv:     {len(pseudo):3d} companies")

    # Column comparison
    print(f"\nColumns in each file:")
    print(f"\nv2.csv:")
    print(f"  {list(v2.columns)}")
    print(f"\nwith_addresses.csv:")
    print(f"  {list(with_addr.columns)}")
    print(f"\npseudofinal.csv:")
    print(f"  {list(pseudo.columns)}")

    # City coverage
    print(f"\n" + "="*70)
    print("GEOGRAPHIC COVERAGE")
    print("="*70)

    print(f"\nCities in v2.csv ({len(v2['City'].unique())} unique):")
    v2_cities = sorted(v2['City'].unique())
    for city in v2_cities:
        count = len(v2[v2['City'] == city])
        print(f"  {city:30s} ({count:3d} companies)")

    print(f"\nCities in with_addresses.csv ({len(with_addr['City'].unique())} unique):")
    with_addr_cities = sorted(with_addr['City'].unique())
    for city in with_addr_cities:
        count = len(with_addr[with_addr['City'] == city])
        print(f"  {city:30s} ({count:3d} companies)")

    # Address completeness
    print(f"\n" + "="*70)
    print("ADDRESS COMPLETENESS")
    print("="*70)

    def count_addresses(df):
        """Count how many addresses are filled in"""
        if 'Address' not in df.columns:
            return 0, len(df)
        filled = df['Address'].notna().sum() - (df['Address'] == '').sum()
        return filled, len(df)

    v2_addr_filled, v2_total = count_addresses(v2)
    with_addr_filled, with_addr_total = count_addresses(with_addr)
    pseudo_filled, pseudo_total = count_addresses(pseudo)

    print(f"\nv2.csv:              {v2_addr_filled:3d}/{v2_total:3d} addresses ({100*v2_addr_filled/v2_total:.1f}%)")
    print(f"with_addresses.csv:  {with_addr_filled:3d}/{with_addr_total:3d} addresses ({100*with_addr_filled/with_addr_total:.1f}%)")
    print(f"pseudofinal.csv:     {pseudo_filled:3d}/{pseudo_total:3d} addresses ({100*pseudo_filled/pseudo_total:.1f}%)")

    # Company overlap
    print(f"\n" + "="*70)
    print("COMPANY OVERLAP")
    print("="*70)

    v2_companies = set(v2['Company Name'])
    with_addr_companies = set(with_addr['Company Name'])
    pseudo_companies = set(pseudo['Company Name'])

    # Companies unique to v2
    unique_to_v2 = v2_companies - with_addr_companies - pseudo_companies
    print(f"\nCompanies ONLY in v2.csv: {len(unique_to_v2)}")
    if len(unique_to_v2) <= 20:
        for company in sorted(unique_to_v2):
            city = v2[v2['Company Name'] == company]['City'].iloc[0]
            print(f"  - {company} ({city})")
    else:
        for company in sorted(list(unique_to_v2)[:10]):
            city = v2[v2['Company Name'] == company]['City'].iloc[0]
            print(f"  - {company} ({city})")
        print(f"  ... and {len(unique_to_v2) - 10} more")

    # Companies in both with_addr and v2
    overlap_v2_with_addr = v2_companies & with_addr_companies
    print(f"\nCompanies in BOTH v2.csv and with_addresses.csv: {len(overlap_v2_with_addr)}")

    # Recommendations
    print(f"\n" + "="*70)
    print("MERGE RECOMMENDATIONS")
    print("="*70)

    print(f"""
Base file: east_bay_biotech_v2.csv ({len(v2)} companies)
  ✓ Most comprehensive (172 companies across entire Bay Area)
  ✓ Includes Palo Alto, SF, Redwood City, etc.

Enrich with: east_bay_biotech_with_addresses.csv
  ✓ Better address data for East Bay companies
  ✓ Has "Tier 1/2/3" format (more readable than numeric)
  ✓ {with_addr_filled}/{with_addr_total} addresses filled

Strategy:
  1. Start with v2.csv as base (all {len(v2)} companies)
  2. For companies in both files:
     - Use address from with_addresses.csv if it's more complete
     - Keep v2.csv address if with_addresses is empty
  3. Remove "Relevance to Profile" / "Tier" columns (personal rankings)
  4. Clean up "Relevance to Profile" column formats
  5. Save as data/working/companies_merged.csv

Next steps after merge:
  - Add Latitude and Longitude columns (geocoding)
  - Add Description, Company Size, Funding Status, Technology Focus
  - Add Careers Link column
  - Save final version to data/final/companies.csv
""")

if __name__ == "__main__":
    analyze_csv_differences()
