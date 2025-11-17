#!/usr/bin/env python3
"""Improved worker enrichment with better search strategies."""

import sys
import csv
import time
from pathlib import Path
from googlemaps import Client as GoogleMapsClient
from config.etld1 import etld1, brand_token_from_etld1
import difflib
import os
import re

# Import secure configuration
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.secure_config import get_config

# Get configuration
config = get_config()
API_KEY = config.google_maps_api_key

if not API_KEY:
    print("Error: Google Maps API key not configured. Please set GOOGLE_MAPS_API_KEY environment variable.")
    print("Copy .env.template to .env and add your API key.")
    exit(1)

def name_similarity(name1, name2):
    """Calculate similarity between two company names."""
    clean1 = re.sub(r'[^\w\s]', '', name1.lower())
    clean2 = re.sub(r'[^\w\s]', '', name2.lower())
    return difflib.SequenceMatcher(None, clean1, clean2).ratio()

def is_california_address(address):
    """Check if address is in California."""
    if not address:
        return False
    return bool(re.search(r',\s*CA\b', address))

def is_california_coords(lat, lng):
    """Check if coordinates are within California bounds."""
    return (32.5 <= lat <= 42.5) and (-124.5 <= lng <= -114.0)

def calculate_confidence_score(bpg_name, details, bpg_website):
    """Calculate match confidence score."""
    score = 0.0
    reasons = []

    # Name similarity (40% weight)
    place_name = details.get('name', '')
    similarity = name_similarity(bpg_name, place_name)
    score += similarity * 0.4
    reasons.append(f"name_sim={similarity:.2f}")

    # Website eTLD+1 check (30% weight)
    details_website = details.get('website', '')
    if bpg_website and details_website:
        bpg_domain = etld1(bpg_website)
        details_domain = etld1(details_website)

        if bpg_domain and details_domain:
            bpg_base = bpg_domain.rsplit('.', 1)[0] if '.' in bpg_domain else bpg_domain
            details_base = details_domain.rsplit('.', 1)[0] if '.' in details_domain else details_domain

            if bpg_domain == details_domain:
                score += 0.3
                reasons.append("exact_domain_match")
            elif bpg_base == details_base:
                score += 0.2
                reasons.append("domain_base_match")
            elif bpg_base in details_base or details_base in bpg_base:
                if similarity >= 0.90:
                    score += 0.2
                    reasons.append("partial_domain_match+high_name_sim")
                else:
                    score -= 0.1
                    reasons.append("weak_partial_domain")
            else:
                score -= 0.2
                reasons.append("domain_mismatch")
        else:
            reasons.append("domain_parse_failed")
    elif not bpg_website and similarity >= 0.85:
        score += 0.15
        reasons.append("no_website_but_high_name_sim")
    else:
        reasons.append("no_website_match_attempted")

    # Geofence check (20% weight)
    address = details.get('formatted_address', '')
    geometry = details.get('geometry', {})
    location = geometry.get('location', {})
    lat = location.get('lat', 0)
    lng = location.get('lng', 0)

    if is_california_address(address) or is_california_coords(lat, lng):
        score += 0.2
        reasons.append("in_california")
    else:
        score -= 0.3
        reasons.append("outside_california")

    # Business status check (10% weight)
    status = details.get('business_status', '')
    if status == 'OPERATIONAL':
        score += 0.1
        reasons.append("operational")
    elif status == 'CLOSED_TEMPORARILY':
        score += 0.05
        reasons.append("temp_closed")
    elif status == 'CLOSED_PERMANENTLY':
        score -= 0.2
        reasons.append("permanently_closed")

    return score, reasons

def search_with_fallbacks(gmaps, company_name, city, website, focus_areas=None):
    """Try multiple search strategies with fallbacks."""
    queries = []

    # Strategy 1: Full company name + city + CA
    if city:
        queries.append(f"{company_name} {city} California")
        queries.append(f"{company_name} {city} CA")

    # Strategy 2: Full company name + address/location
    queries.append(f"{company_name} address")
    queries.append(f"{company_name} location California")

    # Strategy 3: Website domain + city (if available)
    if website:
        domain = etld1(website)
        if domain:
            brand = brand_token_from_etld1(domain)
            if city:
                queries.append(f"{brand} {city}")
            queries.append(f"{brand} California")

    # Strategy 4: Company name variations
    # Remove common suffixes
    clean_name = company_name
    for suffix in [', Inc.', ' Inc.', ', LLC', ' LLC', ' Corp.', ' Corporation', ' Ltd.']:
        clean_name = clean_name.replace(suffix, '')

    if clean_name != company_name:
        queries.append(f"{clean_name} California")

    # Strategy 5: Industry-specific search (based on focus areas)
    if focus_areas:
        focus_lower = focus_areas.lower()
        industry_hint = ""

        if any(term in focus_lower for term in ['pharma', 'drug', 'medicine']):
            industry_hint = "pharmaceutical"
        elif any(term in focus_lower for term in ['diagnostic', 'testing', 'assay']):
            industry_hint = "diagnostics"
        elif any(term in focus_lower for term in ['device', 'equipment', 'instrument']):
            industry_hint = "medical device"
        elif any(term in focus_lower for term in ['therapy', 'treatment', 'clinical']):
            industry_hint = "therapeutics"
        elif any(term in focus_lower for term in ['research', 'discovery', 'development']):
            industry_hint = "research"

        if industry_hint and city:
            queries.append(f"{company_name} {city} {industry_hint}")

    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)

    # Try each query
    best_match = None
    best_score = 0.0
    best_query = None

    for query in unique_queries[:5]:  # Limit to 5 attempts to manage API costs
        try:
            result = gmaps.places(query)
            results = result.get('results', [])[:3]  # Check top 3 results per query

            for place in results:
                place_id = place.get('place_id')
                details_result = gmaps.place(
                    place_id,
                    fields=['name', 'formatted_address', 'website', 'type', 'geometry', 'business_status']
                )
                details = details_result.get('result', {})

                score, reasons = calculate_confidence_score(company_name, details, website)

                if score >= 0.75 and score > best_score:
                    best_score = score
                    best_match = details
                    best_query = query

                    # If we get a very high score, stop searching
                    if score >= 0.95:
                        return best_match, best_score, best_query

            # Small delay between queries
            time.sleep(0.1)

        except Exception as e:
            print(f"  Query failed '{query}': {e}")
            continue

    return best_match, best_score, best_query

def main():
    if len(sys.argv) != 2:
        print("Usage: worker_enrichment_improved.py <worker_id>")
        exit(1)

    worker_id = int(sys.argv[1])
    chunk_file = Path(f"data/working/chunks/chunk_{worker_id}.csv")
    output_file = Path(f"data/working/chunks/chunk_{worker_id}_enriched.csv")

    if not chunk_file.exists():
        print(f"[Worker {worker_id}] No chunk file found")
        exit(0)

    # Initialize Google Maps client
    gmaps = GoogleMapsClient(key=API_KEY)

    # Read companies
    with open(chunk_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        companies = list(reader)

    print(f"[Worker {worker_id}] Processing {len(companies)} companies")

    enriched = []
    failed = []

    for idx, row in enumerate(companies):
        name = row['Company Name']
        website = row.get('Website', '')
        city = row.get('City', '')
        focus_areas = row.get('Focus Areas', '')

        print(f"[Worker {worker_id}] [{idx+1}/{len(companies)}] {name} ({city})")

        # Search with multiple strategies
        try:
            best_match, best_score, best_query = search_with_fallbacks(
                gmaps, name, city, website, focus_areas
            )

            if best_match:
                enriched_row = row.copy()
                enriched_row['Google_Address'] = best_match.get('formatted_address', '')
                enriched_row['Google_Name'] = best_match.get('name', '')
                enriched_row['Google_Website'] = best_match.get('website', '')
                enriched_row['Confidence_Score'] = best_score
                enriched_row['Search_Query'] = best_query

                geometry = best_match.get('geometry', {})
                location = geometry.get('location', {})
                enriched_row['Latitude'] = location.get('lat', '')
                enriched_row['Longitude'] = location.get('lng', '')

                enriched.append(enriched_row)
                print(f"  ✓ MATCHED (score={best_score:.2f}): {best_match.get('name', 'Unknown')}")
                print(f"    Query: {best_query}")
            else:
                failed.append(name)
                print(f"  ✗ NO MATCH FOUND")

        except Exception as e:
            failed.append(name)
            print(f"  ✗ ERROR: {e}")

        # Rate limiting
        time.sleep(0.2)

    # Write results
    if enriched:
        fieldnames = list(enriched[0].keys())
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched)
    else:
        # Create empty file with headers
        fieldnames = list(companies[0].keys()) + [
            'Google_Address', 'Google_Name', 'Google_Website',
            'Confidence_Score', 'Search_Query', 'Latitude', 'Longitude'
        ]
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    # Summary
    print(f"\n[Worker {worker_id}] Complete!")
    print(f"  Enriched: {len(enriched)}/{len(companies)} ({len(enriched)/len(companies)*100:.1f}%)")
    print(f"  Failed: {len(failed)}")
    if failed and len(failed) <= 10:
        print(f"  Failed companies: {', '.join(failed)}")

if __name__ == "__main__":
    main()