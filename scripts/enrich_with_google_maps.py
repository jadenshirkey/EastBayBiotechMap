#!/usr/bin/env python3
"""
Path A Enrichment: Google Maps Places API with gated validation.

This script implements Phase 3 (Issues #11-14) from V4.3 work plan:
- Deterministic scoring and validation gates (geofence, business-type, multi-tenant)
- Cost instrumentation and caching
- Error handling, retries, and checkpointing
- Path A/Path B routing

Usage:
    export GOOGLE_MAPS_API_KEY="your-api-key-here"
    python3 enrich_with_google_maps.py [--resume]

Author: Bay Area Biotech Map V4.3
Date: 2025-11-16
"""

import csv
import os
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Import V4.3 modules
try:
    # Add parent directory to path to import config and utils
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config.geography import geofence_ok
    from utils.helpers import (
        etld1,
        brand_token_from_etld1,
        name_similarity,
        is_multi_tenant,
        validate_multi_tenant_match,
        is_aggregator,
    )
except ImportError as e:
    print(f"Error importing V4.3 modules: {e}")
    print("Make sure config/geography.py and utils/helpers.py exist")
    sys.exit(1)

try:
    import googlemaps
except ImportError:
    print("Error: googlemaps library not installed")
    print("Run: pip install googlemaps")
    sys.exit(1)


# ============================================================================
# Configuration
# ============================================================================

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
WORKING_DIR = DATA_DIR / "working"
CACHE_DIR = DATA_DIR / "cache"

INPUT_FILE = WORKING_DIR / "companies_merged.csv"
OUTPUT_PATH_A = WORKING_DIR / "companies_enriched_path_a.csv"
OUTPUT_PATH_B_QUEUE = WORKING_DIR / "path_b_queue.csv"
MANUAL_QUEUE = WORKING_DIR / "manual_review_queue.csv"
API_USAGE_REPORT = WORKING_DIR / "api_usage_report.txt"
CHECKPOINT_FILE = WORKING_DIR / ".checkpoint_enrichment.json"
PLACE_DETAILS_CACHE = CACHE_DIR / f"place_details_{datetime.now().strftime('%Y%m%d')}.json"

# API pricing (per call)
GOOGLE_MAPS_COST_PER_TEXT_SEARCH = 0.032
GOOGLE_MAPS_COST_PER_DETAILS = 0.017

# Business types to exclude (not biotech/life sciences)
EXCLUDED_BUSINESS_TYPES = {
    'real_estate_agency',
    'lodging',
    'premise',
    'parking',
    'storage',
    'moving_company',
    'lawyer',
    'accounting',
    'insurance_agency',
}

# Scoring thresholds
ACCEPTANCE_THRESHOLD = 0.75
MULTI_TENANT_NAME_SIMILARITY_THRESHOLD = 0.85

# Checkpointing and rate limiting
CHECKPOINT_INTERVAL = 50  # Save checkpoint every N rows
RATE_LIMIT_DELAY = 0.1  # Delay between API calls (seconds)
MAX_RETRIES = 3
RETRY_DELAYS = [0.5, 1.0, 2.0]  # Exponential backoff
RATE_LIMIT_BACKOFF = 60  # Backoff for 429 errors (seconds)

# Place Details fields to request
PLACE_DETAILS_FIELDS = [
    'name',
    'formatted_address',
    'website',
    'types',
    'geometry',
    'business_status'
]


# ============================================================================
# API Usage Counter
# ============================================================================

class APIUsageCounter:
    """Track Google Maps API usage and costs."""

    def __init__(self):
        self.text_search_calls = 0
        self.place_details_calls = 0

    def record_text_search(self):
        """Record a Text Search API call."""
        self.text_search_calls += 1

    def record_place_details(self):
        """Record a Place Details API call."""
        self.place_details_calls += 1

    def total_calls(self) -> int:
        """Get total API calls."""
        return self.text_search_calls + self.place_details_calls

    def estimated_cost(self) -> float:
        """Calculate estimated cost based on API pricing."""
        text_search_cost = self.text_search_calls * GOOGLE_MAPS_COST_PER_TEXT_SEARCH
        details_cost = self.place_details_calls * GOOGLE_MAPS_COST_PER_DETAILS
        return text_search_cost + details_cost

    def report(self) -> str:
        """Generate usage report."""
        lines = [
            "Google Maps API Usage Report",
            "=" * 70,
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "API Calls:",
            f"  Text Search calls: {self.text_search_calls}",
            f"  Place Details calls: {self.place_details_calls}",
            f"  Total calls: {self.total_calls()}",
            "",
            "Estimated Cost:",
            f"  Text Search: ${self.text_search_calls * GOOGLE_MAPS_COST_PER_TEXT_SEARCH:.2f}",
            f"  Place Details: ${self.place_details_calls * GOOGLE_MAPS_COST_PER_DETAILS:.2f}",
            f"  Total: ${self.estimated_cost():.2f}",
        ]
        return "\n".join(lines)


# ============================================================================
# Place Details Cache
# ============================================================================

class PlaceDetailsCache:
    """In-memory and disk cache for Place Details."""

    def __init__(self, cache_file: Path, max_age_days: int = 30):
        self.cache_file = cache_file
        self.max_age_days = max_age_days
        self.cache: Dict[str, dict] = {}
        self.load()

    def load(self):
        """Load cache from disk."""
        if not self.cache_file.exists():
            return

        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)

            # Check cache age
            cache_date_str = data.get('cache_date', '')
            if cache_date_str:
                cache_date = datetime.strptime(cache_date_str, '%Y-%m-%d')
                age = datetime.now() - cache_date
                if age.days > self.max_age_days:
                    print(f"  Cache expired (age: {age.days} days), starting fresh")
                    return

            self.cache = data.get('places', {})
            print(f"  Loaded {len(self.cache)} cached Place Details")
        except Exception as e:
            print(f"  Warning: Could not load cache: {e}")

    def save(self):
        """Save cache to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'cache_date': datetime.now().strftime('%Y-%m-%d'),
            'places': self.cache
        }

        with open(self.cache_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get(self, place_id: str) -> Optional[dict]:
        """Get cached Place Details."""
        return self.cache.get(place_id)

    def put(self, place_id: str, details: dict):
        """Cache Place Details."""
        self.cache[place_id] = details


# ============================================================================
# Checkpoint Management
# ============================================================================

def save_checkpoint(processed_indices: List[int]):
    """Save checkpoint of processed row indices."""
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'timestamp': datetime.now().isoformat(),
        'processed_indices': processed_indices
    }

    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def load_checkpoint() -> List[int]:
    """Load checkpoint if exists."""
    if not CHECKPOINT_FILE.exists():
        return []

    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            data = json.load(f)

        processed = data.get('processed_indices', [])
        timestamp = data.get('timestamp', '')
        print(f"  Found checkpoint from {timestamp}")
        print(f"  Already processed: {len(processed)} rows")
        return processed
    except Exception as e:
        print(f"  Warning: Could not load checkpoint: {e}")
        return []


def clear_checkpoint():
    """Clear checkpoint file after successful completion."""
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()


# ============================================================================
# Google Maps API Functions with Retry Logic
# ============================================================================

def retry_with_backoff(func, *args, **kwargs):
    """Retry function with exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except googlemaps.exceptions.Timeout as e:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                print(f"    Timeout, retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise
        except googlemaps.exceptions.ApiError as e:
            # Handle rate limiting (429)
            if '429' in str(e) or 'OVER_QUERY_LIMIT' in str(e):
                print(f"    Rate limit hit, backing off for {RATE_LIMIT_BACKOFF}s...")
                time.sleep(RATE_LIMIT_BACKOFF)
                if attempt < MAX_RETRIES - 1:
                    continue
            raise
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                print(f"    Error ({type(e).__name__}), retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise


def search_places_text(gmaps, query: str, counter: APIUsageCounter) -> List[dict]:
    """
    Search for places using Text Search API.

    Returns top 3-5 candidates.
    """
    def _search():
        counter.record_text_search()
        result = gmaps.places(query)
        return result

    try:
        results = retry_with_backoff(_search)

        if results.get('status') == 'OK':
            # Return top 5 results
            return results.get('results', [])[:5]

        return []
    except Exception as e:
        print(f"    Text Search error: {e}")
        return []


def get_place_details(
    gmaps,
    place_id: str,
    counter: APIUsageCounter,
    cache: PlaceDetailsCache
) -> Optional[dict]:
    """
    Get Place Details for a place_id.

    Uses cache if available.
    """
    # Check cache first
    cached = cache.get(place_id)
    if cached:
        return cached

    def _get_details():
        counter.record_place_details()
        result = gmaps.place(place_id, fields=PLACE_DETAILS_FIELDS)
        return result

    try:
        result = retry_with_backoff(_get_details)

        if result.get('status') == 'OK':
            details = result.get('result', {})
            # Cache the result
            cache.put(place_id, details)
            return details

        return None
    except Exception as e:
        print(f"    Place Details error: {e}")
        return None


# ============================================================================
# Validation Gates
# ============================================================================

def passes_business_type_gate(types: List[str]) -> bool:
    """
    Check if business types are acceptable (not excluded types).

    Args:
        types: List of Google Places types

    Returns:
        True if passes (no excluded types), False otherwise
    """
    if not types:
        # No types info - allow by default
        return True

    # Check for excluded types
    for excluded_type in EXCLUDED_BUSINESS_TYPES:
        if excluded_type in types:
            return False

    return True


def calculate_confidence_score(
    company_name: str,
    bpg_website: str,
    details: dict,
    city: str
) -> Tuple[float, str]:
    """
    Calculate deterministic confidence score for a Place Details candidate.

    Scoring:
    - +0.4: name_similarity
    - +0.3: eTLD+1 match (website)
    - -0.2: eTLD+1 mismatch
    - +0.1: eTLD+1 absent in details
    - +0.2: geofence pass
    - +0.1: business operational

    Args:
        company_name: Company name from BPG
        bpg_website: Website from BPG (ground truth)
        details: Place Details result
        city: City from BPG

    Returns:
        (score, validation_reason) tuple
    """
    score = 0.0
    reasons = []

    # Name similarity (+0.4 max)
    details_name = details.get('name', '')
    if details_name:
        similarity = name_similarity(company_name, details_name)
        name_score = similarity * 0.4
        score += name_score
        reasons.append(f"name_sim={similarity:.2f}(+{name_score:.2f})")

    # Website eTLD+1 check (+0.3 match, -0.2 mismatch, +0.1 absent)
    details_website = details.get('website', '')
    if bpg_website and details_website:
        bpg_domain = etld1(bpg_website)
        details_domain = etld1(details_website)

        if bpg_domain and details_domain:
            if bpg_domain == details_domain:
                score += 0.3
                reasons.append(f"website_match({bpg_domain},+0.3)")
            else:
                score -= 0.2
                reasons.append(f"website_mismatch({bpg_domain}≠{details_domain},-0.2)")
    elif bpg_website and not details_website:
        # Website absent in details
        score += 0.1
        reasons.append("website_absent(+0.1)")

    # Geofence check (+0.2)
    address = details.get('formatted_address', '')
    geometry = details.get('geometry', {})
    location = geometry.get('location', {})
    lat = location.get('lat')
    lng = location.get('lng')

    if geofence_ok(address, lat=lat, lng=lng):
        score += 0.2
        reasons.append("geofence_ok(+0.2)")
    else:
        reasons.append("geofence_fail(+0.0)")

    # Business operational (+0.1)
    business_status = details.get('business_status', '')
    if business_status == 'OPERATIONAL':
        score += 0.1
        reasons.append("operational(+0.1)")

    validation_reason = "; ".join(reasons)
    return score, validation_reason


def validate_candidate(
    company_name: str,
    bpg_website: str,
    city: str,
    details: dict
) -> Tuple[bool, float, str]:
    """
    Apply all validation gates to a Place Details candidate.

    Gates:
    1. Geofence: address must be in Bay Area
    2. Business type: exclude real_estate, lodging, premise
    3. Multi-tenant: require strong brand-domain match
    4. Score threshold: ≥ 0.75

    Args:
        company_name: Company name from BPG
        bpg_website: Website from BPG
        city: City from BPG
        details: Place Details result

    Returns:
        (accepted, confidence_score, validation_reason) tuple
    """
    # Gate 1: Geofence
    address = details.get('formatted_address', '')
    geometry = details.get('geometry', {})
    location = geometry.get('location', {})
    lat = location.get('lat')
    lng = location.get('lng')

    if not geofence_ok(address, lat=lat, lng=lng):
        return False, 0.0, "geofence_fail"

    # Gate 2: Business type exclusion
    types = details.get('types', [])
    if not passes_business_type_gate(types):
        excluded = [t for t in types if t in EXCLUDED_BUSINESS_TYPES]
        return False, 0.0, f"excluded_type({','.join(excluded)})"

    # Gate 3: Multi-tenant handling
    if is_multi_tenant(address):
        details_name = details.get('name', '')
        details_website = details.get('website', '')

        if not validate_multi_tenant_match(
            company_name, details_name, details_website, bpg_website
        ):
            return False, 0.0, "multi_tenant_mismatch"

    # Calculate deterministic score
    score, validation_reason = calculate_confidence_score(
        company_name, bpg_website, details, city
    )

    # Gate 4: Acceptance threshold
    accepted = score >= ACCEPTANCE_THRESHOLD

    return accepted, score, validation_reason


# ============================================================================
# Path A Enrichment
# ============================================================================

def enrich_path_a(
    company: dict,
    gmaps,
    counter: APIUsageCounter,
    cache: PlaceDetailsCache
) -> Optional[dict]:
    """
    Enrich a company using Path A (gated validation with Google Places).

    Args:
        company: Company dict with Name, Website, City
        gmaps: Google Maps client
        counter: API usage counter
        cache: Place Details cache

    Returns:
        Enrichment dict if successful, None otherwise
    """
    company_name = company.get('Company Name', '')
    bpg_website = company.get('Website', '')
    city = company.get('City', '')

    if not company_name or not city:
        return None

    # Build biasable query using brand token
    brand_token = ''
    if bpg_website:
        domain = etld1(bpg_website)
        if domain:
            brand_token = brand_token_from_etld1(domain)

    # Fallback to company name if no brand token
    if not brand_token:
        brand_token = company_name.split()[0]  # First word

    query = f"{brand_token} {city} CA biotech"

    # Text Search for top 3-5 candidates
    candidates = search_places_text(gmaps, query, counter)

    if not candidates:
        return None

    # Try each candidate with validation gates
    for candidate in candidates:
        place_id = candidate.get('place_id')
        if not place_id:
            continue

        # Get Place Details
        details = get_place_details(gmaps, place_id, counter, cache)
        if not details:
            continue

        # Apply validation gates
        accepted, confidence, validation_reason = validate_candidate(
            company_name, bpg_website, city, details
        )

        if accepted:
            # Success! Return enrichment data
            address = details.get('formatted_address', '')

            return {
                'Address': address,
                'Place_ID': place_id,
                'Confidence_Det': f"{confidence:.3f}",
                'Validation_Reason': validation_reason
            }

    # No candidates passed validation
    return None


# ============================================================================
# Main Processing
# ============================================================================

def main():
    """Main enrichment workflow."""
    parser = argparse.ArgumentParser(description='Path A Enrichment with Google Places API')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    args = parser.parse_args()

    print("=" * 70)
    print("Path A Enrichment: Google Maps Places API")
    print("=" * 70)
    print()

    # Check for API key
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("Error: GOOGLE_MAPS_API_KEY environment variable not set")
        print()
        print("Set it with:")
        print("  export GOOGLE_MAPS_API_KEY='your-api-key-here'")
        sys.exit(1)

    # Initialize Google Maps client
    try:
        gmaps = googlemaps.Client(key=api_key)
        print("✓ Google Maps API client initialized")
    except Exception as e:
        print(f"Error initializing Google Maps client: {e}")
        sys.exit(1)

    # Initialize counters and cache
    counter = APIUsageCounter()
    cache = PlaceDetailsCache(PLACE_DETAILS_CACHE)
    print()

    # Load checkpoint if resuming
    processed_indices = []
    if args.resume:
        processed_indices = load_checkpoint()
        print()

    # Load companies
    if not INPUT_FILE.exists():
        print(f"Error: Input file not found: {INPUT_FILE}")
        print("Run merge_company_sources.py first")
        sys.exit(1)

    print(f"Loading companies from: {INPUT_FILE}")
    companies = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row)

    print(f"  Loaded {len(companies)} companies")
    print()

    # Route to Path A and Path B
    path_a_companies = []
    path_b_companies = []

    for company in companies:
        website = company.get('Website', '').strip()
        if website and not is_aggregator(website):
            path_a_companies.append(company)
        else:
            path_b_companies.append(company)

    print(f"Path A companies (with Website): {len(path_a_companies)}")
    print(f"Path B companies (no Website): {len(path_b_companies)}")
    print()

    # Write Path B queue
    if path_b_companies:
        WORKING_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH_B_QUEUE, 'w', newline='', encoding='utf-8') as f:
            fieldnames = path_b_companies[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(path_b_companies)
        print(f"✓ Wrote {len(path_b_companies)} companies to Path B queue: {OUTPUT_PATH_B_QUEUE}")
        print()

    # Process Path A companies
    print(f"Processing {len(path_a_companies)} Path A companies...")
    print()

    enriched_companies = []
    manual_queue = []
    stats = {
        'total': len(path_a_companies),
        'enriched': 0,
        'failed': 0,
        'skipped': 0
    }

    for i, company in enumerate(path_a_companies):
        # Check if already processed (resume)
        if i in processed_indices:
            stats['skipped'] += 1
            continue

        company_name = company.get('Company Name', '')
        city = company.get('City', '')

        print(f"[{i+1}/{stats['total']}] {company_name} ({city})")

        try:
            # Attempt Path A enrichment
            enrichment = enrich_path_a(company, gmaps, counter, cache)

            if enrichment:
                # Success!
                enriched = company.copy()
                enriched.update(enrichment)
                enriched['Validation_Source'] = 'PathA'
                enriched_companies.append(enriched)
                stats['enriched'] += 1

                print(f"  ✓ Enriched: {enrichment['Address'][:50]}...")
                print(f"    Confidence: {enrichment['Confidence_Det']}")
            else:
                # Failed to enrich - add to manual queue
                manual = company.copy()
                manual['Failure_Reason'] = 'No candidates passed validation gates'
                manual_queue.append(manual)
                enriched_companies.append(company)  # Keep original data
                stats['failed'] += 1

                print(f"  ✗ Failed: No candidates passed validation")

        except Exception as e:
            # Error during enrichment - add to manual queue
            print(f"  ✗ Error: {e}")
            manual = company.copy()
            manual['Failure_Reason'] = f"Error: {type(e).__name__}: {str(e)}"
            manual_queue.append(manual)
            enriched_companies.append(company)  # Keep original data
            stats['failed'] += 1

        # Update checkpoint
        processed_indices.append(i)

        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)

        # Save checkpoint periodically
        if (i + 1) % CHECKPOINT_INTERVAL == 0:
            print()
            print(f"  Saving checkpoint ({i+1}/{stats['total']})...")
            save_checkpoint(processed_indices)
            cache.save()
            print()

    print()
    print("=" * 70)

    # Save results
    WORKING_DIR.mkdir(parents=True, exist_ok=True)

    # Write Path A enriched companies
    if enriched_companies:
        # Ensure all required columns exist
        fieldnames = [
            'Company Name', 'Website', 'City', 'Address', 'Company Stage',
            'Focus Areas', 'Validation_Source', 'Place_ID', 'Confidence_Det',
            'Validation_Reason'
        ]

        with open(OUTPUT_PATH_A, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for company in enriched_companies:
                # Fill in missing fields with empty strings
                row = {field: company.get(field, '') for field in fieldnames}
                writer.writerow(row)

        print(f"✓ Wrote {len(enriched_companies)} companies to: {OUTPUT_PATH_A}")

    # Write manual review queue
    if manual_queue:
        fieldnames = list(manual_queue[0].keys())
        with open(MANUAL_QUEUE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manual_queue)

        print(f"✓ Wrote {len(manual_queue)} companies to manual queue: {MANUAL_QUEUE}")

    # Save cache
    cache.save()
    print(f"✓ Saved Place Details cache: {PLACE_DETAILS_CACHE}")

    # Generate API usage report
    report = counter.report()
    with open(API_USAGE_REPORT, 'w') as f:
        f.write(report)
        f.write("\n\nPath A Statistics:\n")
        f.write(f"  Total Path A companies: {stats['total']}\n")
        f.write(f"  Successfully enriched: {stats['enriched']} ({100*stats['enriched']/stats['total']:.1f}%)\n")
        f.write(f"  Failed (manual review): {stats['failed']} ({100*stats['failed']/stats['total']:.1f}%)\n")
        f.write(f"  Skipped (resumed): {stats['skipped']}\n")

    print(f"✓ Wrote API usage report: {API_USAGE_REPORT}")
    print()

    # Clear checkpoint after successful completion
    clear_checkpoint()

    # Print summary
    print("=" * 70)
    print("PATH A ENRICHMENT SUMMARY")
    print("=" * 70)
    print(f"Total Path A companies: {stats['total']}")
    print(f"Successfully enriched: {stats['enriched']} ({100*stats['enriched']/stats['total']:.1f}%)")
    print(f"Failed (manual review): {stats['failed']} ({100*stats['failed']/stats['total']:.1f}%)")
    print()
    print("API Usage:")
    print(f"  Text Search calls: {counter.text_search_calls}")
    print(f"  Place Details calls: {counter.place_details_calls}")
    print(f"  Total calls: {counter.total_calls()}")
    print(f"  Estimated cost: ${counter.estimated_cost():.2f}")
    print()


if __name__ == '__main__':
    main()
