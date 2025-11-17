#!/usr/bin/env python3
"""
Worker script for parallel Google Maps enrichment.
Processes a specific chunk of companies.
"""

import os
import sys
import json
import csv
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.helpers import etld1, brand_token_from_etld1, name_similarity
from config.geography import geofence_ok
import googlemaps

def calculate_confidence_score(bpg_name, details, bpg_website):
    """Calculate confidence score (same as main script)."""
    score = 0.0
    reasons = []

    # Name similarity (40% weight)
    place_name = details.get('name', '')
    similarity = name_similarity(bpg_name, place_name)
    score += similarity * 0.4
    reasons.append(f"name_sim({similarity:.2f},+{similarity*0.4:.2f})")

    # Website eTLD+1 check (smart matching)
    details_website = details.get('website', '')
    if bpg_website and details_website:
        bpg_domain = etld1(bpg_website)
        details_domain = etld1(details_website)

        if bpg_domain and details_domain:
            bpg_base = bpg_domain.rsplit('.', 1)[0] if '.' in bpg_domain else bpg_domain
            details_base = details_domain.rsplit('.', 1)[0] if '.' in details_domain else details_domain

            if bpg_domain == details_domain:
                score += 0.3
                reasons.append(f"website_match({bpg_domain},+0.3)")
            elif bpg_base == details_base:
                score += 0.2
                reasons.append(f"website_tld_diff({bpg_domain}≈{details_domain},+0.2)")
            elif bpg_base in details_base or details_base in bpg_base:
                if similarity >= 0.90:
                    score += 0.2
                    reasons.append(f"website_partial({bpg_base}⊂{details_base},+0.2)")
                else:
                    score -= 0.1
                    reasons.append(f"website_weak_match({bpg_domain}≠{details_domain},-0.1)")
            else:
                score -= 0.2
                reasons.append(f"website_mismatch({bpg_domain}≠{details_domain},-0.2)")
    elif bpg_website and not details_website:
        score += 0.1
        reasons.append("website_absent(+0.1)")

    # Geofence (20% weight)
    address = details.get('formatted_address', '')
    location = details.get('geometry', {}).get('location', {})
    lat = location.get('lat')
    lng = location.get('lng')

    if geofence_ok(address, lat=lat, lng=lng):
        score += 0.2
        reasons.append("geofence_ok(+0.2)")

    # Business status (10% weight)
    status = details.get('business_status', '')
    if status == 'OPERATIONAL':
        score += 0.1
        reasons.append("operational(+0.1)")

    return score, reasons

def enrich_chunk(worker_id, chunk_file, output_file):
    """Enrich a chunk of companies."""

    # Initialize Google Maps client
    gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])

    # Load chunk
    with open(chunk_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        companies = list(reader)

    print(f"[Worker {worker_id}] Processing {len(companies)} companies")

    # Results
    enriched = []
    failed = []

    for idx, row in enumerate(companies):
        name = row['Company Name']
        website = row['Website']
        city = row.get('City', '')

        print(f"[Worker {worker_id}] [{idx+1}/{len(companies)}] {name} ({city})")

        # Build search query
        domain = etld1(website) if website else None
        brand_token = brand_token_from_etld1(domain) if domain else name.split()[0]
        query = f"{brand_token} {city} CA biotech"

        # Search
        try:
            result = gmaps.places(query)
            results = result.get('results', [])[:5]

            best_match = None
            best_score = 0.0

            for place in results:
                place_id = place.get('place_id')
                details_result = gmaps.place(
                    place_id,
                    fields=['name', 'formatted_address', 'website', 'type', 'geometry', 'business_status']
                )
                details = details_result.get('result', {})

                # Calculate score
                score, reasons = calculate_confidence_score(name, details, website)

                if score >= 0.75 and score > best_score:
                    best_score = score
                    best_match = details

            if best_match:
                enriched_row = row.copy()
                enriched_row['Google_Address'] = best_match.get('formatted_address', '')
                enriched_row['Google_Name'] = best_match.get('name', '')
                enriched_row['Google_Website'] = best_match.get('website', '')
                enriched_row['Confidence_Score'] = str(best_score)
                location = best_match.get('geometry', {}).get('location', {})
                enriched_row['Latitude'] = str(location.get('lat', ''))
                enriched_row['Longitude'] = str(location.get('lng', ''))
                enriched.append(enriched_row)
                print(f"  ✓ Enriched (score: {best_score:.3f})")
            else:
                failed.append(row)
                print(f"  ✗ Failed")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed.append(row)

    # Save results
    if enriched:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=enriched[0].keys())
            writer.writeheader()
            writer.writerows(enriched)
        print(f"[Worker {worker_id}] Saved {len(enriched)} enriched companies to {output_file}")

    # Save failed
    if failed:
        failed_file = output_file.replace('.csv', '_failed.csv')
        with open(failed_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=failed[0].keys())
            writer.writeheader()
            writer.writerows(failed)
        print(f"[Worker {worker_id}] Saved {len(failed)} failed companies to {failed_file}")

    print(f"[Worker {worker_id}] Complete: {len(enriched)}/{len(companies)} enriched ({len(enriched)/len(companies)*100:.1f}%)")

def main():
    if len(sys.argv) < 2:
        print("Usage: worker_enrichment.py <worker_id>")
        sys.exit(1)

    worker_id = int(sys.argv[1])

    # Load worker config
    config_file = Path("data/working/chunks/worker_config.json")
    with open(config_file) as f:
        workers = json.load(f)

    worker = workers[worker_id]
    chunk_file = worker['chunk_file']
    output_file = chunk_file.replace('.csv', '_enriched.csv')

    enrich_chunk(worker_id, chunk_file, output_file)

if __name__ == "__main__":
    main()
