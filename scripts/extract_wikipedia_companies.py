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
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

# Path constants (script-relative paths)
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
DATA_WORKING = REPO_ROOT / 'data' / 'working'
DATA_FINAL = REPO_ROOT / 'data' / 'final'

# Add parent directory to path for imports
sys.path.insert(0, str(REPO_ROOT))
from utils.helpers import is_aggregator

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
                    'website': '',  # Will be extracted later with API call
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
                    'website': '',  # Will be extracted later with API call
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


def extract_website_from_wikipedia_api(page_title):
    """
    Extract official website from Wikipedia page using External Links API.

    Returns the most likely official website URL, or empty string if not found.
    """
    try:
        # Extract page name from full Wikipedia URL if needed
        if 'wikipedia.org/wiki/' in page_title:
            page_title = page_title.split('/wiki/')[-1]

        # Wikipedia API endpoint
        api_url = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'parse',
            'page': unquote(page_title),  # Decode URL-encoded titles
            'prop': 'externallinks',
            'format': 'json',
            'formatversion': 2
        }

        # Include User-Agent header (required by Wikipedia API)
        headers = {
            'User-Agent': 'EastBayBiotechMap/1.0 (Educational Research; https://github.com/jadenshirkey/EastBayBiotechMap)'
        }

        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'error' in data:
            return ''

        if 'parse' not in data:
            return ''

        external_links = data['parse'].get('externallinks', [])

        # Additional patterns to exclude (beyond what is_aggregator handles)
        exclude_patterns = [
            'archive.org', 'web.archive.org',  # Archive sites (handled separately in fallback)
            'doi.org', 'pubmed', 'ncbi.nlm',  # Scientific references
            'sec.gov', 'edgar',  # SEC filings
            'reuters.com', 'bloomberg.com', 'forbes.com', 'fortune.com',  # News sites
            'nytimes.com', 'wsj.com', 'washingtonpost.com',
            'semanticscholar.org', 'scholar.google',  # Academic
            'github.com', 'gitlab.com',  # Code repositories (usually not company sites)
            '.pdf', '.doc', '.xls',  # Direct file downloads
            'geohack.toolforge.org',  # Geographic coordinates tool
            '/media/', '/news/', '/press/',  # Skip deep links to news sections
            'marketwatch.com', 'yahoo.com',  # Financial news
            'biotickr.com',  # Generic biotech ticker site
            'businesswire.com', 'prnewswire.com',  # Press release sites
            'drugs.com', 'drugbank.ca',  # Drug databases
            'bizjournals.com', 'fiercebiotech.com',  # Industry news
            'pharmaintelligence.informa.com',  # Industry database
            'google.com/search', 'jstor.org'  # Search engines
        ]

        # Collect all potentially valid websites
        potential_websites = []
        for link in external_links:
            url = link if isinstance(link, str) else link.get('url', '')

            # Skip if empty
            if not url:
                continue

            # Skip aggregators using our helper
            if is_aggregator(url):
                continue

            # Skip excluded patterns
            if any(pattern in url.lower() for pattern in exclude_patterns):
                continue

            potential_websites.append(url)

        # Strategy: prefer root domains over deep links
        # Extract base domains and return the first one that looks like a company site
        for url in potential_websites:
            # Extract domain from URL
            from urllib.parse import urlparse
            parsed = urlparse(url)

            # Prefer URLs that are at the root or have simple paths like /about-us
            path = parsed.path.rstrip('/')
            if path == '' or path in ['/about', '/about-us', '/company', '/home']:
                return url

        # If no root domain found, return the first valid URL
        if potential_websites:
            return potential_websites[0]

        # Fallback: Check for archived company websites (defunct companies)
        # Extract original URL from archive.org links
        import re
        for link in external_links:
            if 'archive.org/web/' in link:
                # Extract original URL from archive link
                # Format: https://web.archive.org/web/[timestamp]/[original_url]
                match = re.search(r'archive\.org/web/\d+/(.+)', link)
                if match:
                    original_url = match.group(1)
                    # Ensure it has http:// or https://
                    if not original_url.startswith(('http://', 'https://')):
                        original_url = 'http://' + original_url
                    # Ensure it's not another aggregator or excluded site
                    if not is_aggregator(original_url):
                        if not any(pattern in original_url.lower() for pattern in exclude_patterns):
                            # Return the original URL (note: site may be defunct)
                            return original_url

        return ''

    except Exception as e:
        # Silently handle errors - we'll just not have a website for this company
        return ''


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

    # Extract websites from Wikipedia pages
    print("\nExtracting websites from Wikipedia pages...")
    print("(This may take a minute due to rate limiting)")
    websites_found = 0
    for i, company in enumerate(bay_area):
        # Extract website using Wikipedia API
        website = extract_website_from_wikipedia_api(company['source_url'])
        if website:
            company['website'] = website
            websites_found += 1

        # Progress indicator every 25 companies
        if (i + 1) % 25 == 0:
            print(f"  Processed {i + 1}/{len(bay_area)} companies...")

        # Rate limiting: 0.1 second delay between API calls
        time.sleep(0.1)

    print(f"  ✓ Found websites for {websites_found}/{len(bay_area)} companies ({100*websites_found/len(bay_area):.1f}%)")
    print()

    # Sort by company name
    bay_area.sort(key=lambda x: x['company_name'])

    # Write to CSV
    output_dir = DATA_WORKING
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'wikipedia_companies.csv'

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Company Name', 'Website', 'Source URL', 'City', 'Notes'])
        writer.writeheader()

        for company in bay_area:
            writer.writerow({
                'Company Name': company['company_name'],
                'Website': company.get('website', ''),
                'Source URL': company['source_url'],
                'City': company['city'],
                'Notes': company['notes']
            })

    print()
    print(f"✓ Saved to: {output_file}")
    print()
    print("Next steps:")
    print("1. Review the CSV and remove non-biotech companies")
    print("2. Merge with BioPharmGuy data using merge_company_sources.py")
    print("3. Companies with websites can use Path A enrichment (automated)")
    print("4. Companies without websites will use Path B enrichment (AI-assisted)")
    print()


if __name__ == '__main__':
    main()
