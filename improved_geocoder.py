#!/usr/bin/env python3
"""
Improved geocoding with multiple fallback strategies
"""

import os
import time
import json
import requests
from typing import Dict, Optional, Tuple
import csv

class ImprovedGeocoder:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('GOOGLE_MAPS_API_KEY')
        self.base_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        self.geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.cache = {}
        self.request_count = 0
        self.max_requests_per_minute = 50

    def rate_limit(self):
        """Simple rate limiting"""
        self.request_count += 1
        if self.request_count % self.max_requests_per_minute == 0:
            print(f"Rate limiting: sleeping 60s after {self.request_count} requests")
            time.sleep(60)
        else:
            time.sleep(0.1)  # Small delay between requests

    def geocode_with_fallback(self, company_name: str, address: str = None,
                             city: str = None, website: str = None) -> Dict:
        """
        Try multiple strategies to geocode a company:
        1. Full address if available
        2. Company name + city
        3. Company name + "California"
        4. Extract address from website (if implemented)
        """

        strategies = []

        # Strategy 1: Full address
        if address and address.strip():
            strategies.append(('full_address', f"{address}"))

        # Strategy 2: Company name + city
        if city and city.strip():
            strategies.append(('name_city', f"{company_name}, {city}, CA"))

        # Strategy 3: Company name + California
        strategies.append(('name_state', f"{company_name}, California"))

        # Strategy 4: Just company name (risky)
        strategies.append(('name_only', f"{company_name}"))

        for strategy_name, query in strategies:
            result = self._try_geocode(query, strategy_name)
            if result and result.get('latitude'):
                result['strategy_used'] = strategy_name
                result['search_query'] = query
                return result
            time.sleep(0.2)  # Small delay between strategies

        # All strategies failed
        return {
            'latitude': None,
            'longitude': None,
            'google_name': None,
            'google_address': None,
            'confidence_score': 0.0,
            'strategy_used': 'failed',
            'search_query': None
        }

    def _try_geocode(self, query: str, strategy: str) -> Optional[Dict]:
        """Attempt to geocode using Google Places API"""

        if not self.api_key:
            print("WARNING: No Google Maps API key found")
            return None

        self.rate_limit()

        params = {
            'input': query,
            'inputtype': 'textquery',
            'fields': 'name,formatted_address,geometry,types,place_id',
            'key': self.api_key
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'OK' and data.get('candidates'):
                candidate = data['candidates'][0]
                location = candidate['geometry']['location']

                # Calculate confidence based on strategy and result
                confidence = self._calculate_confidence(candidate, strategy)

                # Verify it's in California
                if not self._is_california(location['lat'], location['lng']):
                    print(f"  Rejected: {query} - Not in California")
                    return None

                return {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'google_name': candidate.get('name'),
                    'google_address': candidate.get('formatted_address'),
                    'confidence_score': confidence,
                    'place_id': candidate.get('place_id')
                }

        except Exception as e:
            print(f"  Error geocoding '{query}': {str(e)}")

        return None

    def _calculate_confidence(self, candidate: Dict, strategy: str) -> float:
        """Calculate confidence score based on strategy and result quality"""

        base_scores = {
            'full_address': 0.95,
            'name_city': 0.85,
            'name_state': 0.70,
            'name_only': 0.50
        }

        score = base_scores.get(strategy, 0.50)

        # Boost if it's a business/establishment
        types = candidate.get('types', [])
        if 'establishment' in types or 'point_of_interest' in types:
            score += 0.05

        return min(score, 1.0)

    def _is_california(self, lat: float, lng: float) -> bool:
        """Check if coordinates are within California bounds"""
        # California approximate boundaries
        return (32.5 <= lat <= 42.0) and (-124.5 <= lng <= -114.0)

    def extract_address_from_website(self, website: str) -> Optional[str]:
        """
        Extract address from company website
        This is a placeholder for future implementation
        """
        # TODO: Implement web scraping for address extraction
        # Would need to handle:
        # - Contact pages
        # - Footer information
        # - About pages
        # - Structured data (schema.org)
        pass


def process_companies_csv(input_csv: str, output_csv: str,
                         geocode_missing_only: bool = True):
    """Process companies CSV and geocode missing entries"""

    geocoder = ImprovedGeocoder()

    companies = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        companies = list(reader)

    total = len(companies)
    processed = 0
    improved = 0

    print(f"\nProcessing {total} companies...")

    for idx, company in enumerate(companies, 1):
        company_name = company['Company Name']

        # Check if we need to geocode this company
        has_coords = company.get('Latitude') and company.get('Longitude')

        if geocode_missing_only and has_coords:
            processed += 1
            continue

        print(f"\n[{idx}/{total}] Geocoding: {company_name}")

        result = geocoder.geocode_with_fallback(
            company_name=company_name,
            address=company.get('Address'),
            city=company.get('City'),
            website=company.get('Website')
        )

        if result.get('latitude'):
            company['Latitude'] = result['latitude']
            company['Longitude'] = result['longitude']
            company['Google_Name'] = result.get('google_name', '')
            company['Google_Address'] = result.get('google_address', '')
            company['Confidence_Score'] = result.get('confidence_score', 0)
            company['Validation_Source'] = 'Improved_Geocoder'

            print(f"  ✓ Success: {result['google_address']} (confidence: {result['confidence_score']:.2f})")
            print(f"  Strategy: {result['strategy_used']}")
            improved += 1
        else:
            print(f"  ✗ Failed: Could not geocode")

        processed += 1

        # Save progress every 50 companies
        if processed % 50 == 0:
            print(f"\nSaving progress... ({processed}/{total})")
            with open(output_csv, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=companies[0].keys())
                writer.writeheader()
                writer.writerows(companies)

    # Final save
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=companies[0].keys())
        writer.writeheader()
        writer.writerows(companies)

    print(f"\n{'='*70}")
    print(f"GEOCODING COMPLETE")
    print(f"{'='*70}")
    print(f"Total processed: {processed}")
    print(f"Successfully improved: {improved}")
    print(f"Output saved to: {output_csv}")

    return companies


if __name__ == '__main__':
    import sys

    input_file = sys.argv[1] if len(sys.argv) > 1 else 'data/final/companies.csv'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'data/final/companies_improved.csv'

    process_companies_csv(input_file, output_file, geocode_missing_only=True)
