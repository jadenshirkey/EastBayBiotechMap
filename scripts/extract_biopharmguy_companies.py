#!/usr/bin/env python3
"""
Extract biotech/pharma company names from BioPharmGuy directory.

This script implements Phase 1 of the East Bay Biotech Map methodology:
automated extraction from BioPharmGuy's Northern California company listings.

Usage:
    python3 extract_biopharmguy_companies.py

Output:
    data/working/biopharmguy_companies.csv

Author: Jaden Shirkey
Date: January 2025
"""

import requests
from bs4 import BeautifulSoup
import csv
import re
from pathlib import Path

# BioPharmGuy source
BIOPHARMGUY_URL = 'https://biopharmguy.com/links/company-by-name-northern-california.php'

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


def fetch_biopharmguy_page(url):
    """Fetch BioPharmGuy page content."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; EastBayBiotechMap/1.0; Educational Research)'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse_city_from_text(text):
    """
    Extract city name from location text.

    Common formats:
    - "City, CA"
    - "City, State"
    - "Multiple locations in City and City2"
    """
    if not text:
        return ''

    # Try to match "City, CA" or "City, State" pattern
    match = re.search(r'([A-Za-z\s]+),\s*(?:CA|California)', text)
    if match:
        city = match.group(1).strip()
        # Check if it's a Bay Area city
        if city in BAY_AREA_CITIES:
            return city

    # Check each Bay Area city name in the text
    text_lower = text.lower()
    for city in BAY_AREA_CITIES:
        if city.lower() in text_lower:
            return city

    return ''


def extract_companies_from_biopharmguy(soup):
    """Extract companies from BioPharmGuy Northern California page."""
    companies = []

    # BioPharmGuy uses a table structure with rows
    # Each row has: <td class="company">, <td class="location">, <td class="description">

    # Find all table rows
    table_rows = soup.find_all('tr')

    for row in table_rows:
        # Find the three columns
        company_td = row.find('td', class_='company')
        location_td = row.find('td', class_='location')
        description_td = row.find('td', class_='description')

        # Skip if we don't have all three columns
        if not (company_td and location_td and description_td):
            continue

        # Extract company name from the link
        # There are two links in company_td: one to company.php and one to the website
        # We want the text from the second link (the website link)
        links = company_td.find_all('a')
        if len(links) < 2:
            continue

        company_name = links[1].get_text(strip=True)
        if not company_name or len(company_name) < 2:
            continue

        # Extract location - format is "CA - City" or "CA - City/Region"
        location_text = location_td.get_text(strip=True)

        # Parse city from "CA - City" format
        city = ''
        if 'CA -' in location_text:
            city_part = location_text.replace('CA -', '').strip()

            # Handle abbreviated cities (e.g., "South SF" → "South San Francisco")
            city_mapping = {
                'South SF': 'South San Francisco',
                'SF': 'San Francisco',
                'SJ': 'San Jose'
            }
            city_part = city_mapping.get(city_part, city_part)

            # Check if it's a Bay Area city
            if city_part in BAY_AREA_CITIES:
                city = city_part

        # Skip if not a Bay Area city
        if not city:
            continue

        # Extract description
        description = description_td.get_text(strip=True)

        companies.append({
            'company_name': company_name,
            'source_url': BIOPHARMGUY_URL,
            'city': city,
            'focus_area': description,
            'notes': 'From BioPharmGuy Northern California directory'
        })

    return companies


def deduplicate_companies(companies):
    """Remove duplicate companies by name."""
    seen = {}
    deduplicated = []

    for company in companies:
        name = company['company_name'].strip()
        # Use lowercase for comparison to catch case variations
        name_lower = name.lower()

        if name_lower not in seen:
            seen[name_lower] = True
            deduplicated.append(company)

    return deduplicated


def main():
    """Main extraction workflow."""
    print("="*70)
    print("BioPharmGuy Company Extraction")
    print("="*70)
    print()

    print(f"Fetching: BioPharmGuy Northern California Directory")
    print(f"URL: {BIOPHARMGUY_URL}")

    soup = fetch_biopharmguy_page(BIOPHARMGUY_URL)
    if not soup:
        print("  ⚠️  Failed to fetch page")
        return

    # Extract companies
    companies = extract_companies_from_biopharmguy(soup)
    print(f"  ✓ Extracted {len(companies)} companies\n")

    # Deduplicate
    deduplicated = deduplicate_companies(companies)
    print(f"After deduplication: {len(deduplicated)} companies")

    # Sort by company name
    deduplicated.sort(key=lambda x: x['company_name'])

    # Write to CSV
    output_dir = Path('../data/working')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'biopharmguy_companies.csv'

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Company Name', 'Source URL', 'City', 'Focus Area', 'Notes'])
        writer.writeheader()

        for company in deduplicated:
            writer.writerow({
                'Company Name': company['company_name'],
                'Source URL': company['source_url'],
                'City': company['city'],
                'Focus Area': company['focus_area'],
                'Notes': company['notes']
            })

    print()
    print(f"✓ Saved to: {output_file}")
    print()
    print("Next steps:")
    print("1. Review the CSV and remove non-biotech companies")
    print("2. Manually add: Website, Address, Company Stage")
    print("3. Merge with Wikipedia data and existing data/final/companies.csv")
    print()


if __name__ == '__main__':
    main()
