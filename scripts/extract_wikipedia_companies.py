#!/usr/bin/env python3
"""
Extract biotech/pharma company names from Wikipedia sources.

This script implements Phase 1 of the East Bay Biotech Map methodology:
automated extraction from Wikipedia's biotechnology and pharmaceutical company lists.

Usage:
    python3 extract_wikipedia_companies.py

Output:
    data/working/wikipedia_companies.csv

Author: Jaden Shirkey
Date: January 2025
"""

import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
from pathlib import Path

# Path constants (script-relative paths)
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
DATA_WORKING = REPO_ROOT / 'data' / 'working'
DATA_FINAL = REPO_ROOT / 'data' / 'final'

# Wikipedia sources per methodology
WIKIPEDIA_SOURCES = [
    {
        'name': 'Biotech Companies List',
        'url': 'https://en.wikipedia.org/wiki/List_of_biotechnology_companies',
        'type': 'table'
    },
    {
        'name': 'Pharma Companies Category',
        'url': 'https://en.wikipedia.org/wiki/Category:Pharmaceutical_companies_of_the_United_States',
        'type': 'category'
    },
    {
        'name': 'Bay Area Companies Category',
        'url': 'https://en.wikipedia.org/wiki/Category:Companies_based_in_the_San_Francisco_Bay_Area',
        'type': 'category'
    }
]

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


def fetch_wikipedia_page(url):
    """Fetch Wikipedia page content."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; EastBayBiotechMap/1.0; Educational Research)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_from_table(soup):
    """Extract companies from Wikipedia table format."""
    companies = []
    tables = soup.find_all('table', class_='wikitable')

    for table in tables:
        rows = table.find_all('tr')[1:]  # Skip header row
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue

            # First cell usually contains company name
            first_cell = cells[0]
            link = first_cell.find('a')
            if link and link.get('href'):
                company_name = link.get_text(strip=True)
                wiki_url = 'https://en.wikipedia.org' + link['href']

                # Try to extract city/location from row
                city = ''
                for cell in cells:
                    text = cell.get_text(strip=True)
                    for bay_city in BAY_AREA_CITIES:
                        if bay_city in text:
                            city = bay_city
                            break
                    if city:
                        break

                companies.append({
                    'company_name': company_name,
                    'source_url': wiki_url,
                    'city': city,
                    'notes': 'From Wikipedia table'
                })

    return companies


def extract_from_category(soup):
    """Extract companies from Wikipedia category page."""
    companies = []

    # Category pages have two sections: Subcategories and Pages
    # We want only the "Pages" section (id="mw-pages")
    pages_section = soup.find('div', id='mw-pages')

    if pages_section:
        # Find the mw-category div within mw-pages
        category_div = pages_section.find('div', class_='mw-category')

        if category_div:
            links = category_div.find_all('a')
            for link in links:
                href = link.get('href', '')

                # Skip if not a wiki page or if it's a category page
                if not href.startswith('/wiki/'):
                    continue
                if '/wiki/Category:' in href:
                    continue

                company_name = link.get_text(strip=True)
                wiki_url = 'https://en.wikipedia.org' + href

                companies.append({
                    'company_name': company_name,
                    'source_url': wiki_url,
                    'city': '',  # Categories don't usually include location
                    'notes': 'From Wikipedia category'
                })

    return companies


def is_bay_area_company(company_name, city):
    """Check if company appears to be Bay Area based."""
    # If we found a Bay Area city in the data, it's valid
    if city and city in BAY_AREA_CITIES:
        return True

    # Check if company name mentions Bay Area location
    name_lower = company_name.lower()
    for city_name in BAY_AREA_CITIES:
        if city_name.lower() in name_lower:
            return True

    # Default to including it (manual filtering later)
    return True


def deduplicate_companies(companies):
    """Remove duplicate companies by name."""
    seen = {}
    deduplicated = []

    for company in companies:
        name = company['company_name'].strip()
        if name not in seen:
            seen[name] = True
            deduplicated.append(company)

    return deduplicated


def main():
    """Main extraction workflow."""
    print("="*70)
    print("Wikipedia Company Extraction")
    print("="*70)
    print()

    all_companies = []

    # Extract from each source
    for source in WIKIPEDIA_SOURCES:
        print(f"Fetching: {source['name']}")
        print(f"URL: {source['url']}")

        soup = fetch_wikipedia_page(source['url'])
        if not soup:
            print(f"  ⚠️  Failed to fetch page\n")
            continue

        # Extract based on page type
        if source['type'] == 'table':
            companies = extract_from_table(soup)
        else:  # category
            companies = extract_from_category(soup)

        print(f"  ✓ Extracted {len(companies)} companies\n")
        all_companies.extend(companies)

    print(f"Total companies extracted: {len(all_companies)}")

    # Deduplicate
    deduplicated = deduplicate_companies(all_companies)
    print(f"After deduplication: {len(deduplicated)} companies")

    # Filter for Bay Area (loose filter - keep most for manual review)
    bay_area = [c for c in deduplicated if is_bay_area_company(c['company_name'], c['city'])]
    print(f"Bay Area candidates: {len(bay_area)} companies")

    # Sort by company name
    bay_area.sort(key=lambda x: x['company_name'])

    # Write to CSV
    output_dir = DATA_WORKING
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'wikipedia_companies.csv'

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Company Name', 'Source URL', 'City', 'Notes'])
        writer.writeheader()

        for company in bay_area:
            writer.writerow({
                'Company Name': company['company_name'],
                'Source URL': company['source_url'],
                'City': company['city'],
                'Notes': company['notes']
            })

    print()
    print(f"✓ Saved to: {output_file}")
    print()
    print("Next steps:")
    print("1. Review the CSV and remove non-biotech companies")
    print("2. Manually add: Website, Address, Company Stage, Focus Areas")
    print("3. Merge with existing data/final/companies.csv")
    print()


if __name__ == '__main__':
    main()
