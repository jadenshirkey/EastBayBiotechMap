#!/usr/bin/env python3
"""
Merge company data from multiple sources and remove duplicates.

This script implements Phase 1.5 (Deduplication) from the methodology:
- Merges companies from Wikipedia, BioPharmGuy, and existing dataset
- Deduplicates by normalized company name
- Preserves rich data from existing dataset
- Filters for Bay Area relevance

Usage:
    python3 merge_company_sources.py

Author: Jaden Shirkey
Date: January 2025
"""

import csv
import re
from pathlib import Path
from datetime import datetime

# Bay Area cities whitelist (from METHODOLOGY.md Appendix A)
BAY_AREA_CITIES = {
    # Alameda County
    'Alameda', 'Albany', 'Berkeley', 'Dublin', 'Emeryville', 'Fremont',
    'Hayward', 'Livermore', 'Newark', 'Oakland', 'Pleasanton', 'San Leandro',
    'Union City',
    # Contra Costa County
    'Antioch', 'Concord', 'Richmond', 'San Ramon', 'Walnut Creek',
    # Marin County
    'Novato', 'San Rafael',
    # San Francisco County
    'San Francisco',
    # San Mateo County
    'Belmont', 'Burlingame', 'Foster City', 'Menlo Park', 'Redwood City',
    'San Carlos', 'San Mateo', 'South San Francisco',
    # Santa Clara County
    'Campbell', 'Cupertino', 'Milpitas', 'Mountain View', 'Palo Alto',
    'San Jose', 'Santa Clara', 'Sunnyvale',
    # Solano County
    'Benicia', 'Fairfield', 'Vallejo',
    # Sonoma County
    'Petaluma', 'Santa Rosa',
    # Napa County
    'Napa'
}

# Final schema columns
FINAL_COLUMNS = ['Company Name', 'Website', 'City', 'Address', 'Company Stage', 'Focus Areas']


def normalize_company_name(name):
    """
    Normalize company name for deduplication matching.

    Examples:
        "BioMarin Pharmaceutical Inc." → "biomarin pharmaceutical"
        "ATUM (DNA 2.0)" → "atum"
    """
    if not name:
        return ''

    # Convert to lowercase
    normalized = name.lower()

    # Remove common suffixes
    suffixes = [
        r'\s+inc\.?$', r'\s+incorporated$', r'\s+corporation$', r'\s+corp\.?$',
        r'\s+ltd\.?$', r'\s+limited$', r'\s+llc\.?$', r'\s+co\.?$',
        r'\s+company$', r'\s+plc\.?$'
    ]
    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized)

    # Remove parenthetical notes
    normalized = re.sub(r'\([^)]*\)', '', normalized)

    # Remove special characters except spaces
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)

    # Normalize whitespace
    normalized = ' '.join(normalized.split())

    return normalized.strip()


def is_bay_area_city(city):
    """Check if city is in Bay Area whitelist."""
    if not city:
        return False
    return city.strip() in BAY_AREA_CITIES


def load_existing_companies(filepath):
    """Load existing companies.csv with full data."""
    companies = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append({
                'Company Name': row['Company Name'],
                'Website': row.get('Website', ''),
                'City': row.get('City', ''),
                'Address': row.get('Address', ''),
                'Company Stage': row.get('Company Stage', ''),
                'Focus Areas': row.get('Focus Areas', ''),
                'source': 'existing'
            })
    return companies


def load_wikipedia_companies(filepath):
    """Load Wikipedia extractions (minimal data)."""
    companies = []
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
                'Website': '',  # Not provided
                'City': row.get('City', ''),
                'Address': '',  # Not provided
                'Company Stage': '',  # Not provided
                'Focus Areas': '',  # Not provided
                'source': 'wikipedia'
            })
    return companies


def load_biopharmguy_companies(filepath):
    """Load BioPharmGuy extractions (partial data)."""
    companies = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            city = row.get('City', '').strip()

            # Only include if Bay Area city
            if not is_bay_area_city(city):
                continue

            companies.append({
                'Company Name': row['Company Name'],
                'Website': '',  # Not provided
                'City': city,
                'Address': '',  # Not provided
                'Company Stage': '',  # Not provided
                'Focus Areas': row.get('Focus Area', ''),
                'source': 'biopharmguy'
            })
    return companies


def merge_and_deduplicate(existing, wikipedia, biopharmguy):
    """
    Merge companies from all sources and deduplicate.

    Priority order (highest to lowest):
    1. Existing companies.csv (complete data)
    2. BioPharmGuy (partial data with city and focus)
    3. Wikipedia (minimal data)
    """
    # Build deduplication index from existing companies
    seen_names = {}
    merged = []

    # Phase 1: Add all existing companies (highest priority)
    for company in existing:
        normalized = normalize_company_name(company['Company Name'])
        seen_names[normalized] = True
        merged.append(company)

    print(f"Existing companies: {len(existing)}")

    # Phase 2: Add new companies from BioPharmGuy (medium priority)
    biopharmguy_added = 0
    for company in biopharmguy:
        normalized = normalize_company_name(company['Company Name'])

        if normalized and normalized not in seen_names:
            seen_names[normalized] = True
            merged.append(company)
            biopharmguy_added += 1

    print(f"New from BioPharmGuy: {biopharmguy_added}")

    # Phase 3: Add new companies from Wikipedia (lowest priority)
    wikipedia_added = 0
    for company in wikipedia:
        normalized = normalize_company_name(company['Company Name'])

        # Only add if:
        # 1. Not already seen
        # 2. Has a city (or we can't validate Bay Area location)
        if normalized and normalized not in seen_names:
            # For Wikipedia, we need Bay Area validation
            # Since most don't have cities, skip them unless we can validate
            city = company.get('City', '').strip()
            if city and is_bay_area_city(city):
                seen_names[normalized] = True
                merged.append(company)
                wikipedia_added += 1

    print(f"New from Wikipedia: {wikipedia_added}")
    print(f"Total after merge: {len(merged)}")

    return merged


def save_companies(companies, filepath):
    """Save merged companies to CSV."""
    # Sort by company name
    companies.sort(key=lambda x: x['Company Name'])

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
                'Focus Areas': company.get('Focus Areas', '')
            })


def main():
    """Main merge workflow."""
    print("="*70)
    print("Company Data Merge and Deduplication")
    print("="*70)
    print()

    # File paths
    existing_file = Path('../data/final/companies.csv')
    wikipedia_file = Path('../data/working/wikipedia_companies.csv')
    biopharmguy_file = Path('../data/working/biopharmguy_companies.csv')
    output_file = Path('../data/final/companies.csv')

    # Create backup of existing file
    if existing_file.exists():
        backup_file = Path(f'../data/final/companies_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        print(f"Creating backup: {backup_file.name}")
        import shutil
        shutil.copy(existing_file, backup_file)
        print()

    # Load all sources
    print("Loading data sources...")
    existing = load_existing_companies(existing_file)
    wikipedia = load_wikipedia_companies(wikipedia_file)
    biopharmguy = load_biopharmguy_companies(biopharmguy_file)
    print()

    # Merge and deduplicate
    print("Merging and deduplicating...")
    merged = merge_and_deduplicate(existing, wikipedia, biopharmguy)
    print()

    # Save merged data
    print(f"Saving to: {output_file}")
    save_companies(merged, output_file)
    print()

    print("✓ Merge complete!")
    print()
    print("Summary:")
    print(f"  - Total companies: {len(merged)}")
    print(f"  - New companies need manual enrichment:")
    print(f"    * Website, Address, Company Stage fields")
    print()


if __name__ == '__main__':
    main()
