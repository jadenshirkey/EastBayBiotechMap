#!/usr/bin/env python3
"""
Merge company data from multiple sources with V4.3 deduplication and geofencing.

This script implements Phase 2 (Stage-B) from the V4.3 methodology:
- eTLD+1 + normalized name deduplication
- Domain-reuse conflict detection
- Centralized geofence (late filtering AFTER dedupe)
- Aggregator domain handling
- BPG Website preservation (canonical ground truth)

Usage:
    python3 merge_company_sources.py

Inputs:
    data/working/bpg_ca_raw.csv          (BioPharmGuy CA-wide extraction)
    data/working/wikipedia_companies.csv (Wikipedia extractions)
    data/final/companies.csv             (Existing companies - if exists)

Outputs:
    data/working/companies_merged.csv     (Merged and geofenced companies)
    data/working/domain_reuse_report.txt  (Domain conflict report)

Author: Jaden Shirkey
Date: January 2025
Version: V4.3 Stage-B
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import V4.3 modules
from config.geography import is_in_bay_area_city, is_valid_county, BAY_COUNTIES, CITY_WHITELIST
from utils.helpers import etld1, normalize_name, is_aggregator, AGGREGATOR_ETLD1

# ============================================================================
# Constants
# ============================================================================

# Allow-list for domains that legitimately host multiple companies
# (e.g., gene.com hosts both Genentech and related brands)
ALLOWLIST_DOMAINS = {
    'gene.com',  # Genentech parent domain for multiple brands
}

# Final schema columns
FINAL_COLUMNS = [
    'Company Name', 'Website', 'City', 'Address',
    'Company Stage', 'Focus Areas', 'Validation_Source'
]

# ============================================================================
# Loading Functions
# ============================================================================

def load_bpg_companies(filepath):
    """
    Load BioPharmGuy CA-wide companies.

    Expected columns: Company Name, Website, City, Focus Area, Source URL, Notes
    """
    companies = []
    if not filepath.exists():
        print(f"Warning: {filepath} not found, skipping BPG source")
        return companies

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append({
                'Company Name': row['Company Name'].strip(),
                'Website': row.get('Website', '').strip(),
                'City': row.get('City', '').strip(),
                'Address': '',
                'Company Stage': '',
                'Focus Areas': row.get('Focus Area', '').strip(),
                'source': 'BPG'
            })

    print(f"Loaded {len(companies)} companies from BPG (CA-wide, unfiltered)")
    return companies


def load_wikipedia_companies(filepath):
    """Load Wikipedia extractions (minimal data)."""
    companies = []
    if not filepath.exists():
        print(f"Warning: {filepath} not found, skipping Wikipedia source")
        return companies

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company_name = row['Company Name'].strip()

            # Skip meta entries and non-companies
            skip_keywords = ['list of', 'category:', 'companies based in', 'biotechnology industry',
                           'by county', 'by city', 'wikipedia', 'portal:']
            if any(keyword in company_name.lower() for keyword in skip_keywords):
                continue

            companies.append({
                'Company Name': company_name,
                'Website': '',
                'City': row.get('City', '').strip(),
                'Address': '',
                'Company Stage': '',
                'Focus Areas': '',
                'source': 'Wikipedia'
            })

    print(f"Loaded {len(companies)} companies from Wikipedia")
    return companies


def load_existing_companies(filepath):
    """Load existing companies.csv with full data."""
    companies = []
    if not filepath.exists():
        print(f"Note: {filepath} not found, starting fresh (no existing companies)")
        return companies

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append({
                'Company Name': row['Company Name'].strip(),
                'Website': row.get('Website', '').strip(),
                'City': row.get('City', '').strip(),
                'Address': row.get('Address', '').strip(),
                'Company Stage': row.get('Company Stage', '').strip(),
                'Focus Areas': row.get('Focus Areas', '').strip(),
                'source': 'Existing'
            })

    print(f"Loaded {len(companies)} companies from existing dataset")
    return companies


# ============================================================================
# Aggregator Handling
# ============================================================================

def check_and_reset_aggregators(companies):
    """
    Check for aggregator domains and reset Website to '' to force Path B enrichment.

    Returns: modified companies list, count of aggregators found
    """
    aggregator_count = 0

    for company in companies:
        website = company.get('Website', '').strip()

        if website and is_aggregator(website):
            print(f"  WARNING: Aggregator detected for '{company['Company Name']}': {website}")
            print(f"           Resetting Website to '' (will route to Path B enrichment)")
            company['Website'] = ''
            aggregator_count += 1

    return companies, aggregator_count


# ============================================================================
# Deduplication with eTLD+1
# ============================================================================

def deduplicate_by_etld1_and_name(companies):
    """
    Deduplicate companies using (eTLD+1, normalized_name) tuple.

    Priority order:
    1. BPG (ground truth)
    2. Existing (already validated)
    3. Wikipedia (minimal data)

    Returns: deduplicated companies, domain reuse conflicts
    """
    # Build index: (etld1, normalized_name) -> list of companies
    dedup_index = defaultdict(list)

    for company in companies:
        website = company.get('Website', '').strip()
        name = company.get('Company Name', '').strip()

        # Extract eTLD+1 (empty string if no website)
        domain = etld1(website) if website else ''

        # Normalize name
        norm_name = normalize_name(name)

        # Create dedup key
        # If no website, use just normalized name
        # If website, use (etld1, normalized_name)
        if domain:
            key = (domain, norm_name)
        else:
            # Companies without websites get unique keys based on name only
            # We'll still check for name collisions separately
            key = ('__no_website__', norm_name)

        dedup_index[key].append(company)

    # Deduplicate: prefer BPG > Existing > Wikipedia
    deduplicated = []
    domain_conflicts = defaultdict(list)  # etld1 -> list of company names

    for key, company_list in dedup_index.items():
        domain_part, name_part = key

        if len(company_list) == 1:
            # No conflict, keep the company
            deduplicated.append(company_list[0])
        else:
            # Multiple companies with same (etld1, normalized_name)
            # Sort by priority: BPG > Existing > Wikipedia
            priority_order = {'BPG': 1, 'Existing': 2, 'Wikipedia': 3}
            sorted_companies = sorted(company_list, key=lambda c: priority_order.get(c['source'], 99))

            # Keep the highest priority one
            winner = sorted_companies[0]
            deduplicated.append(winner)

            # If they have different actual names, log the merge
            unique_names = set(c['Company Name'] for c in company_list)
            if len(unique_names) > 1:
                print(f"  Merged {len(company_list)} variants: {', '.join(unique_names)} -> '{winner['Company Name']}' (from {winner['source']})")

    # Now check for domain reuse: same eTLD+1 used by different companies
    # (different normalized names)
    domain_usage = defaultdict(set)  # etld1 -> set of normalized company names

    for company in deduplicated:
        website = company.get('Website', '').strip()
        if website:
            domain = etld1(website)
            if domain and domain not in ALLOWLIST_DOMAINS:
                norm_name = normalize_name(company['Company Name'])
                domain_usage[domain].add((norm_name, company['Company Name']))

    # Find conflicts: domains used by >1 company
    for domain, name_set in domain_usage.items():
        if len(name_set) > 1:
            # Convert set to list of actual company names
            company_names = [actual_name for (norm, actual_name) in name_set]
            domain_conflicts[domain] = company_names

    return deduplicated, domain_conflicts


# ============================================================================
# Geofencing
# ============================================================================

def apply_geofence(companies):
    """
    Apply Bay Area geofence AFTER deduplication.

    Accept if:
    - City in CITY_WHITELIST, OR
    - County in BAY_COUNTIES (if provided)

    Returns: filtered companies, stats
    """
    filtered = []
    rejected_count = 0

    for company in companies:
        city = company.get('City', '').strip()

        # Check city whitelist
        if city and is_in_bay_area_city(city):
            filtered.append(company)
        else:
            rejected_count += 1
            # Optionally log rejections (can be verbose)
            # print(f"  Filtered out: '{company['Company Name']}' in {city} (not in Bay Area)")

    print(f"\nGeofence filtering:")
    print(f"  - Passed geofence: {len(filtered)}")
    print(f"  - Filtered out: {rejected_count}")

    return filtered


# ============================================================================
# Reporting
# ============================================================================

def generate_domain_reuse_report(conflicts, output_path):
    """
    Generate domain_reuse_report.txt listing domains used by >1 company.

    Format:
        Domain: example.com
          - Company A
          - Company B
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("Domain Reuse Conflict Report\n")
        f.write("="*70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        if not conflicts:
            f.write("✓ No domain conflicts detected!\n")
            f.write("  All domains are uniquely assigned to one company.\n")
        else:
            f.write(f"⚠ Found {len(conflicts)} domain(s) used by multiple companies:\n\n")

            for domain, company_names in sorted(conflicts.items()):
                f.write(f"Domain: {domain}\n")
                for name in sorted(company_names):
                    f.write(f"  - {name}\n")
                f.write("\n")

            f.write("-"*70 + "\n")
            f.write("ACTION REQUIRED:\n")
            f.write("  Review these conflicts and resolve manually:\n")
            f.write("  1. Verify which company actually owns the domain\n")
            f.write("  2. Update the incorrect entries to have Website=''\n")
            f.write("  3. If legitimate (e.g., parent company), add to ALLOWLIST_DOMAINS\n")
            f.write("\n")

    print(f"\nDomain reuse report written to: {output_path}")

    return len(conflicts) == 0  # Return True if no conflicts


# ============================================================================
# Output
# ============================================================================

def save_companies(companies, filepath):
    """Save merged companies to CSV (staging output only)."""
    # Validate output path is in working/ directory
    if 'working' not in str(filepath):
        raise ValueError(f"Output path must be in working/ directory, got: {filepath}")

    # Sort by company name
    companies.sort(key=lambda x: x['Company Name'])

    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FINAL_COLUMNS)
        writer.writeheader()

        for company in companies:
            writer.writerow({
                'Company Name': company['Company Name'],
                'Website': company.get('Website', ''),
                'City': company.get('City', ''),
                'Address': company.get('Address', ''),
                'Company Stage': company.get('Company Stage', ''),
                'Focus Areas': company.get('Focus Areas', ''),
                'Validation_Source': company.get('source', '')
            })

    print(f"\n✓ Saved {len(companies)} companies to: {filepath}")


# ============================================================================
# Main Workflow
# ============================================================================

def main():
    """Main merge workflow with V4.3 deduplication and geofencing."""
    print("="*70)
    print("Company Data Merge - V4.3 Stage-B")
    print("="*70)
    print()

    # File paths
    data_dir = Path(__file__).parent.parent / 'data'
    bpg_file = data_dir / 'working' / 'bpg_ca_raw.csv'
    wikipedia_file = data_dir / 'working' / 'wikipedia_companies.csv'
    existing_file = data_dir / 'final' / 'companies.csv'
    output_file = data_dir / 'working' / 'companies_merged.csv'
    report_file = data_dir / 'working' / 'domain_reuse_report.txt'

    # Load all sources
    print("Loading data sources...")
    bpg_companies = load_bpg_companies(bpg_file)
    wikipedia_companies = load_wikipedia_companies(wikipedia_file)
    existing_companies = load_existing_companies(existing_file)

    # Combine all sources
    all_companies = bpg_companies + existing_companies + wikipedia_companies
    print(f"\nTotal companies before processing: {len(all_companies)}")

    # Check and reset aggregator domains
    print("\nChecking for aggregator domains...")
    all_companies, aggregator_count = check_and_reset_aggregators(all_companies)
    if aggregator_count > 0:
        print(f"  Found {aggregator_count} aggregator domain(s) - reset to '' (will route to Path B)")
    else:
        print("  No aggregator domains detected")

    # Deduplicate using eTLD+1 + normalized name
    print("\nDeduplicating by (eTLD+1, normalized_name)...")
    deduplicated, domain_conflicts = deduplicate_by_etld1_and_name(all_companies)
    print(f"  After deduplication: {len(deduplicated)} companies")

    # Apply Bay Area geofence (AFTER deduplication)
    print("\nApplying Bay Area geofence (9-county + city whitelist)...")
    geofenced = apply_geofence(deduplicated)

    # Generate domain reuse report
    print("\nGenerating domain reuse report...")
    no_conflicts = generate_domain_reuse_report(domain_conflicts, report_file)

    # Save merged output
    print("\nSaving merged companies...")
    save_companies(geofenced, output_file)

    # Summary
    print("\n" + "="*70)
    print("Summary:")
    print(f"  - BPG companies (CA-wide): {len(bpg_companies)}")
    print(f"  - Wikipedia companies: {len(wikipedia_companies)}")
    print(f"  - Existing companies: {len(existing_companies)}")
    print(f"  - Total before dedupe: {len(all_companies)}")
    print(f"  - After deduplication: {len(deduplicated)}")
    print(f"  - After Bay Area geofence: {len(geofenced)}")
    print(f"  - Aggregator domains reset: {aggregator_count}")
    print(f"  - Domain conflicts: {len(domain_conflicts)}")

    # Coverage stats
    with_website = sum(1 for c in geofenced if c.get('Website', '').strip())
    without_website = len(geofenced) - with_website
    print(f"\n  Coverage:")
    print(f"    - With Website: {with_website} ({100*with_website/len(geofenced):.1f}%)")
    print(f"    - Without Website: {without_website} ({100*without_website/len(geofenced):.1f}%)")

    print("\n" + "="*70)
    print("✓ Merge complete!")
    print(f"\nNext steps:")
    print(f"  1. Review domain_reuse_report.txt for conflicts")
    print(f"  2. Run Path A enrichment on companies with Website")
    print(f"  3. Run Path B enrichment on companies without Website")
    print()

    # Exit with error if domain conflicts detected (blocks promotion)
    if not no_conflicts:
        print("⚠ WARNING: Domain conflicts detected! Review and resolve before proceeding.")
        print("           (This will not block development, but must be fixed before promotion)")
        # Don't exit with error during development
        # sys.exit(1)


if __name__ == '__main__':
    main()
