#!/usr/bin/env python3
"""Debug why specific companies are failing."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.helpers import etld1, brand_token_from_etld1, name_similarity
from config.geography import geofence_ok

import googlemaps

test_companies = [
    {"name": "CellMax Life", "website": "https://cellmaxlife.com/", "city": "Sunnyvale"},
    {"name": "CellSight Technologies", "website": "https://cellsighttechnologies.com/", "city": "San Francisco"},
]

gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])

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
    print(f"Domain: {domain}")
    print(f"Brand token: {brand_token}")
    print(f"Query: {query}")
    print(f"{'='*70}")

    # Try text search
    result = gmaps.places(query)
    results = result.get('results', [])[:5]

    print(f"Results found: {len(results)}")

    for i, place in enumerate(results, 1):
        place_id = place.get('place_id')

        # Get details
        details_result = gmaps.place(place_id, fields=['name', 'formatted_address', 'website', 'type', 'geometry', 'business_status'])
        details = details_result.get('result', {})

        place_name = details.get('name', '')
        place_address = details.get('formatted_address', '')
        place_website = details.get('website', '')
        place_types = details.get('type', [])
        geometry = details.get('geometry', {})
        location = geometry.get('location', {})
        lat = location.get('lat')
        lng = location.get('lng')

        print(f"\n  Candidate {i}: {place_name}")
        print(f"    Address: {place_address}")
        print(f"    Website: {place_website}")
        print(f"    Types: {place_types}")

        # Calculate score components
        name_sim = name_similarity(name, place_name)
        print(f"\n    Name similarity: {name_sim:.3f} (score: +{name_sim * 0.4:.3f})")

        # Website check (NEW SMART MATCHING)
        if website and place_website:
            bpg_domain = etld1(website)
            place_domain = etld1(place_website)

            if bpg_domain and place_domain:
                # Extract base domain without TLD
                bpg_base = bpg_domain.rsplit('.', 1)[0] if '.' in bpg_domain else bpg_domain
                place_base = place_domain.rsplit('.', 1)[0] if '.' in place_domain else place_domain

                if bpg_domain == place_domain:
                    print(f"    Website exact match: {bpg_domain} (score: +0.3)")
                    website_score = 0.3
                elif bpg_base == place_base:
                    print(f"    Website TLD diff: {bpg_domain} ≈ {place_domain} (score: +0.2)")
                    website_score = 0.2
                elif bpg_base in place_base or place_base in bpg_base:
                    if name_sim >= 0.90:
                        print(f"    Website partial match: {bpg_base} ⊂ {place_base}, name={name_sim:.2f} (score: +0.2)")
                        website_score = 0.2
                    else:
                        print(f"    Website weak match: {bpg_base} ⊂ {place_base}, name={name_sim:.2f} (score: -0.1)")
                        website_score = -0.1
                else:
                    print(f"    Website mismatch: {bpg_domain} ≠ {place_domain} (score: -0.2)")
                    website_score = -0.2
            else:
                website_score = 0.0
        elif website and not place_website:
            print(f"    Website absent in details (score: +0.1)")
            website_score = 0.1
        else:
            website_score = 0.0

        # Geofence
        geofence = geofence_ok(place_address, lat=lat, lng=lng)
        geo_score = 0.2 if geofence else 0.0
        print(f"    Geofence: {geofence} (score: +{geo_score})")

        # Business status
        status = details.get('business_status', '')
        status_score = 0.1 if status == 'OPERATIONAL' else 0.0
        print(f"    Business status: {status} (score: +{status_score})")

        # Total score
        total_score = (name_sim * 0.4) + website_score + geo_score + status_score
        print(f"\n    TOTAL SCORE: {total_score:.3f} (threshold: 0.75)")
        print(f"    RESULT: {'✓ PASS' if total_score >= 0.75 else '✗ FAIL'}")
