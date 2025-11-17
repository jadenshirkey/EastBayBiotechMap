#!/usr/bin/env python3
"""
URL Standardization Utility
Ensures consistent URL formatting across all data sources

Standard format:
- Always include protocol (https:// preferred, http:// if that's what's provided)
- Never include www. prefix (remove if present)
- Remove trailing slashes
- Handle edge cases gracefully
"""

import re
from typing import Optional
from urllib.parse import urlparse, urlunparse


def standardize_url(url: Optional[str]) -> Optional[str]:
    """
    Standardize a URL to consistent format:
    - Ensure protocol (prefer https)
    - Remove www. prefix
    - Remove trailing slash
    - Clean up common issues

    Args:
        url: The URL to standardize (can be None or malformed)

    Returns:
        Standardized URL or None if input is invalid
    """
    if not url:
        return None

    # Clean up the URL
    url = url.strip()

    # Skip if it's not a real URL (e.g., "N/A", "None", etc.)
    if url.lower() in ['n/a', 'none', 'na', '-', '']:
        return None

    # Convert to lowercase for protocol checking
    url_lower = url.lower()

    # Add protocol if missing
    if not url_lower.startswith(('http://', 'https://')):
        # Default to https://
        url = 'https://' + url
    else:
        # Ensure protocol is lowercase
        if url.startswith('HTTP://'):
            url = 'http://' + url[7:]
        elif url.startswith('HTTPS://'):
            url = 'https://' + url[8:]

    try:
        # Parse the URL
        parsed = urlparse(url)

        # Get the hostname without www.
        hostname = parsed.hostname or parsed.netloc
        if hostname and hostname.startswith('www.'):
            hostname = hostname[4:]

        # Rebuild the URL without www. and without trailing slash
        path = parsed.path.rstrip('/') if parsed.path and parsed.path != '/' else ''

        # Reconstruct URL
        standardized = urlunparse((
            parsed.scheme,
            hostname,
            path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))

        # Final cleanup - remove trailing slash if it's just the domain
        if standardized.endswith('/'):
            standardized = standardized[:-1]

        return standardized

    except Exception as e:
        # If URL parsing fails, try basic string manipulation
        try:
            # Remove www. if present
            if '//www.' in url:
                url = url.replace('//www.', '//')

            # Remove trailing slash
            if url.endswith('/'):
                url = url[:-1]

            return url
        except:
            # If all else fails, return None
            return None


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid and reachable format

    Args:
        url: URL to validate

    Returns:
        True if URL appears valid
    """
    if not url:
        return False

    # Must have protocol and domain
    url_pattern = re.compile(
        r'^https?://'  # protocol
        r'[a-zA-Z0-9]'  # first char of domain
        r'[a-zA-Z0-9.-]*'  # rest of domain
        r'\.[a-zA-Z]{2,}'  # TLD
        r'.*$'  # optional path
    )

    return bool(url_pattern.match(url))


def batch_standardize_urls(urls: list) -> list:
    """
    Standardize a batch of URLs

    Args:
        urls: List of URLs to standardize

    Returns:
        List of standardized URLs
    """
    return [standardize_url(url) for url in urls]


# Test the standardization
if __name__ == "__main__":
    test_urls = [
        "https://www.example.com/",
        "http://www.example.com",
        "www.example.com",
        "example.com",
        "https://example.com/path/",
        "http://www.example.com/path/to/page",
        "HTTPS://WWW.EXAMPLE.COM",
        None,
        "N/A",
        "",
        "https://example.com",  # Already correct
    ]

    print("URL Standardization Tests:")
    print("-" * 50)

    for url in test_urls:
        standardized = standardize_url(url)
        print(f"Input:  {url}")
        print(f"Output: {standardized}")
        if standardized:
            print(f"Valid:  {is_valid_url(standardized)}")
        print()