#!/usr/bin/env python3
"""
Dataset expansion using public APIs and databases
Focus on verifiable, structured data sources
"""

import requests
import json
import time
import csv
from typing import List, Dict, Set
import re
import os

class BiotechDatasetExpander:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; DatasetExpander/1.0)'
        })
        self.existing_names = set()

    def load_existing_companies(self, csv_file: str) -> Set[str]:
        """Load existing company names"""
        existing = set()
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = self.normalize_name(row['Company Name'])
                    existing.add(name)
        except FileNotFoundError:
            pass
        return existing

    def normalize_name(self, name: str) -> str:
        """Normalize company name for comparison"""
        name = name.strip().lower()
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'[,.\-]', '', name)
        name = re.sub(r'\s+(inc|llc|corp|corporation|limited|ltd|company)$', '', name)
        return name

    def search_sec_edgar(self) -> List[Dict]:
        """
        Search SEC EDGAR for biotech companies
        Public companies filing with SEC
        """
        print("\n" + "="*70)
        print("SEARCHING: SEC EDGAR Database")
        print("="*70)

        companies = []

        try:
            # SEC EDGAR Company Search API
            # Search for companies with biotech-related SIC codes
            biotech_sic_codes = [
                '2834',  # Pharmaceutical Preparations
                '2835',  # In Vitro & In Vivo Diagnostic Substances
                '2836',  # Biological Products (No Diagnostic Substances)
                '3826',  # Laboratory Analytical Instruments
                '8731',  # Commercial Physical & Biological Research
            ]

            for sic in biotech_sic_codes:
                print(f"\nSearching SIC code: {sic}")

                # Note: This is a simplified approach
                # Full implementation would use SEC's EDGAR API
                print(f"  Would search SEC EDGAR for SIC {sic}")
                # companies.extend(self._query_sec_edgar(sic))

        except Exception as e:
            print(f"Error searching SEC EDGAR: {str(e)}")

        return companies

    def search_pitchbook_free(self) -> List[Dict]:
        """
        Search PitchBook free data
        Note: Full access requires subscription
        """
        print("\n" + "="*70)
        print("SEARCHING: PitchBook (Public Data)")
        print("="*70)

        print("Note: Full PitchBook access requires subscription")
        print("Using alternative approach...")

        return []

    def search_golden_biotech(self) -> List[Dict]:
        """
        Search Golden.com for biotech companies
        Golden has structured company data
        """
        print("\n" + "="*70)
        print("SEARCHING: Golden.com Biotech Database")
        print("="*70)

        companies = []

        try:
            # Golden API (if available)
            # This would require API key
            print("Note: Golden.com API access requires authentication")

        except Exception as e:
            print(f"Error searching Golden: {str(e)}")

        return companies

    def search_ncbi_biotech_companies(self) -> List[Dict]:
        """
        Search NCBI databases for biotech companies
        Companies mentioned in publications, clinical trials
        """
        print("\n" + "="*70)
        print("SEARCHING: NCBI/PubMed for Biotech Companies")
        print("="*70)

        companies = []

        try:
            # Search PubMed for company affiliations
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

            search_terms = [
                "biotechnology company California",
                "biotech startup California",
                "pharmaceutical company California"
            ]

            for term in search_terms:
                params = {
                    'db': 'pubmed',
                    'term': term,
                    'retmax': 100,
                    'retmode': 'json'
                }

                response = self.session.get(base_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Would need to parse author affiliations
                    print(f"  Found {len(data.get('esearchresult', {}).get('idlist', []))} publications")

                time.sleep(0.5)

        except Exception as e:
            print(f"Error searching NCBI: {str(e)}")

        return companies

    def search_clinicaltrials_gov(self) -> List[Dict]:
        """
        Search ClinicalTrials.gov for companies running trials in California
        """
        print("\n" + "="*70)
        print("SEARCHING: ClinicalTrials.gov")
        print("="*70)

        companies = []

        try:
            # ClinicalTrials.gov API
            base_url = "https://clinicaltrials.gov/api/query/study_fields"

            params = {
                'expr': 'AREA[LocationState]California AND AREA[LeadSponsorClass]INDUSTRY',
                'fields': 'LeadSponsorName,LocationCity,LocationState',
                'max_rnk': 1000,
                'fmt': 'json'
            }

            print("Querying ClinicalTrials.gov API...")
            response = self.session.get(base_url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()

                studies = data.get('StudyFieldsResponse', {}).get('StudyFields', [])
                print(f"Found {len(studies)} trials")

                seen_sponsors = set()

                for study in studies:
                    sponsor = study.get('LeadSponsorName', [None])[0]
                    city = study.get('LocationCity', [None])[0]

                    if sponsor and sponsor not in seen_sponsors:
                        seen_sponsors.add(sponsor)

                        company_data = {
                            'Company Name': sponsor,
                            'Website': '',
                            'City': city if isinstance(city, str) else '',
                            'Address': '',
                            'Description': 'Clinical trial sponsor',
                            'Focus Areas': 'Clinical Development',
                            'Source': 'ClinicalTrials.gov'
                        }

                        companies.append(company_data)

                print(f"Extracted {len(companies)} unique sponsors")

        except Exception as e:
            print(f"Error searching ClinicalTrials.gov: {str(e)}")

        return companies

    def search_fda_establishments(self) -> List[Dict]:
        """
        Search FDA establishment database
        Companies registered with FDA
        """
        print("\n" + "="*70)
        print("SEARCHING: FDA Establishment Database")
        print("="*70)

        companies = []

        try:
            # FDA maintains registration databases
            # openFDA API
            base_url = "https://api.fda.gov/device/registrationlisting.json"

            # Search California establishments
            params = {
                'search': 'proprietary_name:"*" AND registration.address.state_code:CA',
                'limit': 100
            }

            print("Querying openFDA API...")
            response = self.session.get(base_url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])

                print(f"Found {len(results)} FDA registrations")

                for result in results:
                    reg = result.get('registration', {})
                    name = reg.get('name')
                    address = reg.get('address', {})

                    if name:
                        company_data = {
                            'Company Name': name,
                            'Website': '',
                            'City': address.get('city', ''),
                            'Address': f"{address.get('address_line_1', '')}, {address.get('city', '')}, CA {address.get('postal_code', '')}",
                            'Description': 'FDA-registered establishment',
                            'Focus Areas': 'Medical Devices',
                            'Source': 'FDA'
                        }
                        companies.append(company_data)

        except Exception as e:
            print(f"Error searching FDA: {str(e)}")

        return companies


def expand_dataset_from_apis(existing_csv: str = 'data/final/companies.csv',
                             output_csv: str = 'data/working/api_companies.csv'):
    """Main function to expand dataset using APIs"""

    expander = BiotechDatasetExpander()

    print("\n" + "="*70)
    print("DATASET EXPANSION - PUBLIC API SOURCES")
    print("="*70)

    # Load existing companies
    expander.existing_names = expander.load_existing_companies(existing_csv)
    print(f"Loaded {len(expander.existing_names)} existing companies\n")

    all_companies = []

    # Search each API source
    sources = [
        ('ClinicalTrials.gov', expander.search_clinicaltrials_gov),
        ('FDA Establishments', expander.search_fda_establishments),
        ('NCBI/PubMed', expander.search_ncbi_biotech_companies),
    ]

    for source_name, search_func in sources:
        try:
            companies = search_func()
            all_companies.extend(companies)
            print(f"\nAdded {len(companies)} companies from {source_name}")
            time.sleep(2)
        except Exception as e:
            print(f"Error with {source_name}: {str(e)}")

    # Deduplicate against existing
    unique_companies = []
    seen = expander.existing_names.copy()

    for company in all_companies:
        normalized = expander.normalize_name(company['Company Name'])
        if normalized not in seen and len(normalized) > 2:
            seen.add(normalized)
            unique_companies.append(company)

    print(f"\n" + "="*70)
    print(f"DEDUPLICATION COMPLETE")
    print(f"="*70)
    print(f"Total found: {len(all_companies)}")
    print(f"Unique new companies: {len(unique_companies)}")

    # Save results
    if unique_companies:
        fieldnames = ['Company Name', 'Website', 'City', 'Address',
                     'Description', 'Focus Areas', 'Source']

        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_companies)

        print(f"Saved to: {output_csv}")

    return unique_companies


if __name__ == '__main__':
    expand_dataset_from_apis()
