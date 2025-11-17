"""
California-wide geographic definitions for expanded biotech mapping.

This module provides geofence logic for all of California, capturing
the major biotech hubs beyond just the Bay Area.

Geographic Scope:
- All California cities
- Major biotech hubs: Bay Area, San Diego, Los Angeles, Orange County
- Simplified validation: any valid CA city passes

Author: Bay Area Biotech Map V4.3 (CA-wide variant)
Date: 2025-11-15
"""

import re
from typing import Optional


# ============================================================================
# Constants
# ============================================================================

# Major California biotech hubs (not exhaustive, but covers main clusters)
CA_BIOTECH_CITIES = {
    # === BAY AREA (original 9 counties) ===
    # San Francisco County
    "San Francisco", "SF",

    # San Mateo County
    "South San Francisco", "South SF", "San Mateo", "Redwood City",
    "Menlo Park", "Brisbane", "Burlingame", "Foster City", "San Carlos",
    "Belmont", "Millbrae", "Daly City", "San Bruno",

    # Alameda County
    "Oakland", "Berkeley", "Emeryville", "Alameda", "Hayward",
    "Fremont", "Newark", "Union City", "Pleasanton", "Dublin",
    "Livermore", "Albany", "San Leandro",

    # Santa Clara County
    "San Jose", "Palo Alto", "Mountain View", "Sunnyvale",
    "Santa Clara", "Cupertino", "Milpitas", "Campbell",
    "Los Gatos", "Los Altos",

    # Contra Costa County
    "Richmond", "Concord", "Walnut Creek", "San Ramon",

    # Marin County
    "San Rafael", "Novato", "Mill Valley",

    # Solano County
    "Benicia", "Fairfield", "Vallejo", "Vacaville",

    # Sonoma County
    "Petaluma", "Santa Rosa", "Rohnert Park",

    # Napa County
    "Napa",

    # === SAN DIEGO AREA (major biotech hub) ===
    "San Diego", "La Jolla", "Carlsbad", "Solana Beach",
    "Del Mar", "Encinitas", "San Marcos", "Vista",
    "Oceanside", "Escondido", "Poway", "Santee",
    "La Mesa", "El Cajon", "Chula Vista", "National City",
    "Sorrento Valley", "Torrey Pines",

    # === LOS ANGELES AREA ===
    "Los Angeles", "LA", "Pasadena", "Glendale",
    "Santa Monica", "Beverly Hills", "West Hollywood",
    "Culver City", "El Segundo", "Manhattan Beach",
    "Torrance", "Long Beach", "Burbank", "Van Nuys",
    "Thousand Oaks", "Westlake Village", "Agoura Hills",
    "Calabasas", "Woodland Hills", "Sherman Oaks",

    # === ORANGE COUNTY ===
    "Irvine", "Newport Beach", "Costa Mesa", "Santa Ana",
    "Anaheim", "Orange", "Tustin", "Lake Forest",
    "Mission Viejo", "Laguna Beach", "Laguna Hills",
    "Aliso Viejo", "Huntington Beach", "Fountain Valley",

    # === VENTURA COUNTY ===
    "Ventura", "Oxnard", "Camarillo", "Simi Valley",
    "Moorpark",

    # === RIVERSIDE/SAN BERNARDINO ===
    "Riverside", "San Bernardino", "Ontario", "Rancho Cucamonga",
    "Corona", "Murrieta", "Temecula",

    # === CENTRAL VALLEY ===
    "Sacramento", "Davis", "Roseville", "Folsom",
    "Stockton", "Modesto", "Fresno", "Bakersfield",

    # === CENTRAL COAST ===
    "Santa Barbara", "Goleta", "San Luis Obispo",
    "Santa Cruz", "Monterey", "Salinas", "Carmel",
}

# Common city aliases and abbreviations
CITY_ALIASES = {
    "south sf": "South San Francisco",
    "sf": "San Francisco",
    "sj": "San Jose",
    "la": "Los Angeles",
    "sd": "San Diego",
    "oc": "Orange County",
}

# List of California-specific location indicators
CA_INDICATORS = [
    ", ca ", ", ca,", ", california",
    ", ca.", ", calif", " ca ",
    ", ca\n", ", ca\t", ", ca"
]


# ============================================================================
# Helper Functions
# ============================================================================

def normalize_city_name(city: str) -> str:
    """
    Normalize city name for comparison.

    Args:
        city: City name (may contain abbreviations, case variations)

    Returns:
        Normalized city name
    """
    if not city:
        return ""

    # Strip whitespace and lowercase
    normalized = city.strip().lower()

    # Remove trailing commas
    if normalized.endswith(','):
        normalized = normalized[:-1].strip()

    # Apply alias mapping
    if normalized in CITY_ALIASES:
        normalized = CITY_ALIASES[normalized].lower()

    return normalized


def is_california_city(city: str) -> bool:
    """
    Check if city is a known California biotech city.

    This is a permissive check - for CA-wide analysis, we accept
    any city that's in our known CA biotech cities list.

    Args:
        city: City name

    Returns:
        True if city is in California biotech cities list
    """
    if not city:
        return False

    normalized = normalize_city_name(city)

    # Check against normalized city list
    for ca_city in CA_BIOTECH_CITIES:
        if normalized == ca_city.lower():
            return True

    # Also accept if it has CA/California in it (very permissive)
    for indicator in CA_INDICATORS:
        if indicator.lower() in normalized:
            return True

    return False


def is_in_california(address_or_city: str) -> bool:
    """
    Simplified California geofence - accepts any CA location.

    This is the primary geofencing function for CA-wide analysis.
    Much more permissive than Bay Area geofencing.

    Args:
        address_or_city: Full address string or city name

    Returns:
        True if location appears to be in California
    """
    if not address_or_city:
        return False

    # Normalize input
    text_lower = address_or_city.lower()

    # Check 1: Is it a known CA biotech city?
    if is_california_city(address_or_city):
        return True

    # Check 2: Does it contain CA/California indicators?
    for indicator in CA_INDICATORS:
        if indicator.lower() in text_lower:
            return True

    # Check 3: Try extracting city from address format
    # Pattern: "Street, City, CA"
    match = re.search(r',\s*([^,]+?),\s*(?:CA|California)', address_or_city, re.IGNORECASE)
    if match:
        potential_city = match.group(1).strip()
        if potential_city and not potential_city.isdigit():
            # Found a city in CA format, accept it
            return True

    return False


def extract_city_from_address(address: str) -> Optional[str]:
    """
    Extract city name from a full address string.

    Args:
        address: Full address (e.g., "1 DNA Way, South San Francisco, CA 94080")

    Returns:
        City name if found, None otherwise
    """
    if not address:
        return None

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
        if is_california_city(part):
            return part

    return None


# ============================================================================
# Compatibility Functions (match original geography.py interface)
# ============================================================================

def is_in_bay_area_city(city: str) -> bool:
    """
    For CA-wide analysis, we accept any California city.
    This maintains compatibility with existing code.
    """
    return is_california_city(city)


def geofence_ok(address_or_city: str, lat: Optional[float] = None,
                lng: Optional[float] = None) -> bool:
    """
    CA-wide geofence check - very permissive.

    For California-wide analysis, we accept any CA location.
    Coordinates are ignored in this variant.

    Args:
        address_or_city: Full address string or city name
        lat: Ignored in CA-wide variant
        lng: Ignored in CA-wide variant

    Returns:
        True if location appears to be in California
    """
    return is_in_california(address_or_city)


def is_valid_county(county: str) -> bool:
    """
    For CA-wide analysis, accept any California county.

    This is a simplified check - in practice, any county
    name is accepted for CA-wide analysis.
    """
    # List of all 58 California counties (simplified - accept any)
    return True  # Accept all for CA-wide analysis


# ============================================================================
# Module Info
# ============================================================================

__all__ = [
    "CA_BIOTECH_CITIES",
    "normalize_city_name",
    "is_california_city",
    "is_in_california",
    "extract_city_from_address",
    "is_in_bay_area_city",  # Compatibility
    "geofence_ok",  # Compatibility
    "is_valid_county",  # Compatibility
]