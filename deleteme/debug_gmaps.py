#!/usr/bin/env python3
"""Debug script to test Google Maps API responses for failing companies."""

import os
import sys
import googlemaps
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from utils.helpers import etld1, brand_token_from_etld1

# Test companies that failed
test_companies = [
    {"name": "1cBio", "website": "https://www.1cbio.com/", "city": "San Francisco"},
    {"name": "64x Bio", "website": "https://www.64xbio.com/", "city": "San Francisco"},
    {"name": "858 Therapeutics", "website": "https://www.858therapeutics.com/", "city": "San Diego"},
    {"name": "ALLInBio", "website": "https://allinbio.com/", "city": "San Francisco"},
]

api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
if not api_key:
    print("Error: GOOGLE_MAPS_API_KEY not set")
    sys.exit(1)

gmaps = googlemaps.Client(key=api_key)

for company in test_companies:
    name = company["name"]
    website = company["website"]
    city = company["city"]

    # Build query same way as script
    domain = etld1(website)
    brand_token = brand_token_from_etld1(domain) if domain else name.split()[0]
    query = f"{brand_token} {city} CA biotech"

    print(f"\n{'='*70}")
    print(f"Company: {name}")
    print(f"Website: {website}")
    print(f"City: {city}")
    print(f"Brand token: {brand_token}")
    print(f"Query: {query}")
    print(f"{'='*70}")

    # Try text search
    try:
        result = gmaps.places(query)
        status = result.get('status')
        results = result.get('results', [])

        print(f"Status: {status}")
        print(f"Results found: {len(results)}")

        if results:
            for i, place in enumerate(results[:3], 1):
                print(f"\n  Result {i}:")
                print(f"    Name: {place.get('name')}")
                print(f"    Address: {place.get('formatted_address', place.get('vicinity'))}")
                print(f"    Types: {place.get('types', [])}")
                print(f"    Place ID: {place.get('place_id')}")
        else:
            print("  No results returned from Google Maps")

    except Exception as e:
        print(f"ERROR: {e}")
