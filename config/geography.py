"""
Canonical Bay Area geographic definitions for V4.3.

This module provides the authoritative geofence logic used across all
data extraction, merging, and enrichment scripts.

Geographic Scope:
- 9-county Bay Area: Alameda, Contra Costa, Marin, Napa, San Francisco,
  San Mateo, Santa Clara, Solano, Sonoma
- ~60 whitelisted cities across these counties
- 60-mile radius backstop from San Francisco (37.7749, -122.4194)

Author: Bay Area Biotech Map V4.3
Date: 2025-11-15
"""

import re
from math import radians, cos, sin, asin, sqrt
from typing import Tuple, Optional


# ============================================================================
# Constants
# ============================================================================

BAY_COUNTIES = [
    "Alameda",
    "Contra Costa",
    "Marin",
    "Napa",
    "San Francisco",
    "San Mateo",
    "Santa Clara",
    "Solano",
    "Sonoma"
]

CITY_WHITELIST = {
    # San Francisco County
    "San Francisco",

    # San Mateo County
    "South San Francisco",
    "San Mateo",
    "Redwood City",
    "Menlo Park",
    "Brisbane",
    "Burlingame",
    "Foster City",
    "San Carlos",
    "Belmont",
    "Millbrae",
    "Daly City",
    "Half Moon Bay",
    "Pacifica",
    "San Bruno",
    "Portola Valley",
    "Woodside",
    "Atherton",
    "Hillsborough",
    "East Palo Alto",

    # Alameda County
    "Oakland",
    "Berkeley",
    "Emeryville",
    "Alameda",
    "Hayward",
    "Fremont",
    "Newark",
    "Union City",
    "Pleasanton",
    "Dublin",
    "Livermore",
    "Albany",
    "San Leandro",
    "Piedmont",
    "Castro Valley",

    # Santa Clara County
    "San Jose",
    "Palo Alto",
    "Mountain View",
    "Sunnyvale",
    "Santa Clara",
    "Cupertino",
    "Milpitas",
    "Campbell",
    "Los Gatos",
    "Saratoga",
    "Morgan Hill",
    "Los Altos",
    "Los Altos Hills",
    "Gilroy",

    # Contra Costa County
    "Richmond",
    "Concord",
    "Walnut Creek",
    "San Ramon",
    "Danville",
    "Pleasant Hill",
    "Martinez",
    "Antioch",
    "Pittsburg",
    "Brentwood",
    "Lafayette",
    "Orinda",
    "Moraga",

    # Marin County
    "San Rafael",
    "Novato",
    "Mill Valley",
    "Larkspur",
    "Corte Madera",
    "Tiburon",
    "Sausalito",
    "Belvedere",
    "Ross",
    "Fairfax",
    "San Anselmo",

    # Solano County
    "Benicia",
    "Fairfield",
    "Vallejo",
    "Vacaville",
    "Suisun City",

    # Sonoma County
    "Petaluma",
    "Santa Rosa",
    "Rohnert Park",
    "Sebastopol",
    "Sonoma",

    # Napa County
    "Napa",
    "American Canyon",
    "Calistoga",
    "St. Helena",
    "Yountville",
}

# Normalized alias mappings for common abbreviations and variants
CITY_ALIASES = {
    "south sf": "South San Francisco",
    "sf": "San Francisco",
    "sj": "San Jose",
    "e palo alto": "East Palo Alto",
    "east pa": "East Palo Alto",
}

# San Francisco coordinates (used as center for radius checks)
SF_LATLNG: Tuple[float, float] = (37.7749, -122.4194)

# 60-mile radius in meters (60 miles ≈ 96,560 meters; rounded to 97,000)
BAY_RADIUS_M: int = 97000


# ============================================================================
# Helper Functions
# ============================================================================

def normalize_city_name(city: str) -> str:
    """
    Normalize city name for comparison.

    Args:
        city: City name (may contain abbreviations, case variations, extra whitespace)

    Returns:
        Normalized city name

    Examples:
        >>> normalize_city_name("  South SF  ")
        'south san francisco'
        >>> normalize_city_name("San Francisco")
        'san francisco'
    """
    if not city:
        return ""

    # Strip whitespace and lowercase
    normalized = city.strip().lower()

    # Apply alias mapping
    if normalized in CITY_ALIASES:
        normalized = CITY_ALIASES[normalized].lower()

    return normalized


def is_in_bay_area_city(city: str) -> bool:
    """
    Check if city is in the Bay Area city whitelist.

    Args:
        city: City name (case-insensitive, handles common abbreviations)

    Returns:
        True if city is in Bay Area whitelist, False otherwise

    Examples:
        >>> is_in_bay_area_city("South San Francisco")
        True
        >>> is_in_bay_area_city("South SF")
        True
        >>> is_in_bay_area_city("Davis")
        False
        >>> is_in_bay_area_city("Sacramento")
        False
    """
    if not city:
        return False

    normalized = normalize_city_name(city)

    # Check against normalized whitelist
    for whitelist_city in CITY_WHITELIST:
        if normalized == whitelist_city.lower():
            return True

    return False


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth (in meters).

    Uses the Haversine formula.

    Args:
        lat1: Latitude of point 1 in decimal degrees
        lng1: Longitude of point 1 in decimal degrees
        lat2: Latitude of point 2 in decimal degrees
        lng2: Longitude of point 2 in decimal degrees

    Returns:
        Distance in meters

    Examples:
        >>> # SF to Oakland (approx 13 km)
        >>> distance = haversine_distance(37.7749, -122.4194, 37.8044, -122.2712)
        >>> 12000 < distance < 14000
        True
    """
    # Earth's radius in meters
    R = 6371000

    # Convert to radians
    lat1_rad, lng1_rad = radians(lat1), radians(lng1)
    lat2_rad, lng2_rad = radians(lat2), radians(lng2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad

    # Haversine formula
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng / 2) ** 2
    c = 2 * asin(sqrt(a))

    return R * c


def is_within_radius(lat: float, lng: float,
                     center: Tuple[float, float] = SF_LATLNG,
                     radius_m: int = BAY_RADIUS_M) -> bool:
    """
    Check if coordinates are within radius of center point.

    Args:
        lat: Latitude in decimal degrees
        lng: Longitude in decimal degrees
        center: Center point (lat, lng) tuple; defaults to San Francisco
        radius_m: Radius in meters; defaults to 97,000m (60 miles)

    Returns:
        True if within radius, False otherwise

    Examples:
        >>> # Oakland is within 60 miles of SF
        >>> is_within_radius(37.8044, -122.2712)
        True
        >>> # Los Angeles is outside 60 miles of SF
        >>> is_within_radius(34.0522, -118.2437)
        False
    """
    center_lat, center_lng = center
    distance = haversine_distance(lat, lng, center_lat, center_lng)
    return distance <= radius_m


def extract_city_from_address(address: str) -> Optional[str]:
    """
    Extract city name from a full address string.

    Args:
        address: Full address (e.g., "1 DNA Way, South San Francisco, CA 94080")

    Returns:
        City name if found, None otherwise

    Examples:
        >>> extract_city_from_address("1 DNA Way, South San Francisco, CA 94080")
        'South San Francisco'
        >>> extract_city_from_address("123 Main St, Berkeley, CA")
        'Berkeley'
    """
    if not address:
        return None

    # Common address formats:
    # "Street, City, State Zip"
    # "Street, City, CA"
    # Try to match City, State pattern

    # Pattern: comma, then city name, then comma or "CA" or "California"
    match = re.search(r',\s*([^,]+?),\s*(?:CA|California)', address, re.IGNORECASE)
    if match:
        potential_city = match.group(1).strip()
        # Validate it's not a ZIP code or state
        if not potential_city.isdigit() and len(potential_city) > 2:
            return potential_city

    # Fallback: split by comma and look for known cities
    parts = [part.strip() for part in address.split(',')]
    for part in parts:
        if is_in_bay_area_city(part):
            return part

    return None


def geofence_ok(address_or_city: str, lat: Optional[float] = None,
                lng: Optional[float] = None) -> bool:
    """
    Generous geofence check: accept if city matches OR coordinates within radius.

    This is the primary geofencing function used across the V4.3 pipeline.
    It accepts a location if EITHER:
    - The city name (extracted from address or passed directly) is in the whitelist, OR
    - The lat/lng coordinates are within 60 miles of San Francisco

    Args:
        address_or_city: Full address string or city name
        lat: Optional latitude in decimal degrees
        lng: Optional longitude in decimal degrees

    Returns:
        True if location passes geofence (city OR radius check), False otherwise

    Examples:
        >>> # City name match
        >>> geofence_ok("South San Francisco")
        True
        >>> # Full address with whitelisted city
        >>> geofence_ok("1 DNA Way, South San Francisco, CA 94080")
        True
        >>> # Coordinates within radius (Oakland)
        >>> geofence_ok("Some address", lat=37.8044, lng=-122.2712)
        True
        >>> # Both out of scope
        >>> geofence_ok("Davis")
        False
        >>> # Davis with coordinates
        >>> geofence_ok("Davis, CA", lat=38.5449, lng=-121.7405)
        False
    """
    if not address_or_city and (lat is None or lng is None):
        return False

    # Check 1: City name (either direct or extracted from address)
    if address_or_city:
        # Try as direct city name
        if is_in_bay_area_city(address_or_city):
            return True

        # Try extracting city from address
        extracted_city = extract_city_from_address(address_or_city)
        if extracted_city and is_in_bay_area_city(extracted_city):
            return True

    # Check 2: Coordinates within radius (if provided)
    if lat is not None and lng is not None:
        if is_within_radius(lat, lng):
            return True

    # Neither check passed
    return False


# ============================================================================
# Validation Functions
# ============================================================================

def is_valid_county(county: str) -> bool:
    """
    Check if county is one of the 9 Bay Area counties.

    Args:
        county: County name

    Returns:
        True if valid Bay Area county, False otherwise

    Examples:
        >>> is_valid_county("Alameda")
        True
        >>> is_valid_county("Yolo")
        False
    """
    if not county:
        return False

    return county.strip() in BAY_COUNTIES


def get_county_for_city(city: str) -> Optional[str]:
    """
    Get the county for a given city (if known).

    Note: This is a simple mapping for common cases. Not all cities are mapped.

    Args:
        city: City name

    Returns:
        County name if known, None otherwise
    """
    # Normalize input
    normalized = normalize_city_name(city)

    # Simple mapping (not exhaustive, but covers major cities)
    CITY_TO_COUNTY = {
        "san francisco": "San Francisco",
        "oakland": "Alameda",
        "berkeley": "Alameda",
        "emeryville": "Alameda",
        "alameda": "Alameda",
        "fremont": "Alameda",
        "hayward": "Alameda",
        "south san francisco": "San Mateo",
        "san mateo": "San Mateo",
        "redwood city": "San Mateo",
        "menlo park": "San Mateo",
        "foster city": "San Mateo",
        "burlingame": "San Mateo",
        "san jose": "Santa Clara",
        "palo alto": "Santa Clara",
        "mountain view": "Santa Clara",
        "sunnyvale": "Santa Clara",
        "santa clara": "Santa Clara",
        "cupertino": "Santa Clara",
        "milpitas": "Santa Clara",
        "san rafael": "Marin",
        "novato": "Marin",
        "napa": "Napa",
        "vallejo": "Solano",
        "fairfield": "Solano",
        "concord": "Contra Costa",
        "walnut creek": "Contra Costa",
        "richmond": "Contra Costa",
        "santa rosa": "Sonoma",
        "petaluma": "Sonoma",
    }

    return CITY_TO_COUNTY.get(normalized)


# ============================================================================
# Module Info
# ============================================================================

__all__ = [
    "BAY_COUNTIES",
    "CITY_WHITELIST",
    "SF_LATLNG",
    "BAY_RADIUS_M",
    "normalize_city_name",
    "is_in_bay_area_city",
    "is_within_radius",
    "extract_city_from_address",
    "geofence_ok",
    "is_valid_county",
    "get_county_for_city",
    "haversine_distance",
]
