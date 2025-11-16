#!/usr/bin/env python3
"""
Path B Enrichment: Anthropic structured outputs with Google Places tool use.

This script implements Phase 3 (Issues #15-19) from V4.3 work plan:
- Google Places tool definitions and Python wrappers
- JSON schema for company_enrichment_result
- Validation prompt with hard gates (9-county, aggregator, business-type, multi-tenant)
- Tool-use controller loop (temperature=0, max 8 rounds)
- Acceptance threshold ≥ 0.75
- Token usage tracking

Usage:
    export GOOGLE_MAPS_API_KEY="your-api-key-here"
    export ANTHROPIC_API_KEY="your-api-key-here"
    python3 path_b_enrichment.py

Author: Bay Area Biotech Map V4.3
Date: 2025-11-16
"""

import csv
import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Import V4.3 modules
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config.geography import BAY_COUNTIES, CITY_WHITELIST
    from utils.helpers import is_aggregator, etld1
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

try:
    import anthropic
except ImportError:
    print("Error: anthropic library not installed")
    print("Run: pip install anthropic")
    sys.exit(1)


# ============================================================================
# Configuration
# ============================================================================

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
WORKING_DIR = DATA_DIR / "working"

INPUT_FILE = WORKING_DIR / "path_b_queue.csv"
OUTPUT_FILE = WORKING_DIR / "companies_enriched_path_b.csv"
MANUAL_QUEUE = WORKING_DIR / "manual_review_queue_path_b.csv"
ANTHROPIC_USAGE_REPORT = WORKING_DIR / "anthropic_usage_report.txt"

# Anthropic configuration
ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"  # Claude Sonnet 4.5 (latest)
TEMPERATURE = 0
MAX_TOKENS = 1200
MAX_TOOL_ROUNDS = 8

# Acceptance thresholds
ACCEPTANCE_THRESHOLD = 0.75

# Rate limiting
RATE_LIMIT_DELAY = 0.5  # Delay between API calls (seconds)


# ============================================================================
# Google Places Tool Definitions
# ============================================================================

SEARCH_PLACES_TOOL = {
    "name": "search_places",
    "description": (
        "Search for places using Google Places Text Search API. "
        "Returns a list of place candidates matching the query. "
        "Use this to find potential matches for a company by name and location."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Text search query. Best practice: include company name, "
                    "city, state, and industry keywords (e.g., 'Genentech South San Francisco CA biotech')"
                )
            },
            "location_bias": {
                "type": "string",
                "description": (
                    "Optional. Geographic bias as 'lat,lng' to prioritize nearby results. "
                    "Example: '37.6624,-122.3801' for South San Francisco."
                ),
                "default": ""
            }
        },
        "required": ["query"]
    }
}

GET_PLACE_DETAILS_TOOL = {
    "name": "get_place_details",
    "description": (
        "Get detailed information about a specific place using its place_id. "
        "Returns name, address, website, business types, coordinates, and operational status. "
        "Use this after search_places to get full details for validation."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "place_id": {
                "type": "string",
                "description": "The place_id from a search_places result."
            }
        },
        "required": ["place_id"]
    }
}

# Tool registry
TOOL_REGISTRY = {}


# ============================================================================
# Tool Python Wrappers
# ============================================================================

def search_places_tool(query: str, location_bias: str = "") -> dict:
    """
    Python wrapper for search_places tool.

    Args:
        query: Text search query
        location_bias: Optional lat,lng bias

    Returns:
        Dict with status and results list
    """
    gmaps = TOOL_REGISTRY.get('gmaps')
    if not gmaps:
        return {"status": "ERROR", "error": "Google Maps client not initialized"}

    try:
        # Parse location bias if provided
        location = None
        if location_bias:
            parts = location_bias.split(',')
            if len(parts) == 2:
                try:
                    lat = float(parts[0].strip())
                    lng = float(parts[1].strip())
                    location = {'lat': lat, 'lng': lng}
                except ValueError:
                    pass

        # Call Google Places Text Search
        if location:
            result = gmaps.places(query, location=location)
        else:
            result = gmaps.places(query)

        if result.get('status') == 'OK':
            # Return simplified results
            results = []
            for place in result.get('results', [])[:5]:  # Top 5
                results.append({
                    'place_id': place.get('place_id'),
                    'name': place.get('name'),
                    'address': place.get('formatted_address', ''),
                    'types': place.get('types', [])
                })

            return {
                "status": "OK",
                "results": results,
                "result_count": len(results)
            }
        else:
            return {
                "status": result.get('status', 'ERROR'),
                "results": [],
                "result_count": 0
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "results": [],
            "result_count": 0
        }


def get_place_details_tool(place_id: str) -> dict:
    """
    Python wrapper for get_place_details tool.

    Args:
        place_id: Place ID from search results

    Returns:
        Dict with status and place details
    """
    gmaps = TOOL_REGISTRY.get('gmaps')
    if not gmaps:
        return {"status": "ERROR", "error": "Google Maps client not initialized"}

    try:
        # Call Google Places Details API
        fields = [
            'name',
            'formatted_address',
            'website',
            'types',
            'geometry',
            'business_status'
        ]

        result = gmaps.place(place_id, fields=fields)

        if result.get('status') == 'OK':
            details = result.get('result', {})
            geometry = details.get('geometry', {})
            location = geometry.get('location', {})

            return {
                "status": "OK",
                "place_id": place_id,
                "name": details.get('name', ''),
                "formatted_address": details.get('formatted_address', ''),
                "website": details.get('website', ''),
                "types": details.get('types', []),
                "latitude": location.get('lat'),
                "longitude": location.get('lng'),
                "business_status": details.get('business_status', '')
            }
        else:
            return {
                "status": result.get('status', 'ERROR'),
                "error": f"Place Details API returned {result.get('status')}"
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e)
        }


# Register tools
TOOL_REGISTRY['search_places'] = search_places_tool
TOOL_REGISTRY['get_place_details'] = get_place_details_tool


# ============================================================================
# JSON Schema for Structured Output
# ============================================================================

COMPANY_ENRICHMENT_SCHEMA = {
    "name": "company_enrichment_result",
    "description": "Structured output for company enrichment with validation",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "Company name from the enrichment"
            },
            "website": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "null"}
                ],
                "description": "Company website URL (null if not found or uncertain)"
            },
            "address": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "null"}
                ],
                "description": "Full formatted address (null if not found or uncertain)"
            },
            "city": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "null"}
                ],
                "description": "City name (null if not found or uncertain)"
            },
            "place_id": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "null"}
                ],
                "description": "Google Places place_id (null if not found)"
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score from 0.0 to 1.0"
            },
            "validation": {
                "type": "object",
                "properties": {
                    "in_bay_area": {
                        "type": "boolean",
                        "description": "True if location is in 9-county Bay Area"
                    },
                    "is_business": {
                        "type": "boolean",
                        "description": "True if types indicate legitimate business (not real estate, lodging, or premise-only)"
                    },
                    "brand_domain_ok": {
                        "type": "boolean",
                        "description": "True if website is not an aggregator (LinkedIn, Bloomberg, etc.)"
                    },
                    "multi_tenant_ok": {
                        "type": "boolean",
                        "description": "True if not at known incubator address, or name/domain strongly match"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of validation decision"
                    }
                },
                "required": ["in_bay_area", "is_business", "brand_domain_ok", "multi_tenant_ok", "reasoning"],
                "additionalProperties": False
            }
        },
        "required": ["company_name", "website", "address", "city", "place_id", "confidence", "validation"],
        "additionalProperties": False
    }
}


# ============================================================================
# Validation Prompt Template
# ============================================================================

VALIDATION_PROMPT_TEMPLATE = """You are a data validation assistant helping to enrich Bay Area biotech company information.

**Company to validate:**
- Name: {company_name}
- City hint: {city}

**Your task:**
Use the provided tools to search for this company and validate the information according to strict criteria.

**HARD GATES (Must all pass for acceptance ≥ 0.75):**

1. **Bay Area Geographic Scope (9-county hard gate):**
   - REQUIRED counties: Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano, Sonoma
   - REQUIRED cities: {city_whitelist}
   - REJECT: Davis, Sacramento, San Diego, or any location outside the 9-county Bay Area
   - Use coordinates to verify if uncertain

2. **Aggregator Rejection:**
   - REJECT if website is LinkedIn, Bloomberg, Crunchbase, ZoomInfo, or similar aggregator
   - REJECT if website is domain parking or "for sale" page
   - Prefer NULL over aggregator websites

3. **Business Type Filtering:**
   - ACCEPT: Biotech, pharmaceutical, life sciences, research, healthcare, medical device companies
   - REJECT: Real estate agencies, lodging, premise-only locations, parking, storage, lawyers, accounting
   - Check Google Places 'types' field carefully

4. **Multi-Tenant Address Rules:**
   - Known incubator/shared-space addresses require STRONG brand-domain evidence
   - If address contains "Gateway", "QB3", "BioHub", "Mission Bay", or similar: confidence must be ≥ 0.85
   - Name similarity AND domain match required for multi-tenant locations

5. **Acceptance Threshold:**
   - confidence ≥ 0.75 required to accept
   - confidence < 0.75 should return null fields (except company_name)

6. **Prefer Nulls Over Wrong Data:**
   - If uncertain about website: set to null
   - If uncertain about address: set to null
   - If location is outside Bay Area: set confidence to 0.0 and all fields to null
   - NEVER guess or hallucinate data

**Process:**
1. Use search_places with query like "{company_name} {city} CA biotech"
2. For top candidates, use get_place_details to get full information
3. Validate each candidate against all hard gates
4. Calculate confidence based on:
   - Name similarity (up to 0.4)
   - Geographic match (up to 0.3)
   - Business type appropriateness (up to 0.2)
   - Source reliability (up to 0.1)
5. Select best candidate if confidence ≥ 0.75, otherwise return nulls

**Output:**
Return a company_enrichment_result with all fields populated according to validation rules.
"""


# ============================================================================
# Anthropic Token Usage Counter
# ============================================================================

class AnthropicUsageCounter:
    """Track Anthropic API usage and costs."""

    def __init__(self):
        self.total_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def record_usage(self, usage):
        """
        Record usage from API response.

        Args:
            usage: Usage object from response (response.usage)
        """
        self.total_calls += 1
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens

    def total_tokens(self) -> int:
        """Get total tokens (input + output)."""
        return self.total_input_tokens + self.total_output_tokens

    def report(self) -> str:
        """Generate usage report."""
        lines = [
            "Anthropic API Usage Report",
            "=" * 70,
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "API Calls:",
            f"  Total calls: {self.total_calls}",
            "",
            "Token Usage:",
            f"  Input tokens: {self.total_input_tokens:,}",
            f"  Output tokens: {self.total_output_tokens:,}",
            f"  Total tokens: {self.total_tokens():,}",
            "",
            "Estimated Cost:",
            "  Note: Anthropic pricing varies by model and volume tier.",
            "  For Claude 3.5 Sonnet (as of 2024):",
            f"    Input: ~${self.total_input_tokens * 0.000003:.4f} (at $3/MTok)",
            f"    Output: ~${self.total_output_tokens * 0.000015:.4f} (at $15/MTok)",
            f"    Total estimate: ~${(self.total_input_tokens * 0.000003 + self.total_output_tokens * 0.000015):.4f}",
            "",
            "  (Check current pricing at https://anthropic.com/pricing)",
        ]
        return "\n".join(lines)


# ============================================================================
# Tool Use Controller Loop
# ============================================================================

def run_structured_enrichment(
    company_name: str,
    city: str,
    client: anthropic.Anthropic,
    counter: AnthropicUsageCounter
) -> dict:
    """
    Run Anthropic structured enrichment with tool use.

    Args:
        company_name: Company name to enrich
        city: City hint for the company
        client: Anthropic client
        counter: Usage counter

    Returns:
        Enrichment result dict

    Raises:
        RuntimeError: If controller loop fails or exceeds max rounds
    """
    # Build prompt with validation instructions
    city_whitelist = ", ".join(sorted(CITY_WHITELIST)[:20]) + ", ..."  # First 20 cities

    prompt = VALIDATION_PROMPT_TEMPLATE.format(
        company_name=company_name,
        city=city,
        city_whitelist=city_whitelist
    )

    # Initialize message history
    messages = [
        {"role": "user", "content": prompt}
    ]

    # Tool use loop (max 8 rounds)
    for round_num in range(MAX_TOOL_ROUNDS):
        try:
            # Call Anthropic API
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                tools=[SEARCH_PLACES_TOOL, GET_PLACE_DETAILS_TOOL],
                messages=messages
            )

            # Record usage
            counter.record_usage(response.usage)

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Extract final JSON from response
                for block in response.content:
                    if hasattr(block, 'text') and block.text:
                        # Try to parse as JSON
                        try:
                            result = json.loads(block.text)
                            return result
                        except json.JSONDecodeError:
                            pass

                # No valid JSON found
                raise RuntimeError(f"No JSON output in end_turn response: {response.content}")

            elif response.stop_reason == "tool_use":
                # Process tool use blocks
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_use_id = block.id

                        # Execute tool
                        if tool_name in TOOL_REGISTRY:
                            tool_func = TOOL_REGISTRY[tool_name]
                            tool_output = tool_func(**tool_input)
                        else:
                            tool_output = {
                                "status": "ERROR",
                                "error": f"Unknown tool: {tool_name}"
                            }

                        # Build tool_result block
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps(tool_output)
                        })

                # Append assistant message and tool results to history
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

                # Continue loop
                continue

            elif response.stop_reason == "max_tokens":
                raise RuntimeError("Response exceeded max_tokens limit")

            else:
                raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason}")

        except anthropic.APIError as e:
            raise RuntimeError(f"Anthropic API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error in tool use loop: {e}")

    # Exceeded max rounds
    raise RuntimeError(f"Exceeded {MAX_TOOL_ROUNDS} tool use rounds without completion")


# ============================================================================
# Acceptance Logic
# ============================================================================

def accept_enrichment_result(result: dict, company_name: str) -> Tuple[bool, dict]:
    """
    Apply acceptance logic to enrichment result.

    Acceptance criteria:
    - confidence ≥ 0.75
    - in_bay_area == True
    - is_business == True
    - brand_domain_ok == True (not aggregator)

    Args:
        result: Enrichment result from run_structured_enrichment
        company_name: Original company name

    Returns:
        (accepted, enriched_data) tuple
        - accepted: True if passes all gates
        - enriched_data: Dict with enrichment fields
    """
    # Parse result
    confidence = result.get('confidence', 0.0)
    validation = result.get('validation', {})

    in_bay_area = validation.get('in_bay_area', False)
    is_business = validation.get('is_business', False)
    brand_domain_ok = validation.get('brand_domain_ok', True)  # Default True

    website = result.get('website')

    # Check if website is aggregator (double-check)
    if website and is_aggregator(website):
        brand_domain_ok = False

    # Apply acceptance gates
    accepted = (
        confidence >= ACCEPTANCE_THRESHOLD
        and in_bay_area
        and is_business
        and brand_domain_ok
    )

    if accepted:
        # Build enriched data
        enriched_data = {
            'Company Name': company_name,
            'Website': website or '',
            'Address': result.get('address') or '',
            'City': result.get('city') or '',
            'Place_ID': result.get('place_id') or '',
            'Confidence': f"{confidence:.3f}",
            'Validation_Source': 'PathB',
            'Validation_JSON': json.dumps(validation)
        }
    else:
        # Rejected - keep nulls
        rejection_reason = validation.get('reasoning', 'Failed acceptance criteria')
        enriched_data = {
            'Company Name': company_name,
            'Website': '',
            'Address': '',
            'City': '',
            'Place_ID': '',
            'Confidence': f"{confidence:.3f}",
            'Validation_Source': 'PathB',
            'Validation_JSON': json.dumps(validation),
            'Rejection_Reason': rejection_reason
        }

    return accepted, enriched_data


# ============================================================================
# Main Processing
# ============================================================================

def main():
    """Main Path B enrichment workflow."""
    parser = argparse.ArgumentParser(description='Path B Enrichment with Anthropic structured outputs')
    parser.add_argument('--limit', type=int, help='Limit number of companies to process (for testing)')
    args = parser.parse_args()

    print("=" * 70)
    print("Path B Enrichment: Anthropic Structured Outputs")
    print("=" * 70)
    print()

    # Check for API keys
    google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not google_api_key:
        print("Error: GOOGLE_MAPS_API_KEY environment variable not set")
        sys.exit(1)

    if not anthropic_api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Initialize clients
    try:
        gmaps = googlemaps.Client(key=google_api_key)
        TOOL_REGISTRY['gmaps'] = gmaps
        print("✓ Google Maps API client initialized")
    except Exception as e:
        print(f"Error initializing Google Maps client: {e}")
        sys.exit(1)

    try:
        client = anthropic.Anthropic(api_key=anthropic_api_key)
        print("✓ Anthropic API client initialized")
    except Exception as e:
        print(f"Error initializing Anthropic client: {e}")
        sys.exit(1)

    # Initialize counter
    counter = AnthropicUsageCounter()
    print()

    # Load Path B queue
    if not INPUT_FILE.exists():
        print(f"Error: Input file not found: {INPUT_FILE}")
        print("Run enrich_with_google_maps.py first to generate Path B queue")
        sys.exit(1)

    print(f"Loading Path B queue from: {INPUT_FILE}")
    companies = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row)

    total_companies = len(companies)

    # Apply limit if specified
    if args.limit:
        companies = companies[:args.limit]
        print(f"  Loaded {total_companies} companies (processing {len(companies)} with --limit)")
    else:
        print(f"  Loaded {len(companies)} companies")

    print()

    # Process companies
    print(f"Processing {len(companies)} Path B companies...")
    print()

    enriched_companies = []
    manual_queue = []
    stats = {
        'total': len(companies),
        'accepted': 0,
        'rejected': 0,
        'errors': 0
    }

    for i, company in enumerate(companies):
        company_name = company.get('Company Name', '')
        city = company.get('City', '')

        print(f"[{i+1}/{stats['total']}] {company_name} ({city})")

        try:
            # Run structured enrichment
            result = run_structured_enrichment(company_name, city, client, counter)

            # Apply acceptance logic
            accepted, enriched_data = accept_enrichment_result(result, company_name)

            if accepted:
                enriched_companies.append(enriched_data)
                stats['accepted'] += 1

                address_short = enriched_data['Address'][:50]
                print(f"  ✓ Accepted: {address_short}...")
                print(f"    Confidence: {enriched_data['Confidence']}")
            else:
                # Rejected - add to manual queue
                manual_queue.append(enriched_data)
                enriched_companies.append(enriched_data)  # Still include in output
                stats['rejected'] += 1

                rejection_reason = enriched_data.get('Rejection_Reason', 'Unknown')
                print(f"  ✗ Rejected: {rejection_reason}")

        except Exception as e:
            # Error during enrichment
            print(f"  ✗ Error: {e}")

            error_data = {
                'Company Name': company_name,
                'Website': '',
                'Address': '',
                'City': city,
                'Place_ID': '',
                'Confidence': '0.000',
                'Validation_Source': 'PathB',
                'Validation_JSON': json.dumps({'error': str(e)}),
                'Error': str(e)
            }

            manual_queue.append(error_data)
            enriched_companies.append(error_data)
            stats['errors'] += 1

        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)

        # Progress update every 10 companies
        if (i + 1) % 10 == 0:
            print()
            print(f"  Progress: {i+1}/{stats['total']} ({100*(i+1)/stats['total']:.1f}%)")
            print(f"  Accepted: {stats['accepted']}, Rejected: {stats['rejected']}, Errors: {stats['errors']}")
            print()

    print()
    print("=" * 70)

    # Save results
    WORKING_DIR.mkdir(parents=True, exist_ok=True)

    # Write Path B enriched companies
    if enriched_companies:
        fieldnames = [
            'Company Name', 'Website', 'City', 'Address',
            'Place_ID', 'Confidence', 'Validation_Source', 'Validation_JSON'
        ]

        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for company in enriched_companies:
                row = {field: company.get(field, '') for field in fieldnames}
                writer.writerow(row)

        print(f"✓ Wrote {len(enriched_companies)} companies to: {OUTPUT_FILE}")

    # Write manual review queue
    if manual_queue:
        fieldnames = list(manual_queue[0].keys())
        with open(MANUAL_QUEUE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manual_queue)

        print(f"✓ Wrote {len(manual_queue)} companies to manual queue: {MANUAL_QUEUE}")

    # Generate Anthropic usage report
    report = counter.report()
    with open(ANTHROPIC_USAGE_REPORT, 'w') as f:
        f.write(report)
        f.write("\n\nPath B Statistics:\n")
        f.write(f"  Total Path B companies: {stats['total']}\n")
        f.write(f"  Accepted: {stats['accepted']} ({100*stats['accepted']/stats['total']:.1f}%)\n")
        f.write(f"  Rejected: {stats['rejected']} ({100*stats['rejected']/stats['total']:.1f}%)\n")
        f.write(f"  Errors: {stats['errors']} ({100*stats['errors']/stats['total']:.1f}%)\n")

    print(f"✓ Wrote Anthropic usage report: {ANTHROPIC_USAGE_REPORT}")
    print()

    # Print summary
    print("=" * 70)
    print("PATH B ENRICHMENT SUMMARY")
    print("=" * 70)
    print(f"Total Path B companies: {stats['total']}")
    print(f"Accepted: {stats['accepted']} ({100*stats['accepted']/stats['total']:.1f}%)")
    print(f"Rejected: {stats['rejected']} ({100*stats['rejected']/stats['total']:.1f}%)")
    print(f"Errors: {stats['errors']} ({100*stats['errors']/stats['total']:.1f}%)")
    print()
    print("Anthropic API Usage:")
    print(f"  Total calls: {counter.total_calls}")
    print(f"  Input tokens: {counter.total_input_tokens:,}")
    print(f"  Output tokens: {counter.total_output_tokens:,}")
    print(f"  Total tokens: {counter.total_tokens():,}")
    print()


if __name__ == '__main__':
    main()
