#!/usr/bin/env python3
"""
Enrich company data using Google Maps Places API.

This script implements Phase 2-3 (Data Standardization & Enrichment) from the methodology:
- Uses Google Places API to find addresses, websites, and coordinates
- Classifies company stage using heuristics
- Provides geocoded coordinates ready for map visualization

Usage:
    export GOOGLE_MAPS_API_KEY="your-api-key-here"
    python3 enrich_with_google_maps.py

Author: Jaden Shirkey
Date: January 2025
"""

import csv
import os
import sys
import time
import re
from pathlib import Path
from datetime import datetime

try:
    import googlemaps
except ImportError:
    print("Error: googlemaps library not installed")
    print("Run: pip install googlemaps")
    sys.exit(1)

# Configuration
SAVE_INTERVAL = 50  # Save progress every N companies
RATE_LIMIT_DELAY = 0.1  # Delay between API calls (seconds)

# Final schema columns
FINAL_COLUMNS = ['Company Name', 'Website', 'City', 'Address', 'Company Stage', 'Focus Areas']


def classify_company_stage(focus_areas, website_text=''):
    """
    Classify company stage using keyword heuristics.

    Based on methodology categories:
    - Large Pharma
    - Commercial-Stage Biotech
    - Clinical-Stage Biotech
    - Pre-clinical/Startup
    - Tools/Services/CDMO
    - Academic/Gov't
    - Acquired
    - Unknown
    """
    text = (focus_areas + ' ' + website_text).lower()

    # Check for acquisition
    if any(keyword in text for keyword in ['acquired by', 'acquisition', 'merged with']):
        return 'Acquired'

    # Check for academic/government
    if any(keyword in text for keyword in ['university', 'institute', 'national lab', '.edu', '.gov']):
        return 'Academic/Gov\'t'

    # Check for large pharma (usually already classified, but check for keywords)
    if any(keyword in text for keyword in ['fortune 500', 'global pharmaceutical']):
        return 'Large Pharma'

    # Check for commercial stage
    if any(keyword in text for keyword in ['fda approved', 'marketed product', 'commercial', 'revenue']):
        return 'Commercial-Stage Biotech'

    # Check for clinical stage
    clinical_keywords = ['phase i', 'phase ii', 'phase iii', 'phase 1', 'phase 2', 'phase 3',
                         'clinical trial', 'clinical development']
    if any(keyword in text for keyword in clinical_keywords):
        return 'Clinical-Stage Biotech'

    # Check for tools/services/CDMO
    service_keywords = ['cdmo', 'cro', 'contract', 'services', 'reagents', 'instruments',
                       'equipment', 'supplies', 'antibodies', 'kits', 'assays']
    if any(keyword in text for keyword in service_keywords):
        return 'Tools/Services/CDMO'

    # Default to pre-clinical for drug/therapeutic companies
    drug_keywords = ['therapeutic', 'drug', 'therapy', 'treatment', 'medicine']
    if any(keyword in text for keyword in drug_keywords):
        return 'Pre-clinical/Startup'

    # Unknown if can't determine
    return 'Unknown'


def search_place(gmaps, company_name, city):
    """
    Search for company using Google Places API.

    Returns dict with: name, address, website, lat, lng, phone
    """
    try:
        # Try with "biotech" qualifier
        query = f"{company_name} {city} CA biotech"
        results = gmaps.places(query)

        if results['status'] == 'OK' and results['results']:
            place = results['results'][0]

            # Get detailed info using Place Details API
            place_id = place['place_id']
            details = gmaps.place(place_id, fields=['name', 'formatted_address', 'website',
                                                     'geometry', 'formatted_phone_number'])

            if details['status'] == 'OK':
                result = details['result']
                return {
                    'name': result.get('name', ''),
                    'address': result.get('formatted_address', ''),
                    'website': result.get('website', ''),
                    'lat': result.get('geometry', {}).get('location', {}).get('lat', ''),
                    'lng': result.get('geometry', {}).get('location', {}).get('lng', ''),
                    'phone': result.get('formatted_phone_number', '')
                }

        # Try without "biotech" if first search failed
        query = f"{company_name} {city} CA"
        results = gmaps.places(query)

        if results['status'] == 'OK' and results['results']:
            place = results['results'][0]
            place_id = place['place_id']
            details = gmaps.place(place_id, fields=['name', 'formatted_address', 'website',
                                                     'geometry', 'formatted_phone_number'])

            if details['status'] == 'OK':
                result = details['result']
                return {
                    'name': result.get('name', ''),
                    'address': result.get('formatted_address', ''),
                    'website': result.get('website', ''),
                    'lat': result.get('geometry', {}).get('location', {}).get('lat', ''),
                    'lng': result.get('geometry', {}).get('location', {}).get('lng', ''),
                    'phone': result.get('formatted_phone_number', '')
                }

    except Exception as e:
        print(f"  Error searching for {company_name}: {e}")

    return None


def load_companies(filepath):
    """Load companies from CSV."""
    companies = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row)
    return companies


def save_companies(companies, filepath):
    """Save companies to CSV."""
    # Sort by company name
    companies.sort(key=lambda x: x['Company Name'])

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FINAL_COLUMNS)
        writer.writeheader()
        writer.writerows(companies)


def main():
    """Main enrichment workflow."""
    print("="*70)
    print("Google Maps Places API Enrichment")
    print("="*70)
    print()

    # Check for API key
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("Error: GOOGLE_MAPS_API_KEY environment variable not set")
        print()
        print("Set it with:")
        print("  export GOOGLE_MAPS_API_KEY='your-api-key-here'")
        print()
        print("Or on Windows:")
        print("  set GOOGLE_MAPS_API_KEY=your-api-key-here")
        print()
        sys.exit(1)

    # Initialize Google Maps client
    try:
        gmaps = googlemaps.Client(key=api_key)
        print("✓ Google Maps API client initialized")
    except Exception as e:
        print(f"Error initializing Google Maps client: {e}")
        sys.exit(1)

    # Load companies
    companies_file = Path('../data/final/companies.csv')
    print(f"Loading companies from: {companies_file}")
    companies = load_companies(companies_file)
    print(f"  Loaded {len(companies)} companies")
    print()

    # Identify companies needing enrichment
    needs_enrichment = []
    for company in companies:
        website = company.get('Website', '').strip()
        address = company.get('Address', '').strip()

        if not website or not address:
            needs_enrichment.append(company)

    print(f"Companies needing enrichment: {len(needs_enrichment)}")
    print()

    # Statistics tracking
    stats = {
        'total': len(needs_enrichment),
        'addresses_found': 0,
        'websites_found': 0,
        'not_found': 0,
        'errors': 0
    }

    not_found = []

    # Process each company
    for i, company in enumerate(needs_enrichment, 1):
        company_name = company['Company Name']
        city = company['City']

        print(f"[{i}/{stats['total']}] {company_name} ({city})")

        # Search using Google Places API
        place_data = search_place(gmaps, company_name, city)

        if place_data:
            # Update company data
            if place_data['address'] and not company.get('Address'):
                company['Address'] = place_data['address']
                stats['addresses_found'] += 1
                print(f"  ✓ Address: {place_data['address']}")

            if place_data['website'] and not company.get('Website'):
                company['Website'] = place_data['website']
                stats['websites_found'] += 1
                print(f"  ✓ Website: {place_data['website']}")

            # Classify company stage if not already set
            if not company.get('Company Stage') or company.get('Company Stage') == 'Unknown':
                stage = classify_company_stage(company.get('Focus Areas', ''))
                company['Company Stage'] = stage
                print(f"  ✓ Stage: {stage}")

        else:
            stats['not_found'] += 1
            not_found.append(company_name)
            print(f"  ✗ Not found in Google Maps")

        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)

        # Save progress periodically
        if i % SAVE_INTERVAL == 0:
            print(f"\n  Saving progress ({i}/{stats['total']})...\n")
            save_companies(companies, companies_file)

    # Final save
    print()
    print("Saving final results...")
    save_companies(companies, companies_file)
    print(f"✓ Saved to: {companies_file}")
    print()

    # Generate report
    report_file = Path('../data/working/enrichment_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("Google Maps API Enrichment Report\n")
        f.write("=" * 70 + "\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("Statistics:\n")
        f.write(f"  Total companies processed: {stats['total']}\n")
        f.write(f"  Addresses found: {stats['addresses_found']} ({100*stats['addresses_found']/stats['total']:.1f}%)\n")
        f.write(f"  Websites found: {stats['websites_found']} ({100*stats['websites_found']/stats['total']:.1f}%)\n")
        f.write(f"  Not found: {stats['not_found']} ({100*stats['not_found']/stats['total']:.1f}%)\n\n")

        if not_found:
            f.write("Companies not found in Google Maps:\n")
            for name in not_found:
                f.write(f"  - {name}\n")

    print(f"✓ Report saved to: {report_file}")
    print()

    # Print summary
    print("="*70)
    print("ENRICHMENT SUMMARY")
    print("="*70)
    print(f"Total processed: {stats['total']}")
    print(f"Addresses found: {stats['addresses_found']} ({100*stats['addresses_found']/stats['total']:.1f}%)")
    print(f"Websites found: {stats['websites_found']} ({100*stats['websites_found']/stats['total']:.1f}%)")
    print(f"Not found: {stats['not_found']} ({100*stats['not_found']/stats['total']:.1f}%)")
    print()


if __name__ == '__main__':
    main()
