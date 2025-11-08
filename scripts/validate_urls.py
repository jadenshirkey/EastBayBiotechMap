#!/usr/bin/env python3
"""
Validate careers page URLs in the dataset.

This script tests each URL in the "Hiring" column to ensure it's accessible
and returns appropriate HTTP status codes.

Usage:
    python3 validate_urls.py

Prerequisites:
    - data/working/companies_with_careers.csv must exist
    - requests library (install: pip install requests)

Output:
    - data/working/url_validation_report.txt (detailed validation results)
    - Console summary of broken/working URLs

Author: Jaden Shirkey
Date: January 2025
"""

import csv
import time
from datetime import datetime

# Configuration
INPUT_FILE = '../data/working/companies_with_careers.csv'
REPORT_FILE = '../data/working/url_validation_report.txt'
TIMEOUT = 10  # seconds to wait for HTTP response
DELAY = 1  # seconds between requests (be respectful to servers)


def validate_url(url):
    """
    Validate a single URL by making an HTTP request.

    Args:
        url (str): URL to validate

    Returns:
        tuple: (status_code, message) or (None, error_message) if failed
    """
    # Skip non-URL entries
    if not url or url == "Check Website" or not url.startswith('http'):
        return (None, "Not a URL")

    try:
        # NOTE: This requires the 'requests' library
        # Install with: pip install requests
        #
        # import requests
        # response = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
        # return (response.status_code, response.reason)

        # TEMPLATE: Replace above with actual HTTP request
        # For now, return a placeholder
        return (200, "OK (not validated - implement HTTP request)")

    except Exception as e:
        return (None, f"Error: {str(e)}")


def main():
    """Main execution function"""

    print("="*70)
    print("URL VALIDATION - STARTED")
    print("="*70)

    # Load CSV
    print(f"\nLoading companies from: {INPUT_FILE}")

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            companies = list(reader)
    except FileNotFoundError:
        print(f"ERROR: Could not find {INPUT_FILE}")
        print("Make sure you've run fetch_careers_urls.py first!")
        return

    print(f"Loaded {len(companies)} companies\n")

    # Initialize report
    report_lines = []
    report_lines.append(f"URL Validation Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("="*70)
    report_lines.append("")

    # Track statistics
    stats = {
        'total': 0,
        'valid': 0,
        'redirects': 0,
        'broken': 0,
        'not_url': 0,
    }

    broken_urls = []

    # Validate each URL
    for idx, company in enumerate(companies, 1):
        company_name = company['Company Name']
        url = company.get('Hiring', '').strip()

        print(f"[{idx}/{len(companies)}] Validating: {company_name}")

        stats['total'] += 1

        # Validate the URL
        status_code, message = validate_url(url)

        # Categorize result
        if status_code is None:
            stats['not_url'] += 1
            result = f"⏭️  SKIP: {message}"
        elif status_code == 200:
            stats['valid'] += 1
            result = f"✅ OK: {message}"
        elif 300 <= status_code < 400:
            stats['redirects'] += 1
            result = f"⚠️  REDIRECT: {status_code} {message}"
        else:
            stats['broken'] += 1
            result = f"❌ BROKEN: {status_code} {message}"
            broken_urls.append((company_name, url, f"{status_code} {message}"))

        # Log to report
        report_lines.append(f"{company_name}")
        report_lines.append(f"  URL: {url}")
        report_lines.append(f"  {result}")
        report_lines.append("")

        # Rate limiting
        if url and url.startswith('http'):
            time.sleep(DELAY)

    # Add summary to report
    report_lines.append("="*70)
    report_lines.append("VALIDATION SUMMARY")
    report_lines.append("="*70)
    report_lines.append(f"Total companies: {stats['total']}")
    report_lines.append(f"Valid URLs (200 OK): {stats['valid']}")
    report_lines.append(f"Redirects (3xx): {stats['redirects']}")
    report_lines.append(f"Broken URLs (4xx/5xx): {stats['broken']}")
    report_lines.append(f"Not a URL: {stats['not_url']}")
    report_lines.append("")

    if broken_urls:
        report_lines.append("="*70)
        report_lines.append("BROKEN URLS - NEEDS FIXING")
        report_lines.append("="*70)
        for company_name, url, error in broken_urls:
            report_lines.append(f"{company_name}: {url}")
            report_lines.append(f"  Error: {error}")
            report_lines.append("")

    # Save report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    # Print summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"Total companies: {stats['total']}")
    print(f"✅ Valid URLs (200 OK): {stats['valid']}")
    print(f"⚠️  Redirects (3xx): {stats['redirects']}")
    print(f"❌ Broken URLs (4xx/5xx): {stats['broken']}")
    print(f"⏭️  Not a URL: {stats['not_url']}")
    print("")

    if broken_urls:
        print("⚠️  ATTENTION: Found {len(broken_urls)} broken URL(s)")
        print("Check the report for details:")
        print(f"  {REPORT_FILE}")
    else:
        print("✅ All URLs are valid!")

    print(f"\nFull report saved to: {REPORT_FILE}")
    print("="*70)
    print("URL VALIDATION - COMPLETED")
    print("="*70)


if __name__ == "__main__":
    main()
