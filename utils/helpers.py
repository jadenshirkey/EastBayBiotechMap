"""
Helper utilities for V4.3 Bay Area Biotech Map.

This module provides utility functions for:
- eTLD+1 extraction and brand token parsing
- Aggregator domain detection
- Company name normalization and similarity scoring
- Multi-tenant/incubator address handling
- Validation logic for Path A and Path B enrichment

Author: Bay Area Biotech Map V4.3
Date: 2025-11-15
"""

import re
from typing import Optional
import tldextract
from textdistance import jaro_winkler


# ============================================================================
# Constants
# ============================================================================

# Aggregator domains that should NOT be used as canonical websites
# These domains host multiple companies and are not suitable for deduplication
AGGREGATOR_ETLD1 = {
    "linkedin.com",
    "crunchbase.com",
    "facebook.com",
    "yelp.com",
    "wixsite.com",
    "squarespace.com",
    "godaddysites.com",
    "about.me",
    "linktr.ee",
    "google.com",  # Catches sites.google.com and other google subdomains
    # Additional common aggregators
    "twitter.com",
    "instagram.com",
    "youtube.com",
    "pinterest.com",
    "angellist.com",
    "biopharmguy.com",  # BioPharmGuy directory listings
    "wikipedia.org",  # Wikipedia articles
}

# Known multi-tenant/incubator addresses in the Bay Area
# Companies at these addresses need strong brand-domain validation
INCUBATOR_ADDRESSES = {
    # QB3 @ Genentech Hall (multiple biotechs)
    "201 Gateway Blvd, South San Francisco, CA 94080, USA",
    # IndieBio incubator
    "149 Commonwealth Dr, Menlo Park, CA 94025",
    # Mission Bio location (often shared)
    "544B Bryant St, San Francisco, CA 94107",
    # Additional common incubator addresses
    "1700 Owens St, San Francisco, CA 94158",  # Mission Bay area
    "953 Indiana St, San Francisco, CA 94107",  # Dogpatch Labs area
    "QB3@953, 953 Indiana St, San Francisco, CA 94107",
}


# ============================================================================
# URL and Domain Functions
# ============================================================================

def etld1(url: str) -> str:
    """
    Extract the eTLD+1 (effective top-level domain + 1) from a URL.

    This is the registered domain name, which is the public suffix plus one
    additional label. For example:
    - https://www.gene.com/about → gene.com
    - http://research.stanford.edu → stanford.edu
    - https://sites.google.com/view/mycompany → sites.google.com

    Args:
        url: Full URL or domain string

    Returns:
        eTLD+1 string (e.g., "gene.com"), or empty string if extraction fails

    Examples:
        >>> etld1("https://www.gene.com/about")
        'gene.com'
        >>> etld1("http://research.stanford.edu")
        'stanford.edu'
        >>> etld1("https://subdomain.example.co.uk")
        'example.co.uk'
    """
    if not url:
        return ""

    try:
        # tldextract handles various URL formats and edge cases
        extracted = tldextract.extract(url)

        # Combine domain + suffix (e.g., "gene" + "com" → "gene.com")
        if extracted.domain and extracted.suffix:
            return f"{extracted.domain}.{extracted.suffix}"

        return ""
    except Exception:
        # If extraction fails for any reason, return empty string
        return ""


def brand_token_from_etld1(domain: str) -> str:
    """
    Extract the brand token from an eTLD+1 domain.

    The brand token is the primary identifying part of the domain,
    typically the part before the TLD. This is used for matching
    company names to domains.

    Args:
        domain: eTLD+1 domain (e.g., "gene.com", "bio-rad.com")

    Returns:
        Brand token (e.g., "gene", "biorad")

    Examples:
        >>> brand_token_from_etld1("gene.com")
        'gene'
        >>> brand_token_from_etld1("bio-rad.com")
        'biorad'
        >>> brand_token_from_etld1("10xgenomics.com")
        '10xgenomics'
    """
    if not domain:
        return ""

    try:
        # Extract just the domain part (before the TLD)
        extracted = tldextract.extract(domain)
        brand = extracted.domain

        # Remove common separators (hyphens, underscores)
        # Keep alphanumeric only
        brand = re.sub(r'[-_]', '', brand)

        # Lowercase for case-insensitive matching
        return brand.lower()
    except Exception:
        return ""


def is_aggregator(url: str) -> bool:
    """
    Check if a URL is from an aggregator domain.

    Aggregator domains (LinkedIn, Crunchbase, Facebook, etc.) host
    multiple companies and should not be used as canonical websites.

    Args:
        url: URL to check

    Returns:
        True if URL is from an aggregator domain, False otherwise

    Examples:
        >>> is_aggregator("https://www.linkedin.com/company/genentech")
        True
        >>> is_aggregator("https://www.gene.com")
        False
        >>> is_aggregator("https://mycompany.wixsite.com/home")
        True
    """
    if not url:
        return False

    domain = etld1(url)
    return domain in AGGREGATOR_ETLD1


# ============================================================================
# Company Name Functions
# ============================================================================

def normalize_name(name: str) -> str:
    """
    Normalize a company name for comparison and deduplication.

    Normalization includes:
    - Convert to lowercase
    - Remove common suffixes (Inc, LLC, Corp, etc.)
    - Remove punctuation (except spaces)
    - Collapse multiple spaces to single space
    - Strip leading/trailing whitespace

    Args:
        name: Company name to normalize

    Returns:
        Normalized company name

    Examples:
        >>> normalize_name("Genentech, Inc.")
        'genentech'
        >>> normalize_name("10x Genomics, LLC")
        '10x genomics'
        >>> normalize_name("Bio-Rad Laboratories")
        'biorad laboratories'
    """
    if not name:
        return ""

    # Lowercase
    normalized = name.lower()

    # Remove punctuation (but keep spaces and alphanumeric) - do this first
    normalized = re.sub(r'[^\w\s]', '', normalized)

    # Collapse multiple spaces to single space
    normalized = re.sub(r'\s+', ' ', normalized)

    # Strip leading/trailing whitespace
    normalized = normalized.strip()

    # Remove common company suffixes
    # Pattern matches suffixes at end of string, with word boundaries
    suffixes = [
        r'\binc$',
        r'\bincorporated$',
        r'\bllc$',
        r'\bltd$',
        r'\blimited$',
        r'\bcorp$',
        r'\bcorporation$',
        r'\bco$',
        r'\bcompany$',
        r'\blaboratories$',
        r'\blabs?$',
        r'\btherapeutics$',
        r'\bbio$',
        r'\bpharma$',
        r'\bpharmaceuticals$',
    ]

    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized)
        # Strip and collapse spaces after each removal
        normalized = normalized.strip()

    return normalized


def name_similarity(a: str, b: str) -> float:
    """
    Calculate similarity score between two company names using Jaro-Winkler.

    Jaro-Winkler is ideal for short strings like company names and gives
    higher scores to strings that match from the beginning (common with
    company names/brands).

    Args:
        a: First company name
        b: Second company name

    Returns:
        Similarity score between 0.0 (no match) and 1.0 (perfect match)

    Examples:
        >>> name_similarity("Genentech", "Genentech Inc")
        # Returns ~0.95 (high similarity)
        >>> name_similarity("Genentech", "10x Genomics")
        # Returns ~0.4 (low similarity)
        >>> name_similarity("BioMarin", "Bio-Marin")
        # Returns ~0.9 (high similarity despite punctuation)
    """
    if not a or not b:
        return 0.0

    # Normalize both names first for better comparison
    norm_a = normalize_name(a)
    norm_b = normalize_name(b)

    # Calculate Jaro-Winkler similarity
    # Returns float between 0.0 and 1.0
    similarity = jaro_winkler.normalized_similarity(norm_a, norm_b)

    return similarity


# ============================================================================
# Multi-Tenant / Incubator Functions
# ============================================================================

def normalize_address(address: str) -> str:
    """
    Normalize an address for comparison.

    Args:
        address: Full address string

    Returns:
        Normalized address (lowercase, collapsed spaces)
    """
    if not address:
        return ""

    # Lowercase and collapse spaces
    normalized = address.lower()
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.strip()

    # Remove common variations (Street vs St, etc.)
    normalized = re.sub(r'\bstreet\b', 'st', normalized)
    normalized = re.sub(r'\bavenue\b', 'ave', normalized)
    normalized = re.sub(r'\bboulevard\b', 'blvd', normalized)
    normalized = re.sub(r'\bdrive\b', 'dr', normalized)

    return normalized


def is_multi_tenant(address: str) -> bool:
    """
    Check if an address is a known multi-tenant/incubator location.

    Multi-tenant addresses house multiple companies and require stronger
    validation to ensure the correct company is matched.

    Args:
        address: Full address string

    Returns:
        True if address is a known multi-tenant location, False otherwise

    Examples:
        >>> is_multi_tenant("201 Gateway Blvd, South San Francisco, CA 94080, USA")
        True
        >>> is_multi_tenant("1 DNA Way, South San Francisco, CA 94080")
        False
    """
    if not address:
        return False

    normalized_input = normalize_address(address)

    # Check against all known incubator addresses
    for incubator_addr in INCUBATOR_ADDRESSES:
        normalized_incubator = normalize_address(incubator_addr)

        # Check if normalized addresses match (or one contains the other)
        # This handles minor variations in formatting
        if (normalized_incubator in normalized_input or
            normalized_input in normalized_incubator):
            return True

    return False


def validate_multi_tenant_match(
    company_name: str,
    details_name: str,
    details_website: Optional[str],
    bpg_website: Optional[str]
) -> bool:
    """
    Validate that a Google Places result matches the company for multi-tenant addresses.

    For incubator/multi-tenant addresses, we need strong evidence that the
    Place Details result is for the correct company, not another tenant.

    Validation criteria:
    1. High name similarity (≥ 0.85) between company_name and details_name, OR
    2. Website eTLD+1 match between details_website and bpg_website

    Args:
        company_name: Company name from BPG or source data
        details_name: Company name from Google Place Details
        details_website: Website from Google Place Details (may be None)
        bpg_website: Website from BPG (ground truth, may be None)

    Returns:
        True if validation passes, False otherwise

    Examples:
        >>> # High name similarity
        >>> validate_multi_tenant_match(
        ...     "Acme Therapeutics",
        ...     "Acme Therapeutics Inc",
        ...     None,
        ...     None
        ... )
        True

        >>> # Website match
        >>> validate_multi_tenant_match(
        ...     "Acme Therapeutics",
        ...     "Different Name",
        ...     "https://acme.com",
        ...     "https://www.acme.com/about"
        ... )
        True

        >>> # Neither criterion met
        >>> validate_multi_tenant_match(
        ...     "Acme Therapeutics",
        ...     "Totally Different Company",
        ...     "https://different.com",
        ...     "https://acme.com"
        ... )
        False
    """
    # Criterion 1: High name similarity
    if company_name and details_name:
        similarity = name_similarity(company_name, details_name)
        if similarity >= 0.85:
            return True

    # Criterion 2: Website eTLD+1 match
    if details_website and bpg_website:
        details_domain = etld1(details_website)
        bpg_domain = etld1(bpg_website)

        # Both must be non-empty and must match
        if details_domain and bpg_domain and details_domain == bpg_domain:
            return True

    # Neither criterion met
    return False


# ============================================================================
# Module Info
# ============================================================================

__all__ = [
    "AGGREGATOR_ETLD1",
    "INCUBATOR_ADDRESSES",
    "etld1",
    "brand_token_from_etld1",
    "is_aggregator",
    "normalize_name",
    "name_similarity",
    "normalize_address",
    "is_multi_tenant",
    "validate_multi_tenant_match",
]
