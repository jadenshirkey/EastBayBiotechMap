#!/usr/bin/env python3
"""
Extract biotech/pharma company names from BioPharmGuy directory.

This script implements Phase 1 (Stage A) of the V4.3 East Bay Biotech Map methodology:
automated extraction from BioPharmGuy's California-wide company listings.

Changes from V4.2:
- Extract ALL California companies (no early filtering for Bay Area)
- Capture Website field from external link
- Add HTML caching with 7-day TTL
- Add extraction validation
- Output to bpg_ca_raw.csv

Usage:
    python3 extract_biopharmguy_companies.py

Output:
    data/working/bpg_ca_raw.csv

Author: Jaden Shirkey
Date: January 2025
Version: V4.3 Stage-A
"""

import requests
from bs4 import BeautifulSoup
import csv
import re
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Import URL standardizer
import sys
sys.path.append(str(Path(__file__).parent.parent))
from scripts.utils.url_standardizer import standardize_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# BioPharmGuy source - CA-wide (not just Northern CA)
BIOPHARMGUY_URL = 'https://biopharmguy.com/links/state-ca-all-geo.php'

# User-Agent for respectful scraping
USER_AGENT = 'BayAreaBiotechMap/4.3 (Research Project; https://github.com/jadenshirkey/EastBayBiotechMap)'

# Cache settings
CACHE_DIR = Path(__file__).parent.parent / 'data' / 'cache'
CACHE_TTL_DAYS = 7


def get_cache_path():
    """Get the cache file path for today's date."""
    date_str = datetime.now().strftime('%Y%m%d')
    return CACHE_DIR / f'bpg_ca_{date_str}.html'


def load_cached_html():
    """Load cached HTML if it exists and is less than 7 days old."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Check for any cache files
    for cache_file in CACHE_DIR.glob('bpg_ca_*.html'):
        # Extract date from filename
        match = re.search(r'bpg_ca_(\d{8})\.html', cache_file.name)
        if match:
            date_str = match.group(1)
            cache_date = datetime.strptime(date_str, '%Y%m%d')
            age_days = (datetime.now() - cache_date).days

            if age_days < CACHE_TTL_DAYS:
                logger.info(f"Using cached HTML from {date_str} ({age_days} days old)")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.info(f"Cache file {cache_file.name} is {age_days} days old, expired")
                # Clean up old cache file
                cache_file.unlink()

    return None


def save_html_to_cache(html_content):
    """Save HTML content to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = get_cache_path()

    with open(cache_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"Saved HTML to cache: {cache_path}")


def fetch_biopharmguy_page(url):
    """Fetch BioPharmGuy page content with caching and retry logic."""
    # Try to load from cache first
    cached_html = load_cached_html()
    if cached_html:
        return BeautifulSoup(cached_html, 'html.parser')

    # Fetch from web with exponential backoff
    max_retries = 3
    backoff_delays = [0.5, 1.0, 2.0]

    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': USER_AGENT
            }
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            html_content = response.text

            # Save to cache
            save_html_to_cache(html_content)

            return BeautifulSoup(html_content, 'html.parser')

        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")

            if attempt < max_retries - 1:
                delay = backoff_delays[attempt]
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                return None

    return None


def is_valid_url(url):
    """Check if a string is a valid URL."""
    if not url or url.strip() == '':
        return True  # Empty is OK

    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_companies_from_biopharmguy(soup):
    """Extract ALL CA companies from BioPharmGuy state-ca-all-geo.php page."""
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

        # Extract company name and website from the links
        # First <a> tag: internal link to company.php
        # Second <a> tag: external link to company website
        links = company_td.find_all('a')
        if len(links) < 1:
            continue

        # Company name is in the second link if it exists, otherwise first link
        if len(links) >= 2:
            company_name = links[1].get_text(strip=True)
            # Website is the href from the second link
            website = links[1].get('href', '').strip()
            # Standardize the URL format
            website = standardize_url(website) or ''
        else:
            company_name = links[0].get_text(strip=True)
            website = ''

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
            city = city_mapping.get(city_part, city_part)
        else:
            # Try to extract city name from other formats
            city = location_text.replace('CA', '').strip(' -')

        # Extract description (Focus Area)
        focus_area = description_td.get_text(strip=True)

        # NO FILTERING - extract all CA companies
        companies.append({
            'Company Name': company_name,
            'Website': website,
            'City': city,
            'Focus Area': focus_area,
            'Source URL': BIOPHARMGUY_URL,
            'Notes': ''
        })

    return companies


def deduplicate_companies(companies):
    """Remove duplicate companies by name."""
    seen = {}
    deduplicated = []

    for company in companies:
        name = company['Company Name'].strip()
        # Use lowercase for comparison to catch case variations
        name_lower = name.lower()

        if name_lower not in seen:
            seen[name_lower] = True
            deduplicated.append(company)
        else:
            logger.warning(f"Duplicate company found: {name}")

    return deduplicated


def validate_extraction_output(companies):
    """
    Validate the extraction output meets quality requirements.

    Validation checks:
    - Output has > 0 rows
    - No duplicate Company Names
    - Website field is valid URL or empty string

    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []

    # Check 1: Must have at least one company
    if len(companies) == 0:
        errors.append("ERROR: Extraction produced 0 rows")
        return False, errors

    logger.info(f"✓ Validation: Extracted {len(companies)} companies")

    # Check 2: No duplicate names
    names = [c['Company Name'].strip().lower() for c in companies]
    duplicates = [name for name in set(names) if names.count(name) > 1]

    if duplicates:
        errors.append(f"ERROR: Found {len(duplicates)} duplicate company names")
        for dup in duplicates[:5]:  # Show first 5
            errors.append(f"  - Duplicate: {dup}")
        return False, errors

    logger.info(f"✓ Validation: No duplicate company names")

    # Check 3: Website field is valid URL or empty
    invalid_urls = []
    for company in companies:
        website = company['Website']
        if not is_valid_url(website):
            invalid_urls.append(f"{company['Company Name']}: {website}")

    if invalid_urls:
        errors.append(f"ERROR: Found {len(invalid_urls)} invalid URLs")
        for url in invalid_urls[:5]:  # Show first 5
            errors.append(f"  - {url}")
        return False, errors

    logger.info(f"✓ Validation: All Website fields are valid URLs or empty")

    # All checks passed
    return True, []


def main():
    """Main extraction workflow for V4.3 Stage-A."""
    logger.info("="*70)
    logger.info("BioPharmGuy Company Extraction - V4.3 Stage-A")
    logger.info("="*70)

    logger.info(f"Source: BioPharmGuy California-wide Directory")
    logger.info(f"URL: {BIOPHARMGUY_URL}")

    soup = fetch_biopharmguy_page(BIOPHARMGUY_URL)
    if not soup:
        logger.error("Failed to fetch page - aborting")
        return 1

    # Extract ALL CA companies (no filtering)
    logger.info("Extracting companies from HTML...")
    companies = extract_companies_from_biopharmguy(soup)
    logger.info(f"Initial extraction: {len(companies)} companies")

    # Deduplicate
    logger.info("Deduplicating companies...")
    deduplicated = deduplicate_companies(companies)
    logger.info(f"After deduplication: {len(deduplicated)} companies")

    # Calculate extraction statistics
    total_rows = len(deduplicated)
    rows_with_website = sum(1 for c in deduplicated if c['Website'].strip() != '')
    rows_without_website = total_rows - rows_with_website
    coverage_percentage = (rows_with_website / total_rows * 100) if total_rows > 0 else 0

    logger.info("")
    logger.info("Extraction Statistics:")
    logger.info(f"  Total companies extracted: {total_rows}")
    logger.info(f"  Companies with Website: {rows_with_website} ({coverage_percentage:.1f}%)")
    logger.info(f"  Companies without Website: {rows_without_website}")
    logger.info("")

    # Validate extraction output
    logger.info("Running validation checks...")
    is_valid, errors = validate_extraction_output(deduplicated)

    if not is_valid:
        logger.error("Validation failed:")
        for error in errors:
            logger.error(error)
        return 1

    logger.info("✓ All validation checks passed")

    # Sort by company name
    deduplicated.sort(key=lambda x: x['Company Name'])

    # Write to CSV
    output_dir = Path(__file__).parent.parent / 'data' / 'working'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'bpg_ca_raw.csv'

    fieldnames = ['Company Name', 'Website', 'City', 'Focus Area', 'Source URL', 'Notes']

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(deduplicated)

    logger.info("")
    logger.info(f"✓ Output saved to: {output_file}")
    logger.info("")
    logger.info("Next pipeline stage:")
    logger.info("  Stage-B: Merge with other sources and apply geofence filter")
    logger.info("  (scripts/merge_company_sources.py)")
    logger.info("")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
