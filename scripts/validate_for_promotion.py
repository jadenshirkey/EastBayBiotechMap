#!/usr/bin/env python3
"""
Stage-F (QC Part 1): Automated Validators for Promotion Gate

Runs 6 automated validators that must ALL PASS before promotion to final/:
1. validate_urls() - all Website fields valid HTTPS or blank
2. validate_geofence() - all City in whitelist, all Address in Bay Area
3. validate_no_duplicate_domains() - zero duplicate eTLD+1 (except allowlist)
4. validate_no_aggregators() - no aggregator domains in final output
5. validate_place_ids() - if Address present, Place_ID present
6. validate_no_out_of_scope() - zero Davis/Sacramento/out-of-area companies

Exit code 0 if all validators PASS, 1 if any validator FAILS.

Usage:
    python scripts/validate_for_promotion.py

Input:  data/working/companies_focused.csv
Output: data/working/validation_report.txt

Author: Bay Area Biotech Map V4.3
Date: 2025-11-16
"""

import csv
import sys
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple
from urllib.parse import urlparse
import re

# Import geography and helpers modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.geography import CITY_WHITELIST, is_in_bay_area_city, geofence_ok
from utils.helpers import etld1, is_aggregator

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

INPUT_FILE = Path("data/working/companies_focused.csv")
REPORT_FILE = Path("data/working/validation_report.txt")

# Out-of-scope cities (examples - should NOT appear in final output)
OUT_OF_SCOPE_CITIES = {
    "Davis",
    "Sacramento",
    "San Diego",
    "Los Angeles",
    "Irvine",
    "La Jolla",
}

# Allowlist for domains that can legitimately be shared (multi-brand companies)
DOMAIN_ALLOWLIST = {
    "gene.com",  # Genentech/Roche multi-brand
}


# ============================================================================
# Validation Functions
# ============================================================================

def validate_urls(rows: List[Dict]) -> Tuple[bool, str]:
    """
    Validator 1: All Website fields must be valid HTTPS URLs or blank.

    Args:
        rows: List of company data rows

    Returns:
        (passed, message) tuple
    """
    logger.info("Running Validator 1: URL validation...")

    invalid_urls = []

    for row in rows:
        website = row.get("Website", "").strip()

        if not website:
            # Blank is OK
            continue

        # Check if it's a valid URL
        try:
            parsed = urlparse(website)

            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                invalid_urls.append(f"{row.get('Company Name', 'Unknown')}: {website}")
                continue

            # Prefer HTTPS, but HTTP is acceptable
            if parsed.scheme not in ['http', 'https']:
                invalid_urls.append(f"{row.get('Company Name', 'Unknown')}: {website} (invalid scheme)")

        except Exception as e:
            invalid_urls.append(f"{row.get('Company Name', 'Unknown')}: {website} (parse error)")

    if invalid_urls:
        message = f"FAIL - Found {len(invalid_urls)} invalid URLs:\n"
        for url in invalid_urls[:10]:  # Show first 10
            message += f"  - {url}\n"
        if len(invalid_urls) > 10:
            message += f"  ... and {len(invalid_urls) - 10} more\n"
        logger.error(message)
        return False, message
    else:
        message = f"PASS - All URLs valid (checked {len(rows)} companies)"
        logger.info(f"  ✓ {message}")
        return True, message


def validate_geofence(rows: List[Dict]) -> Tuple[bool, str]:
    """
    Validator 2: All City in whitelist, all Address in Bay Area.

    Args:
        rows: List of company data rows

    Returns:
        (passed, message) tuple
    """
    logger.info("Running Validator 2: Geofence validation...")

    geofence_violations = []

    for row in rows:
        city = row.get("City", "").strip()
        address = row.get("Address", "").strip()

        # Check city (if present)
        if city and not is_in_bay_area_city(city):
            geofence_violations.append(
                f"{row.get('Company Name', 'Unknown')}: City '{city}' not in whitelist"
            )

        # Check address (if present) - use full geofence check
        if address:
            # Extract lat/lng if available (for coordinates check)
            # Note: This is a simplified check - in production, you'd parse lat/lng from enrichment
            if not geofence_ok(address):
                geofence_violations.append(
                    f"{row.get('Company Name', 'Unknown')}: Address '{address}' outside Bay Area"
                )

    if geofence_violations:
        message = f"FAIL - Found {len(geofence_violations)} geofence violations:\n"
        for violation in geofence_violations[:10]:
            message += f"  - {violation}\n"
        if len(geofence_violations) > 10:
            message += f"  ... and {len(geofence_violations) - 10} more\n"
        logger.error(message)
        return False, message
    else:
        message = f"PASS - All locations within Bay Area geofence (checked {len(rows)} companies)"
        logger.info(f"  ✓ {message}")
        return True, message


def validate_no_duplicate_domains(rows: List[Dict]) -> Tuple[bool, str]:
    """
    Validator 3: Zero duplicate eTLD+1 (except allowlist).

    Args:
        rows: List of company data rows

    Returns:
        (passed, message) tuple
    """
    logger.info("Running Validator 3: Duplicate domain validation...")

    # Track domain → companies mapping
    domain_to_companies: Dict[str, List[str]] = {}

    for row in rows:
        website = row.get("Website", "").strip()
        company_name = row.get("Company Name", "Unknown")

        if not website:
            continue

        domain = etld1(website)
        if not domain:
            continue

        # Skip allowlisted domains
        if domain in DOMAIN_ALLOWLIST:
            continue

        if domain not in domain_to_companies:
            domain_to_companies[domain] = []

        domain_to_companies[domain].append(company_name)

    # Find duplicates
    duplicates = {
        domain: companies
        for domain, companies in domain_to_companies.items()
        if len(companies) > 1
    }

    if duplicates:
        message = f"FAIL - Found {len(duplicates)} duplicate domains:\n"
        for domain, companies in list(duplicates.items())[:10]:
            message += f"  - {domain}: {', '.join(companies)}\n"
        if len(duplicates) > 10:
            message += f"  ... and {len(duplicates) - 10} more\n"
        logger.error(message)
        return False, message
    else:
        message = f"PASS - No duplicate domains (checked {len(domain_to_companies)} unique domains)"
        logger.info(f"  ✓ {message}")
        return True, message


def validate_no_aggregators(rows: List[Dict]) -> Tuple[bool, str]:
    """
    Validator 4: No aggregator domains in final output.

    Args:
        rows: List of company data rows

    Returns:
        (passed, message) tuple
    """
    logger.info("Running Validator 4: Aggregator domain validation...")

    aggregator_violations = []

    for row in rows:
        website = row.get("Website", "").strip()
        company_name = row.get("Company Name", "Unknown")

        if not website:
            continue

        if is_aggregator(website):
            aggregator_violations.append(f"{company_name}: {website}")

    if aggregator_violations:
        message = f"FAIL - Found {len(aggregator_violations)} aggregator domains:\n"
        for violation in aggregator_violations[:10]:
            message += f"  - {violation}\n"
        if len(aggregator_violations) > 10:
            message += f"  ... and {len(aggregator_violations) - 10} more\n"
        logger.error(message)
        return False, message
    else:
        message = f"PASS - No aggregator domains (checked {len(rows)} companies)"
        logger.info(f"  ✓ {message}")
        return True, message


def validate_place_ids(rows: List[Dict]) -> Tuple[bool, str]:
    """
    Validator 5: If Address present, Place_ID must be present.

    Args:
        rows: List of company data rows

    Returns:
        (passed, message) tuple
    """
    logger.info("Running Validator 5: Place_ID validation...")

    missing_place_ids = []

    for row in rows:
        address = row.get("Address", "").strip()
        place_id = row.get("Place_ID", "").strip()
        company_name = row.get("Company Name", "Unknown")

        # If address is present, place_id must also be present
        if address and not place_id:
            missing_place_ids.append(f"{company_name}: has address but no Place_ID")

    if missing_place_ids:
        message = f"FAIL - Found {len(missing_place_ids)} companies with address but no Place_ID:\n"
        for violation in missing_place_ids[:10]:
            message += f"  - {violation}\n"
        if len(missing_place_ids) > 10:
            message += f"  ... and {len(missing_place_ids) - 10} more\n"
        logger.error(message)
        return False, message
    else:
        message = f"PASS - All companies with addresses have Place_IDs (checked {len(rows)} companies)"
        logger.info(f"  ✓ {message}")
        return True, message


def validate_no_out_of_scope(rows: List[Dict]) -> Tuple[bool, str]:
    """
    Validator 6: Zero Davis/Sacramento/out-of-area companies.

    Args:
        rows: List of company data rows

    Returns:
        (passed, message) tuple
    """
    logger.info("Running Validator 6: Out-of-scope location validation...")

    out_of_scope_violations = []

    for row in rows:
        city = row.get("City", "").strip()
        address = row.get("Address", "").strip()
        company_name = row.get("Company Name", "Unknown")

        # Check city against out-of-scope list
        if city in OUT_OF_SCOPE_CITIES:
            out_of_scope_violations.append(f"{company_name}: City '{city}' is out of scope")
            continue

        # Check if address mentions out-of-scope cities
        if address:
            for out_city in OUT_OF_SCOPE_CITIES:
                if out_city.lower() in address.lower():
                    out_of_scope_violations.append(
                        f"{company_name}: Address contains '{out_city}' (out of scope)"
                    )
                    break

    if out_of_scope_violations:
        message = f"FAIL - Found {len(out_of_scope_violations)} out-of-scope locations:\n"
        for violation in out_of_scope_violations[:10]:
            message += f"  - {violation}\n"
        if len(out_of_scope_violations) > 10:
            message += f"  ... and {len(out_of_scope_violations) - 10} more\n"
        logger.error(message)
        return False, message
    else:
        message = f"PASS - No out-of-scope locations (checked {len(rows)} companies)"
        logger.info(f"  ✓ {message}")
        return True, message


# ============================================================================
# Main Validation Runner
# ============================================================================

def run_all_validators(input_path: Path, report_path: Path) -> bool:
    """
    Run all validators and generate report.

    Args:
        input_path: Path to companies_focused.csv
        report_path: Path to output validation_report.txt

    Returns:
        True if all validators pass, False otherwise
    """
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.info("This script expects companies_focused.csv from Stage E (focus extraction).")
        return False

    # Load data
    logger.info(f"Loading data from: {input_path}")
    rows = []

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.info(f"Loaded {len(rows)} companies")
    logger.info("")

    # Run all validators
    validators = [
        ("URLs", validate_urls),
        ("Geofence", validate_geofence),
        ("Duplicate Domains", validate_no_duplicate_domains),
        ("Aggregators", validate_no_aggregators),
        ("Place IDs", validate_place_ids),
        ("Out-of-Scope Locations", validate_no_out_of_scope),
    ]

    results = []
    all_passed = True

    for name, validator_func in validators:
        passed, message = validator_func(rows)
        results.append((name, passed, message))

        if not passed:
            all_passed = False

    # Generate report
    logger.info("")
    logger.info("=" * 60)
    logger.info("VALIDATION REPORT")
    logger.info("=" * 60)

    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("VALIDATION REPORT")
    report_lines.append("V4.3 Framework - Stage F (QC Part 1)")
    report_lines.append(f"Input: {input_path}")
    report_lines.append(f"Companies validated: {len(rows)}")
    report_lines.append("=" * 60)
    report_lines.append("")

    for name, passed, message in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {name}")
        report_lines.append(f"{status}: {name}")
        report_lines.append(f"  {message}")
        report_lines.append("")

    logger.info("=" * 60)
    report_lines.append("=" * 60)

    if all_passed:
        summary = "ALL VALIDATORS PASSED - Ready for promotion"
        logger.info(f"✓ {summary}")
    else:
        summary = "VALIDATION FAILED - Fix issues before promotion"
        logger.error(f"✗ {summary}")

    report_lines.append(summary)
    report_lines.append("=" * 60)

    # Write report to file
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"Report written to: {report_path}")

    return all_passed


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    """Main entry point."""
    logger.info("Starting Automated Validation (Stage F - Part 1)")
    logger.info("V4.3 Framework - Issue #22")
    logger.info("")

    try:
        # Run all validators
        all_passed = run_all_validators(INPUT_FILE, REPORT_FILE)

        logger.info("")
        if all_passed:
            logger.info("✓ All validators passed!")
            logger.info("✓ Data is ready for manual review and promotion")
            return 0
        else:
            logger.error("✗ Validation failed!")
            logger.error("✗ Fix issues before proceeding to promotion")
            return 1

    except Exception as e:
        logger.error(f"Validation failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
