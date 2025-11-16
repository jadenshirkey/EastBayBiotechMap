#!/usr/bin/env python3
"""Test different query strategies."""

import os
import googlemaps

test_companies = [
    {"name": "1cBio", "city": "San Francisco"},
    {"name": "64x Bio", "city": "San Francisco"},
]

gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])

for company in test_companies:
    name = company["name"]
    city = company["city"]

    # Try different query strategies
    queries = [
        f"{name} {city} CA",
        f"{name} {city}",
        f"{name} biotech {city}",
        name,
    ]

    print(f"\n{'='*70}")
    print(f"Company: {name} ({city})")
    print(f"{'='*70}")

    for query in queries:
        try:
            result = gmaps.places(query)
            results = result.get('results', [])
            top_result = results[0] if results else None

            if top_result:
                print(f"\nQuery: '{query}'")
                print(f"  → {top_result.get('name')}")
                print(f"     {top_result.get('formatted_address', top_result.get('vicinity'))}")
            else:
                print(f"\nQuery: '{query}' → NO RESULTS")

        except Exception as e:
            print(f"\nQuery: '{query}' → ERROR: {e}")
