#!/usr/bin/env python3
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.helpers import etld1, brand_token_from_etld1, name_similarity
from config.geography import geofence_ok
import googlemaps

# Use ACTUAL website from CSV
company = {"name": "CellSight Technologies", "website": "https://cellsighttech.com/", "city": "San Francisco"}

gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])

name = company["name"]
website = company["website"]
city = company["city"]

domain = etld1(website)
brand_token = brand_token_from_etld1(domain) if domain else name.split()[0]
query = f"{brand_token} {city} CA biotech"

print(f"Company: {name}")
print(f"Website: {website}")
print(f"Domain: {domain}")
print(f"Brand token: {brand_token}")
print(f"Query: {query}\n")

result = gmaps.places(query)
results = result.get('results', [])[:3]

print(f"Results: {len(results)}\n")

for i, place in enumerate(results, 1):
    place_id = place.get('place_id')
    details_result = gmaps.place(place_id, fields=['name', 'formatted_address', 'website', 'type', 'geometry', 'business_status'])
    details = details_result.get('result', {})

    place_name = details.get('name', '')
    place_website = details.get('website', '')

    name_sim = name_similarity(name, place_name)

    bpg_domain = etld1(website)
    place_domain = etld1(place_website) if place_website else None

    if bpg_domain and place_domain:
        if bpg_domain == place_domain:
            web_score = 0.3
            web_msg = f"MATCH ({bpg_domain})"
        else:
            web_score = -0.2
            web_msg = f"MISMATCH ({bpg_domain} ≠ {place_domain})"
    elif bpg_domain and not place_domain:
        web_score = 0.1
        web_msg = "ABSENT"
    else:
        web_score = 0.0
        web_msg = "N/A"

    score = name_sim * 0.4 + web_score + 0.2 + 0.1  # assume geofence + operational

    print(f"Candidate {i}: {place_name}")
    print(f"  Website: {place_website or 'N/A'}")
    print(f"  Name sim: {name_sim:.3f}, Web: {web_msg}, Score: {score:.3f} {'✓' if score >= 0.75 else '✗'}\n")
