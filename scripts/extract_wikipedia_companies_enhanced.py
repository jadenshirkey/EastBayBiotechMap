#!/usr/bin/env python3
"""
Enhanced Wikipedia company extraction with infobox metadata parsing.

Extracts additional metadata for early classification:
- traded_as (stock ticker/exchange)
- parent company
- defunct year
- founded year
- company type
- revenue
- number of employees

This enables classification BEFORE expensive API calls.

Author: Bay Area Biotech Map V5
Date: 2025-11-16
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path constants
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
DATA_WORKING = REPO_ROOT / 'data' / 'working'

# Wikipedia API endpoint
WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# Bay Area cities (simplified list)
BAY_AREA_CITIES = {
    'Alameda', 'Berkeley', 'Emeryville', 'Fremont', 'Oakland', 'Pleasanton',
    'San Francisco', 'South San Francisco', 'San Mateo', 'Redwood City',
    'Palo Alto', 'Mountain View', 'San Jose', 'Sunnyvale', 'Santa Clara',
    'Cupertino', 'Menlo Park', 'Foster City', 'San Carlos', 'Burlingame'
}


class EnhancedWikipediaExtractor:
    """Enhanced extractor with infobox parsing capabilities"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EastBayBiotechMap/2.0 (Educational Research)'
        })
        self.companies = []
        self.stats = {
            'total_extracted': 0,
            'with_ticker': 0,
            'with_parent': 0,
            'defunct': 0,
            'with_metadata': 0
        }

    def extract_infobox_data(self, wiki_url: str) -> Dict:
        """
        Extract structured data from Wikipedia infobox

        Returns dict with:
        - traded_as: Stock ticker and exchange
        - parent: Parent company
        - defunct: Year company became defunct
        - founded: Year founded
        - type: Public/Private company
        - revenue: Latest revenue
        - employees: Number of employees
        """
        metadata = {
            'traded_as': None,
            'parent': None,
            'defunct': None,
            'founded': None,
            'company_type': None,
            'revenue': None,
            'employees': None,
            'headquarters': None,
            'description': None
        }

        try:
            # Rate limiting
            time.sleep(0.5)

            # Fetch the page
            response = self.session.get(wiki_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the infobox
            infobox = soup.find('table', class_='infobox')
            if not infobox:
                # Try alternative infobox classes
                infobox = soup.find('table', class_=['infobox vcard', 'infobox biography vcard'])

            if infobox:
                rows = infobox.find_all('tr')

                for row in rows:
                    header = row.find('th')
                    if not header:
                        continue

                    header_text = header.get_text(strip=True).lower()
                    data = row.find('td')
                    if not data:
                        continue

                    data_text = data.get_text(strip=True)

                    # Extract traded_as (stock ticker)
                    if 'traded as' in header_text or 'ticker' in header_text:
                        metadata['traded_as'] = data_text
                        # Try to extract ticker symbol
                        ticker_match = re.search(r'([A-Z]+:\s*[A-Z]+)', data_text)
                        if ticker_match:
                            metadata['traded_as'] = ticker_match.group(1)
                        logger.debug(f"Found ticker: {metadata['traded_as']}")

                    # Extract parent company
                    elif 'parent' in header_text or 'owned by' in header_text:
                        parent_link = data.find('a')
                        if parent_link:
                            metadata['parent'] = parent_link.get_text(strip=True)
                        else:
                            metadata['parent'] = data_text

                    # Extract defunct status
                    elif 'defunct' in header_text or 'dissolved' in header_text:
                        metadata['defunct'] = data_text
                        # Try to extract year
                        year_match = re.search(r'(\d{4})', data_text)
                        if year_match:
                            metadata['defunct'] = year_match.group(1)

                    # Extract founded year
                    elif 'founded' in header_text or 'established' in header_text:
                        metadata['founded'] = data_text
                        year_match = re.search(r'(\d{4})', data_text)
                        if year_match:
                            metadata['founded'] = year_match.group(1)

                    # Extract company type
                    elif 'type' in header_text:
                        metadata['company_type'] = data_text

                    # Extract revenue
                    elif 'revenue' in header_text:
                        metadata['revenue'] = data_text

                    # Extract employees
                    elif 'employees' in header_text:
                        metadata['employees'] = data_text
                        # Try to extract number
                        num_match = re.search(r'([\d,]+)', data_text)
                        if num_match:
                            metadata['employees'] = num_match.group(1).replace(',', '')

                    # Extract headquarters
                    elif 'headquarters' in header_text or 'location' in header_text:
                        metadata['headquarters'] = data_text

            # Get first paragraph as description
            first_para = soup.find('p', class_=None)
            if first_para:
                metadata['description'] = first_para.get_text(strip=True)[:500]  # First 500 chars

        except Exception as e:
            logger.warning(f"Failed to extract infobox from {wiki_url}: {e}")

        return metadata

    def classify_from_metadata(self, metadata: Dict) -> str:
        """
        Early classification based on Wikipedia metadata

        Returns classification hint for use before API enrichment
        """
        # If has stock ticker -> Public
        if metadata.get('traded_as'):
            return 'Public'

        # If defunct -> Defunct
        if metadata.get('defunct'):
            return 'Defunct'

        # If has parent company -> likely acquired/subsidiary
        if metadata.get('parent'):
            return 'Private with SEC Filings'  # Many acquired companies file with SEC

        # If company type mentions public
        company_type = metadata.get('company_type', '').lower()
        if 'public' in company_type:
            return 'Public'
        elif 'private' in company_type:
            return 'Private'

        # Check description for clinical trials mentions
        description = metadata.get('description', '').lower()
        if any(phrase in description for phrase in ['clinical trial', 'phase i', 'phase ii', 'phase iii']):
            return 'Clinical Stage'

        return 'Unknown'

    def extract_from_list_page(self, url: str) -> List[Dict]:
        """Extract companies from a Wikipedia list page"""
        companies = []

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all tables with class wikitable
            tables = soup.find_all('table', class_='wikitable')

            for table in tables:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if not cells:
                        continue

                    # First cell usually has company name with link
                    first_cell = cells[0]
                    link = first_cell.find('a')
                    if link and link.get('href'):
                        company_name = link.get_text(strip=True)
                        wiki_url = 'https://en.wikipedia.org' + link['href']

                        # Extract location if present
                        location = None
                        for cell in cells[1:]:
                            text = cell.get_text(strip=True)
                            for city in BAY_AREA_CITIES:
                                if city in text:
                                    location = city
                                    break

                        companies.append({
                            'company_name': company_name,
                            'wiki_url': wiki_url,
                            'location': location
                        })

            logger.info(f"Extracted {len(companies)} companies from {url}")

        except Exception as e:
            logger.error(f"Failed to extract from {url}: {e}")

        return companies

    def process_companies(self, companies: List[Dict]):
        """Process companies and extract metadata"""
        enhanced_companies = []

        for i, company in enumerate(companies):
            if i % 10 == 0:
                logger.info(f"Processing company {i}/{len(companies)}")

            wiki_url = company.get('wiki_url')
            if not wiki_url:
                continue

            # Extract infobox metadata
            metadata = self.extract_infobox_data(wiki_url)

            # Get early classification
            early_classification = self.classify_from_metadata(metadata)

            # Combine data
            enhanced_company = {
                'company_name': company['company_name'],
                'wiki_url': wiki_url,
                'location': company.get('location', ''),
                'traded_as': metadata.get('traded_as'),
                'parent_company': metadata.get('parent'),
                'defunct': metadata.get('defunct'),
                'founded': metadata.get('founded'),
                'company_type': metadata.get('company_type'),
                'revenue': metadata.get('revenue'),
                'employees': metadata.get('employees'),
                'headquarters': metadata.get('headquarters'),
                'description': metadata.get('description'),
                'early_classification': early_classification,
                'metadata_json': json.dumps(metadata)
            }

            enhanced_companies.append(enhanced_company)

            # Update statistics
            self.stats['total_extracted'] += 1
            if metadata.get('traded_as'):
                self.stats['with_ticker'] += 1
            if metadata.get('parent'):
                self.stats['with_parent'] += 1
            if metadata.get('defunct'):
                self.stats['defunct'] += 1
            if any(metadata.values()):
                self.stats['with_metadata'] += 1

        return enhanced_companies

    def save_to_csv(self, companies: List[Dict], output_path: Path):
        """Save enhanced company data to CSV"""
        if not companies:
            logger.warning("No companies to save")
            return

        fieldnames = [
            'company_name', 'wiki_url', 'location', 'traded_as', 'parent_company',
            'defunct', 'founded', 'company_type', 'revenue', 'employees',
            'headquarters', 'description', 'early_classification', 'metadata_json'
        ]

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(companies)

        logger.info(f"Saved {len(companies)} companies to {output_path}")

    def print_statistics(self):
        """Print extraction statistics"""
        logger.info("\n" + "="*60)
        logger.info("EXTRACTION STATISTICS")
        logger.info("="*60)
        logger.info(f"Total companies extracted: {self.stats['total_extracted']}")
        logger.info(f"Companies with stock ticker: {self.stats['with_ticker']}")
        logger.info(f"Companies with parent company: {self.stats['with_parent']}")
        logger.info(f"Defunct companies: {self.stats['defunct']}")
        logger.info(f"Companies with metadata: {self.stats['with_metadata']}")

        if self.stats['total_extracted'] > 0:
            ticker_pct = self.stats['with_ticker'] / self.stats['total_extracted'] * 100
            metadata_pct = self.stats['with_metadata'] / self.stats['total_extracted'] * 100
            logger.info(f"\nTicker coverage: {ticker_pct:.1f}%")
            logger.info(f"Metadata coverage: {metadata_pct:.1f}%")
        logger.info("="*60)


def main():
    """Main entry point"""
    logger.info("Starting Enhanced Wikipedia Extraction")
    logger.info("Extracting infobox metadata for early classification")

    # Wikipedia sources
    sources = [
        'https://en.wikipedia.org/wiki/List_of_biotechnology_companies',
        'https://en.wikipedia.org/wiki/List_of_pharmaceutical_companies'
    ]

    extractor = EnhancedWikipediaExtractor()

    # Extract companies from list pages
    all_companies = []
    for source_url in sources:
        companies = extractor.extract_from_list_page(source_url)
        all_companies.extend(companies)

    # Remove duplicates
    seen = set()
    unique_companies = []
    for company in all_companies:
        name = company['company_name']
        if name not in seen:
            seen.add(name)
            unique_companies.append(company)

    logger.info(f"Found {len(unique_companies)} unique companies")

    # Process and enhance with metadata
    enhanced_companies = extractor.process_companies(unique_companies[:50])  # Limit for testing

    # Save results
    output_path = DATA_WORKING / 'wikipedia_companies_enhanced.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    extractor.save_to_csv(enhanced_companies, output_path)

    # Print statistics
    extractor.print_statistics()

    logger.info(f"\n✓ Enhanced extraction complete!")
    logger.info(f"✓ Output: {output_path}")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())