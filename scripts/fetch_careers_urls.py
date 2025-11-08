#!/usr/bin/env python3
"""
Fetch careers page URLs for Bay Area biotech companies.

This script searches for careers pages across common applicant tracking systems
(ATS) and company websites, then updates the "Hiring" column in the CSV.

Usage:
    python3 fetch_careers_urls.py

Prerequisites:
    - data/working/companies_merged.csv must exist
    - WebSearch capability or manual URL research

Output:
    - data/working/companies_with_careers.csv (updated with careers URLs)
    - data/working/careers_search_log.txt (progress log)

Author: Jaden Shirkey
Date: January 2025
"""

import csv
import time
from datetime import datetime

# Configuration
INPUT_FILE = '../data/working/companies_merged.csv'
OUTPUT_FILE = '../data/working/companies_with_careers.csv'
LOG_FILE = '../data/working/careers_search_log.txt'
SAVE_INTERVAL = 25  # Save progress every N companies

# ATS platforms to search
ATS_PLATFORMS = [
    ('Greenhouse', 'site:greenhouse.io'),
    ('Lever', 'site:lever.co'),
    ('Workday', 'site:myworkdayjobs.com'),
    ('SmartRecruiters', 'site:smartrecruiters.com'),
]


def log_message(message):
    """Log messages to both console and log file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')


def search_ats_platforms(company_name):
    """
    Search for company careers pages across ATS platforms.

    NOTE: This is a TEMPLATE function. You'll need to implement WebSearch
    or manual research to populate the actual URLs.

    Args:
        company_name (str): Name of the company to search

    Returns:
        str: Careers URL if found, empty string otherwise
    """
    # TODO: Implement WebSearch or manual search logic here
    #
    # Example with WebSearch tool (if available):
    # for platform_name, site_query in ATS_PLATFORMS:
    #     query = f'{site_query} "{company_name}"'
    #     results = WebSearch(query)
    #     if results:
    #         # Parse results for URL
    #         url = extract_url_from_results(results)
    #         if url:
    #             log_message(f"  Found on {platform_name}: {url}")
    #             return url

    # For now, return empty string (manual research needed)
    return ""


def search_company_careers_page(company_name, company_website):
    """
    Search for company's careers page on their own website.

    NOTE: This is a TEMPLATE function. Implement your search logic here.

    Args:
        company_name (str): Name of the company
        company_website (str): Company's main website URL

    Returns:
        str: Careers URL if found, empty string otherwise
    """
    # TODO: Implement search logic
    #
    # Example approach:
    # 1. Try common patterns: company.com/careers, company.com/jobs
    # 2. Use WebSearch: "[Company Name] careers jobs apply"
    # 3. Parse search results for careers URL

    # Common careers page patterns to try:
    common_paths = ['/careers', '/jobs', '/join-us', '/about/careers', '/careers/']

    # For now, return empty string (manual research needed)
    return ""


def fetch_careers_url_for_company(company_row):
    """
    Attempt to find careers URL for a single company.

    Args:
        company_row (dict): Row from CSV with company data

    Returns:
        str: Careers URL if found, "Check Website" otherwise
    """
    company_name = company_row['Company Name']
    company_website = company_row.get('Website', '')

    log_message(f"Searching for: {company_name}")

    # Skip if careers URL already exists
    existing_url = company_row.get('Hiring', '').strip()
    if existing_url and existing_url != 'Check Website' and existing_url.startswith('http'):
        log_message(f"  Already has URL: {existing_url}")
        return existing_url

    # Step 1: Search ATS platforms
    ats_url = search_ats_platforms(company_name)
    if ats_url:
        return ats_url

    # Step 2: Search company careers page
    careers_url = search_company_careers_page(company_name, company_website)
    if careers_url:
        return careers_url

    # Step 3: Fallback
    log_message(f"  No careers page found - needs manual research")
    return "Check Website"


def main():
    """Main execution function"""

    log_message("="*70)
    log_message("CAREERS URL COLLECTION - STARTED")
    log_message("="*70)

    # Load input CSV
    log_message(f"Loading companies from: {INPUT_FILE}")

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            companies = list(reader)
            fieldnames = reader.fieldnames
    except FileNotFoundError:
        log_message(f"ERROR: Could not find {INPUT_FILE}")
        return

    log_message(f"Loaded {len(companies)} companies")
    log_message("")

    # Track progress
    found_count = 0
    manual_count = 0

    # Process each company
    for idx, company in enumerate(companies, 1):
        log_message(f"\n[{idx}/{len(companies)}] Processing company...")

        # Fetch careers URL
        careers_url = fetch_careers_url_for_company(company)

        # Update the row
        company['Hiring'] = careers_url

        # Track stats
        if careers_url and careers_url != "Check Website":
            found_count += 1
        else:
            manual_count += 1

        # Save progress periodically
        if idx % SAVE_INTERVAL == 0:
            log_message(f"\nSaving progress... ({idx} companies processed)")
            save_csv(OUTPUT_FILE, fieldnames, companies)
            log_message(f"Stats so far: {found_count} URLs found, {manual_count} need manual research")

        # Rate limiting (be respectful to servers)
        time.sleep(2)  # 2 second delay between searches

    # Save final results
    log_message("\n" + "="*70)
    log_message("FINAL SAVE")
    log_message("="*70)
    save_csv(OUTPUT_FILE, fieldnames, companies)

    # Print summary
    log_message("\n" + "="*70)
    log_message("SUMMARY")
    log_message("="*70)
    log_message(f"Total companies processed: {len(companies)}")
    log_message(f"Careers URLs found: {found_count} ({100*found_count/len(companies):.1f}%)")
    log_message(f"Need manual research: {manual_count} ({100*manual_count/len(companies):.1f}%)")
    log_message(f"\nOutput saved to: {OUTPUT_FILE}")
    log_message(f"Log saved to: {LOG_FILE}")
    log_message("\n" + "="*70)
    log_message("CAREERS URL COLLECTION - COMPLETED")
    log_message("="*70)


def save_csv(filename, fieldnames, rows):
    """Save rows to CSV file"""
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    # Initialize log file
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Careers URL Collection Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")

    # Run main process
    main()

    print(f"\n✓ Script complete! Check {LOG_FILE} for details.")
