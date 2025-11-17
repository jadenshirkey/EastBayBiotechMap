#!/usr/bin/env python3
"""
Stage-E: Focus Areas Extraction Script

Extracts factual focus areas from company websites (About/Technology pages).
- 1-3 plain sentences, ≤200 characters
- De-marketed (avoid marketing fluff)
- Include keywords: platform, technology, therapeutic area, modality
- HTML caching (reuse BPG cache directory)
- Rate limiting (1 request/second)
- Timeout handling (5s per request)

Default to empty string if extraction fails.

Usage:
    python scripts/extract_focus_areas.py

Input:  data/working/companies_classified.csv
Output: data/working/companies_focused.csv

Author: Bay Area Biotech Map V4.3
Date: 2025-11-16
"""

import csv
import sys
import logging
import time
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ============================================================================
# Setup Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

INPUT_FILE = Path("data/working/companies_classified.csv")
OUTPUT_FILE = Path("data/working/companies_focused.csv")
CACHE_DIR = Path("data/cache")

# Rate limiting
REQUEST_DELAY = 1.0  # 1 second between requests
REQUEST_TIMEOUT = 5  # 5 second timeout per request

# User agent
USER_AGENT = "BayAreaBiotechMap/4.3 (Research Project; github.com/jadenshirkey/EastBayBiotechMap)"

# Keywords to look for in focus areas
FOCUS_KEYWORDS = {
    # Technology/platform
    "platform", "technology", "AI", "machine learning", "CRISPR", "gene editing",
    "cell therapy", "CAR-T", "antibody", "mRNA", "genomics", "proteomics",
    "bioinformatics", "computational", "screening", "discovery",

    # Therapeutic areas
    "oncology", "cancer", "immunology", "neurology", "cardiovascular",
    "rare disease", "infectious disease", "metabolic", "autoimmune",

    # Modalities
    "small molecule", "biologics", "gene therapy", "cell therapy",
    "RNA", "DNA", "protein", "enzyme", "vaccine",

    # Development stage
    "clinical", "preclinical", "discovery", "development", "pipeline",
}

# Common About page paths
ABOUT_PATHS = [
    "/about",
    "/about-us",
    "/company",
    "/technology",
    "/platform",
    "/science",
    "/our-approach",
    "/what-we-do",
]


# ============================================================================
# HTML Caching
# ============================================================================

def get_cache_path(url: str) -> Path:
    """
    Get cache file path for a URL.

    Args:
        url: URL to cache

    Returns:
        Path to cache file
    """
    # Create a hash of the URL for the filename
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"html_{url_hash}.html"


def load_cached_html(url: str) -> Optional[str]:
    """
    Load HTML from cache if it exists.

    Args:
        url: URL to load

    Returns:
        Cached HTML content, or None if not cached
    """
    cache_path = get_cache_path(url)

    if cache_path.exists():
        logger.debug(f"  Loading from cache: {url}")
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.debug(f"  Cache read failed: {e}")
            return None

    return None


def save_to_cache(url: str, html: str) -> None:
    """
    Save HTML to cache.

    Args:
        url: URL being cached
        html: HTML content to cache
    """
    cache_path = get_cache_path(url)

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(html)
        logger.debug(f"  Saved to cache: {url}")
    except Exception as e:
        logger.debug(f"  Cache write failed: {e}")


# ============================================================================
# HTML Fetching
# ============================================================================

def fetch_html(url: str, use_cache: bool = True) -> Optional[str]:
    """
    Fetch HTML from URL with caching and rate limiting.

    Args:
        url: URL to fetch
        use_cache: Whether to use cached version if available

    Returns:
        HTML content, or None if fetch failed
    """
    # Check cache first
    if use_cache:
        cached = load_cached_html(url)
        if cached:
            return cached

    # Fetch from web
    try:
        logger.debug(f"  Fetching: {url}")

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        }

        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)

        # Check status code
        if response.status_code != 200:
            logger.debug(f"  HTTP {response.status_code}: {url}")
            return None

        html = response.text

        # Save to cache
        save_to_cache(url, html)

        # Rate limiting: sleep after successful fetch
        time.sleep(REQUEST_DELAY)

        return html

    except requests.exceptions.Timeout:
        logger.debug(f"  Timeout: {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.debug(f"  Request failed: {e}")
        return None
    except Exception as e:
        logger.debug(f"  Unexpected error: {e}")
        return None


# ============================================================================
# Text Extraction
# ============================================================================

def extract_text_from_html(html: str, max_chars: int = 200) -> str:
    """
    Extract clean text from HTML, focusing on biotech-relevant content.

    Args:
        html: HTML content
        max_chars: Maximum characters to return

    Returns:
        Extracted text (≤ max_chars)
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()

        # Try to find relevant sections first
        # Look for sections with biotech keywords
        relevant_sections = []

        # Check for sections with relevant headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            heading_text = heading.get_text().lower()
            if any(keyword in heading_text for keyword in
                   ['about', 'technology', 'platform', 'science', 'what we do', 'our approach']):
                # Get the next paragraph or two after this heading
                next_elem = heading.find_next(['p', 'div'])
                if next_elem:
                    text = next_elem.get_text(strip=True)
                    if text and len(text) > 50:  # Meaningful content
                        relevant_sections.append(text)

        # If we found relevant sections, use those
        if relevant_sections:
            combined = ' '.join(relevant_sections)
        else:
            # Fall back to all paragraph text
            paragraphs = soup.find_all('p')
            texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
            combined = ' '.join(texts)

        # Clean up the text
        # Remove extra whitespace
        combined = re.sub(r'\s+', ' ', combined)
        combined = combined.strip()

        # Truncate to max_chars, breaking at sentence boundary if possible
        if len(combined) > max_chars:
            # Try to break at sentence
            truncated = combined[:max_chars]
            # Find last period, exclamation, or question mark
            last_sentence_end = max(
                truncated.rfind('.'),
                truncated.rfind('!'),
                truncated.rfind('?')
            )

            if last_sentence_end > 50:  # Don't break too early
                combined = truncated[:last_sentence_end + 1]
            else:
                # Break at word boundary
                combined = truncated.rsplit(' ', 1)[0] + '...'

        return combined

    except Exception as e:
        logger.debug(f"  Text extraction failed: {e}")
        return ""


def extract_focus_areas(website: str) -> str:
    """
    Extract focus areas from a company website.

    Strategy:
    1. Try homepage first
    2. Try common About/Technology pages
    3. Extract text with biotech keywords
    4. Return ≤200 char summary

    Args:
        website: Company website URL

    Returns:
        Focus areas text (≤200 chars), or empty string if extraction failed
    """
    if not website:
        return ""

    # Normalize URL
    if not website.startswith('http'):
        website = 'https://' + website

    # Parse base URL
    parsed = urlparse(website)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # Try homepage first
    homepage_html = fetch_html(website)
    if homepage_html:
        text = extract_text_from_html(homepage_html)
        if text:
            return text

    # Try common About pages
    for path in ABOUT_PATHS:
        about_url = urljoin(base_url, path)
        about_html = fetch_html(about_url)

        if about_html:
            text = extract_text_from_html(about_html)
            if text:
                return text

    # No text extracted
    return ""


# ============================================================================
# Processing
# ============================================================================

def process_focus_extraction(input_path: Path, output_path: Path) -> Dict[str, int]:
    """
    Read classified companies CSV and add Focus_Areas field.

    Args:
        input_path: Path to companies_classified.csv
        output_path: Path to output companies_focused.csv

    Returns:
        Dictionary with extraction statistics
    """
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.info("This script expects companies_classified.csv from Stage D (classification).")
        return {}

    # Statistics
    stats = {
        "total": 0,
        "with_website": 0,
        "extracted": 0,
        "failed": 0,
    }

    # Read input, extract focus, write output
    logger.info(f"Reading from: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        # Prepare output fieldnames (add Focus_Areas if not present)
        fieldnames = list(reader.fieldnames)
        if "Focus_Areas" not in fieldnames:
            fieldnames.append("Focus_Areas")

        with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                stats["total"] += 1

                company_name = row.get("Company Name", "")
                website = row.get("Website", "")
                existing_focus = row.get("Focus_Areas", "") or row.get("Focus Areas", "")
                description = row.get("Description", "")

                # Log progress every 10 companies
                if stats["total"] % 10 == 0:
                    logger.info(f"  Processed {stats['total']} companies...")

                # Priority order for Focus_Areas:
                # 1. Keep existing focus areas if already populated (from BPG or previous run)
                # 2. Try to extract from website if available
                # 3. Use Wikipedia Description as fallback
                # 4. Empty string if nothing available

                focus_text = ""

                # Check if we already have focus areas
                if existing_focus:
                    focus_text = existing_focus
                    logger.debug(f"  Using existing focus areas for: {company_name}")

                # Try website extraction if no existing focus areas
                elif website:
                    stats["with_website"] += 1
                    logger.debug(f"Extracting focus for: {company_name}")

                    focus_text = extract_focus_areas(website)

                    if focus_text:
                        stats["extracted"] += 1
                        logger.debug(f"  ✓ Extracted from website ({len(focus_text)} chars)")
                    else:
                        # Website extraction failed, try Description fallback
                        if description:
                            # Use Description but truncate to 200 chars to match Focus_Areas format
                            if len(description) > 200:
                                # Try to break at sentence boundary
                                truncated = description[:200]
                                last_period = truncated.rfind('.')
                                if last_period > 100:
                                    focus_text = truncated[:last_period + 1]
                                else:
                                    focus_text = truncated.rsplit(' ', 1)[0] + '...'
                            else:
                                focus_text = description

                            logger.debug(f"  ⚠ Using Description as fallback ({len(focus_text)} chars)")
                            stats["extracted"] += 1  # Count as successful extraction
                        else:
                            stats["failed"] += 1
                            logger.debug(f"  ✗ Extraction failed (no fallback)")

                # No website, use Description if available
                elif description:
                    # Use Description as focus areas
                    if len(description) > 200:
                        # Try to break at sentence boundary
                        truncated = description[:200]
                        last_period = truncated.rfind('.')
                        if last_period > 100:
                            focus_text = truncated[:last_period + 1]
                        else:
                            focus_text = truncated.rsplit(' ', 1)[0] + '...'
                    else:
                        focus_text = description

                    logger.debug(f"  Using Description for {company_name} (no website)")
                    stats["extracted"] += 1

                # Set Focus_Areas field
                row["Focus_Areas"] = focus_text

                # Write to output
                writer.writerow(row)

    logger.info(f"Output written to: {output_path}")

    return stats


def print_statistics(stats: Dict[str, int]) -> None:
    """Print extraction statistics."""
    if not stats:
        return

    total = stats["total"]
    with_website = stats["with_website"]
    extracted = stats["extracted"]
    failed = stats["failed"]

    logger.info("=" * 60)
    logger.info("FOCUS AREAS EXTRACTION STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total companies: {total}")
    logger.info(f"Companies with website: {with_website}")
    logger.info(f"Successfully extracted: {extracted}")
    logger.info(f"Extraction failed: {failed}")
    logger.info("")

    if with_website > 0:
        success_rate = (extracted / with_website * 100)
        logger.info(f"Success rate: {success_rate:.1f}%")

    logger.info("=" * 60)


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    """Main entry point."""
    logger.info("Starting Focus Areas Extraction (Stage E)")
    logger.info("V4.3 Framework - Issue #21")
    logger.info("")

    try:
        # Create output directory if it doesn't exist
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Process extraction
        stats = process_focus_extraction(INPUT_FILE, OUTPUT_FILE)

        if not stats:
            logger.error("Extraction failed - no statistics generated")
            return 1

        # Print statistics
        print_statistics(stats)

        logger.info("")
        logger.info("✓ Focus areas extraction complete!")
        logger.info(f"✓ Output: {OUTPUT_FILE}")

        return 0

    except Exception as e:
        logger.error(f"Extraction failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
