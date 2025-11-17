#!/usr/bin/env python3
"""
Autonomous web scraper for California biotech companies
Scrapes multiple sources to expand the dataset
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import csv
from typing import List, Dict, Set
import re
from urllib.parse import urljoin, urlparse

class BiotechCompanyScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.companies = []
        self.company_names = set()  # Prevent duplicates

    def scrape_clsa_members(self) -> List[Dict]:
        """Scrape California Life Sciences Association member directory"""

        print("\n" + "="*70)
        print("SCRAPING: California Life Sciences Association (CLSA)")
        print("="*70)

        # CLSA member directory
        # Note: This may require API access or login
        # Implementing a fallback approach

        companies = []

        try:
            # Try the public member directory
            url = "https://www.califesciences.org/member-directory/"

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for company listings
            # This is a generic pattern - actual structure may vary
            company_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'member|company|listing'))

            print(f"Found {len(company_elements)} potential member elements")

            for element in company_elements[:100]:  # Limit to first 100
                company_data = self._extract_company_from_element(element)
                if company_data:
                    companies.append(company_data)

            print(f"Extracted {len(companies)} companies from CLSA")

        except Exception as e:
            print(f"Error scraping CLSA: {str(e)}")
            print("CLSA scraping may require authentication or API access")

        return companies

    def scrape_biocom_california(self) -> List[Dict]:
        """Scrape Biocom California member listings"""

        print("\n" + "="*70)
        print("SCRAPING: Biocom California")
        print("="*70)

        companies = []

        try:
            # Biocom member directory
            url = "https://www.biocom.org/member-directory/"

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract company information
            company_elements = soup.find_all(['div', 'article'], class_=re.compile(r'member|company'))

            print(f"Found {len(company_elements)} potential member elements")

            for element in company_elements[:100]:
                company_data = self._extract_company_from_element(element)
                if company_data:
                    companies.append(company_data)

            print(f"Extracted {len(companies)} companies from Biocom")

        except Exception as e:
            print(f"Error scraping Biocom: {str(e)}")
            print("Biocom scraping may require authentication")

        return companies

    def scrape_uc_tech_transfer(self) -> List[Dict]:
        """Scrape UC tech transfer company portfolios"""

        print("\n" + "="*70)
        print("SCRAPING: UC Tech Transfer Portfolios")
        print("="*70)

        companies = []

        # UC campuses with biotech programs
        uc_sources = [
            ('https://techtransfer.universityofcalifornia.edu/technology-search', 'UC System'),
            ('https://innovation.ucsf.edu/', 'UCSF'),
            ('https://innovation.ucdavis.edu/', 'UC Davis'),
            ('https://innovation.ucla.edu/', 'UCLA'),
            ('https://otl.ucsd.edu/', 'UC San Diego'),
        ]

        for url, campus in uc_sources:
            try:
                print(f"\nScraping: {campus}")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Look for company or startup listings
                company_elements = soup.find_all(['div', 'article', 'li'],
                                                class_=re.compile(r'startup|company|portfolio|spin'))

                print(f"  Found {len(company_elements)} potential elements")

                for element in company_elements[:50]:
                    company_data = self._extract_company_from_element(element)
                    if company_data:
                        company_data['Source'] = f'UC_{campus.replace(" ", "_")}'
                        companies.append(company_data)

                time.sleep(2)  # Be polite

            except Exception as e:
                print(f"  Error scraping {campus}: {str(e)}")

        print(f"\nTotal companies from UC tech transfer: {len(companies)}")
        return companies

    def scrape_vc_portfolios(self) -> List[Dict]:
        """Scrape California VC portfolio companies in biotech"""

        print("\n" + "="*70)
        print("SCRAPING: California VC Portfolio Companies")
        print("="*70)

        companies = []

        # Major California biotech VCs
        vc_firms = [
            ('https://www.a16z.bio/portfolio/', 'a16z Bio'),
            ('https://www.versantventures.com/portfolio/', 'Versant Ventures'),
            ('https://www.thirdrockvntures.com/portfolio/', 'Third Rock Ventures'),
            ('https://www.fmrc.com/portfolio/', 'FMRC'),
            ('https://www.flagship.com/companies', 'Flagship Pioneering'),
        ]

        for url, vc_name in vc_firms:
            try:
                print(f"\nScraping: {vc_name}")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Look for portfolio companies
                company_elements = soup.find_all(['div', 'article', 'li'],
                                                class_=re.compile(r'portfolio|company|investment'))

                print(f"  Found {len(company_elements)} potential elements")

                for element in company_elements[:50]:
                    company_data = self._extract_company_from_element(element)
                    if company_data:
                        company_data['Source'] = f'VC_{vc_name.replace(" ", "_")}'
                        companies.append(company_data)

                time.sleep(2)  # Be polite

            except Exception as e:
                print(f"  Error scraping {vc_name}: {str(e)}")

        print(f"\nTotal companies from VC portfolios: {len(companies)}")
        return companies

    def scrape_crunchbase_biotech_ca(self) -> List[Dict]:
        """
        Scrape Crunchbase for California biotech companies
        Note: Requires Crunchbase API access for best results
        """

        print("\n" + "="*70)
        print("SCRAPING: Crunchbase (Public Data)")
        print("="*70)

        companies = []

        # This would require Crunchbase API key for full access
        # Using public search as fallback

        try:
            # Public search for California biotech
            url = "https://www.crunchbase.com/discover/organization.companies"

            # This is a placeholder - actual implementation would need:
            # 1. Crunchbase API key
            # 2. Proper API endpoints
            # 3. Filtering by location=California, industry=Biotechnology

            print("Note: Full Crunchbase access requires API key")
            print("Skipping Crunchbase scraping in this implementation")

        except Exception as e:
            print(f"Error accessing Crunchbase: {str(e)}")

        return companies

    def _extract_company_from_element(self, element) -> Dict:
        """Extract company information from HTML element"""

        try:
            # Try to find company name
            name = None
            website = None
            city = None
            description = None

            # Look for name in various tags
            name_elem = (element.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'name|title|company')) or
                        element.find('a', href=True))

            if name_elem:
                name = name_elem.get_text(strip=True)

                # Get website from link
                if name_elem.name == 'a' and name_elem.get('href'):
                    href = name_elem['href']
                    if href.startswith('http'):
                        website = href
                    elif not href.startswith('#') and not href.startswith('javascript'):
                        # Relative URL - would need base URL
                        pass

            # Look for location
            location_elem = element.find(['span', 'div', 'p'], class_=re.compile(r'location|city|address'))
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                # Extract California city
                ca_cities = ['San Francisco', 'San Diego', 'Los Angeles', 'Irvine',
                           'South San Francisco', 'Carlsbad', 'Palo Alto', 'Berkeley']
                for city_name in ca_cities:
                    if city_name.lower() in location_text.lower():
                        city = city_name
                        break

            # Look for description
            desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|summary|about'))
            if desc_elem:
                description = desc_elem.get_text(strip=True)[:500]  # Limit length

            if name and len(name) > 2:
                return {
                    'Company Name': name,
                    'Website': website or '',
                    'City': city or '',
                    'Address': '',
                    'Description': description or '',
                    'Focus Areas': 'Biotechnology',
                    'Source': 'Web_Scraping'
                }

        except Exception as e:
            pass

        return None

    def load_existing_companies(self, csv_file: str) -> Set[str]:
        """Load existing company names to avoid duplicates"""

        existing = set()
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Normalize company name for comparison
                    name = row['Company Name'].strip().lower()
                    name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
                    name = re.sub(r'[,.\-]', '', name)  # Remove punctuation
                    existing.add(name)
        except FileNotFoundError:
            pass

        print(f"Loaded {len(existing)} existing companies")
        return existing

    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for duplicate detection"""
        name = name.strip().lower()
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'[,.\-]', '', name)
        # Remove common suffixes
        name = re.sub(r'\s+(inc|llc|corp|corporation|limited|ltd)$', '', name)
        return name

    def deduplicate_companies(self, companies: List[Dict],
                             existing_names: Set[str]) -> List[Dict]:
        """Remove duplicate companies"""

        unique = []
        seen = existing_names.copy()

        for company in companies:
            name = self.normalize_company_name(company['Company Name'])

            if name not in seen and len(name) > 2:
                seen.add(name)
                unique.append(company)

        print(f"Deduplication: {len(companies)} -> {len(unique)} unique companies")
        return unique


def scrape_all_sources(existing_csv: str = 'data/final/companies.csv',
                      output_csv: str = 'data/working/new_companies.csv'):
    """Scrape all sources and compile new companies"""

    scraper = BiotechCompanyScraper()

    print("\n" + "="*70)
    print("AUTONOMOUS BIOTECH COMPANY DATASET EXPANSION")
    print("="*70)

    # Load existing companies to avoid duplicates
    existing_names = scraper.load_existing_companies(existing_csv)

    all_new_companies = []

    # Scrape each source
    sources = [
        ('CLSA', scraper.scrape_clsa_members),
        ('Biocom', scraper.scrape_biocom_california),
        ('UC Tech Transfer', scraper.scrape_uc_tech_transfer),
        ('VC Portfolios', scraper.scrape_vc_portfolios),
    ]

    for source_name, scrape_func in sources:
        print(f"\n{'='*70}")
        print(f"Processing: {source_name}")
        print(f"{'='*70}")

        try:
            companies = scrape_func()
            all_new_companies.extend(companies)
            print(f"Added {len(companies)} companies from {source_name}")
            time.sleep(3)  # Be polite between sources
        except Exception as e:
            print(f"Error with {source_name}: {str(e)}")

    # Deduplicate
    unique_companies = scraper.deduplicate_companies(all_new_companies, existing_names)

    # Save to CSV
    if unique_companies:
        fieldnames = ['Company Name', 'Website', 'City', 'Address', 'Description',
                     'Focus Areas', 'Source']

        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_companies)

        print(f"\n{'='*70}")
        print(f"SCRAPING COMPLETE")
        print(f"{'='*70}")
        print(f"Total new companies found: {len(unique_companies)}")
        print(f"Saved to: {output_csv}")
    else:
        print("\nNo new companies found")

    return unique_companies


if __name__ == '__main__':
    scrape_all_sources()
